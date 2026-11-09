#!/usr/bin/env python3
"""
zopen community Vulnerability Source Merger

Merges vulnerability findings from multiple sources (OSV and Trivy) into a
unified, deduplicated zopen_vulnerability.json file, applying repository
inclusion and exclusion lists.
"""

import argparse
import json
import os
import ssl
import sys
import tempfile
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

HEADER = """
zopen community Vulnerability Source Merger
Merges OSV and Trivy vulnerability datasets into a consolidated zopen_vulnerability.json.
"""

SEVERITY_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 0
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=HEADER)
    parser.add_argument(
        "--osv",
        dest="osv_file",
        required=True,
        help="Path or URL to OSV vulnerability JSON file"
    )
    parser.add_argument(
        "--trivy",
        dest="trivy_file",
        default=None,
        help="Path or URL to Trivy vulnerability JSON file (optional)"
    )
    parser.add_argument(
        "--releases-json",
        dest="releases_json",
        default=None,
        help="Path or URL to zopen_releases.json (used for version mapping in exclude/include)"
    )
    parser.add_argument(
        "--exclude-file",
        dest="exclude_file",
        default="meta/data/cve_exclude.json",
        help="Path to cve_exclude.json"
    )
    parser.add_argument(
        "--include-file",
        dest="include_file",
        default="meta/data/cve_include.json",
        help="Path to cve_include.json"
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        required=True,
        help="Destination path for merged vulnerability JSON"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()


def load_json_data(source: Optional[str], verbose: bool = False) -> Dict[str, Any]:
    """Loads JSON data from local path or URL; returns empty dict if unavailable."""
    if not source:
        return {}

    if source.startswith("http://") or source.startswith("https://"):
        try:
            if verbose:
                print(f"Fetching JSON from URL: {source}")
            req = urllib.request.Request(
                source,
                headers={"User-Agent": "zopen-vuln-merger"}
            )
            context = ssl.create_default_context()
            with urllib.request.urlopen(req, context=context) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            if verbose:
                print(f"Failed to fetch JSON from {source}: {e}")
            return {}
    else:
        if not os.path.exists(source):
            if verbose:
                print(f"File not found: {source}")
            return {}
        try:
            if verbose:
                print(f"Reading JSON from file: {source}")
            with open(source, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            if verbose:
                print(f"Failed to parse JSON file {source}: {e}")
            return {}


def choose_higher_severity(sev1: Optional[str], sev2: Optional[str]) -> str:
    """Returns the higher severity of the two inputs."""
    s1 = (sev1 or "LOW").strip().upper()
    s2 = (sev2 or "LOW").strip().upper()
    score1 = SEVERITY_ORDER.get(s1, 1)
    score2 = SEVERITY_ORDER.get(s2, 1)
    return s1 if score1 >= score2 else s2


def merge_cve_entries(osv_cve: Dict[str, Any], trivy_cve: Dict[str, Any]) -> Dict[str, Any]:
    """Combines an OSV CVE entry and a Trivy CVE entry for the same ID."""
    higher_sev = choose_higher_severity(osv_cve.get("severity"), trivy_cve.get("severity"))
    details = osv_cve.get("details") or trivy_cve.get("details") or ""
    published = osv_cve.get("published") or trivy_cve.get("published") or ""

    merged = {
        "id": osv_cve.get("id") or trivy_cve.get("id"),
        "details": details,
        "published": published,
        "severity": higher_sev,
        "source": "osv,trivy"
    }

    # Add optional enrichment fields if present in Trivy
    for field in ("package", "installed_version", "fixed_version"):
        if field in trivy_cve and trivy_cve[field]:
            merged[field] = trivy_cve[field]
        elif field in osv_cve and osv_cve[field]:
            merged[field] = osv_cve[field]

    return merged


def merge_vuln_datasets(
    osv_data: Dict[str, Any],
    trivy_data: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Merges two vulnerability datasets keyed by project -> release -> metadata & CVEs."""
    merged_data: Dict[str, Dict[str, Any]] = defaultdict(dict)
    all_projects = set(osv_data.keys()) | set(trivy_data.keys())

    for project in all_projects:
        osv_releases = osv_data.get(project, {})
        trivy_releases = trivy_data.get(project, {})
        all_release_keys = set(osv_releases.keys()) | set(trivy_releases.keys())

        for rel_key in all_release_keys:
            osv_rel = osv_releases.get(rel_key, {})
            trivy_rel = trivy_releases.get(rel_key, {})

            release_name = osv_rel.get("release_name") or trivy_rel.get("release_name", "")
            commit_sha = osv_rel.get("commit_sha") or trivy_rel.get("commit_sha", "")

            osv_cves = {cve["id"]: dict(cve) for cve in osv_rel.get("CVEs", []) if "id" in cve}
            trivy_cves = {cve["id"]: dict(cve) for cve in trivy_rel.get("CVEs", []) if "id" in cve}

            merged_cves_map: Dict[str, Dict[str, Any]] = {}
            all_cve_ids = set(osv_cves.keys()) | set(trivy_cves.keys())

            for cve_id in all_cve_ids:
                if cve_id in osv_cves and cve_id in trivy_cves:
                    merged_cves_map[cve_id] = merge_cve_entries(osv_cves[cve_id], trivy_cves[cve_id])
                elif cve_id in osv_cves:
                    entry = dict(osv_cves[cve_id])
                    if "source" not in entry:
                        entry["source"] = "osv"
                    merged_cves_map[cve_id] = entry
                else:
                    entry = dict(trivy_cves[cve_id])
                    if "source" not in entry:
                        entry["source"] = "trivy"
                    merged_cves_map[cve_id] = entry

            merged_list = list(merged_cves_map.values())
            merged_data[project][rel_key] = {
                "release_name": release_name,
                "commit_sha": commit_sha,
                "CVEs": merged_list
            }

    return merged_data


def apply_exclusions_and_inclusions(
    vuln_data: Dict[str, Dict[str, Any]],
    exclude_json: Dict[str, Any],
    include_json: Dict[str, Any],
    releases_data: Dict[str, Any],
    verbose: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Applies exclude rules and include rules against the merged vulnerability dataset."""
    # Build release timestamp to version map and release name maps
    # exclude_json format: { "pkg": [ { "id": "CVE-...", "versions": ["1.0", "1.1"] } ] }
    filtered_data: Dict[str, Dict[str, Any]] = defaultdict(dict)

    # Build lookup table for package versions per release timestamp and name
    pkg_release_version_map: Dict[str, Dict[str, str]] = defaultdict(dict)
    for pkg, releases in releases_data.items():
        for rel in releases:
            rel_name = rel.get("name", "")
            for asset in rel.get("assets", []):
                rel_ts = asset.get("release", "")
                version = asset.get("version", "")
                if rel_ts:
                    pkg_release_version_map[pkg][rel_ts] = version
                if rel_name:
                    pkg_release_version_map[pkg][rel_name] = version

    # 1. Apply exclusions
    for project, releases in vuln_data.items():
        exclude_rules = exclude_json.get(project, [])
        for rel_ts, rel_info in releases.items():
            rel_name = rel_info.get("release_name", "")
            commit_sha = rel_info.get("commit_sha", "")
            cves = rel_info.get("CVEs", [])

            version = pkg_release_version_map.get(project, {}).get(rel_ts) or pkg_release_version_map.get(project, {}).get(rel_name, "")

            filtered_cves = []
            for cve in cves:
                cve_id = cve.get("id")
                excluded = False
                for rule in exclude_rules:
                    if rule.get("id") == cve_id:
                        rule_versions = set(rule.get("versions", []))
                        # If versions list is specified, check version match; if empty or version matches, exclude
                        if not rule_versions or version in rule_versions:
                            excluded = True
                            if verbose:
                                print(f"Excluded {cve_id} in {project} release {rel_name} ({version})")
                            break
                if not excluded:
                    filtered_cves.append(cve)

            if filtered_cves or rel_info:
                filtered_data[project][rel_ts] = {
                    "release_name": rel_name,
                    "commit_sha": commit_sha,
                    "CVEs": filtered_cves
                }

    # 2. Apply inclusions
    # include_json format: { "pkg": [ { "id": "CVE-...", "details": "...", "severity": "HIGH", "versions": ["1.0"] } ] }
    for project, include_rules in include_json.items():
        for rule in include_rules:
            cve_id = rule.get("id")
            rule_versions = set(rule.get("versions", []))
            details = rule.get("details", "")
            severity = rule.get("severity", "LOW")

            for rel_ts, rel_info in filtered_data.get(project, {}).items():
                rel_name = rel_info.get("release_name", "")
                version = pkg_release_version_map.get(project, {}).get(rel_ts) or pkg_release_version_map.get(project, {}).get(rel_name, "")
                if not rule_versions or version in rule_versions:
                    # Check if already present
                    existing_ids = {c["id"] for c in rel_info["CVEs"]}
                    if cve_id not in existing_ids:
                        if verbose:
                            print(f"Included {cve_id} in {project} release {rel_name} ({version})")
                        rel_info["CVEs"].append({
                            "id": cve_id,
                            "details": details,
                            "severity": severity,
                            "source": "manual_include"
                        })

    # Clean up empty release entries if CVE list is empty
    result: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for project, releases in filtered_data.items():
        for rel_ts, rel_info in releases.items():
            if rel_info.get("CVEs"):
                result[project][rel_ts] = rel_info

    return result


def atomic_write_json(file_path: str, data: Any) -> None:
    """Atomically writes JSON to the destination path."""
    dest_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(dest_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dest_dir, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=4)
        temp_name = tf.name
    os.replace(temp_name, file_path)


def main() -> int:
    args = parse_args()

    osv_data = load_json_data(args.osv_file, verbose=args.verbose)
    trivy_data = load_json_data(args.trivy_file, verbose=args.verbose) if args.trivy_file else {}
    exclude_json = load_json_data(args.exclude_file, verbose=args.verbose)
    include_json = load_json_data(args.include_file, verbose=args.verbose)

    releases_json = load_json_data(args.releases_json, verbose=args.verbose) if args.releases_json else {}
    releases_data = releases_json.get("release_data", {}) if isinstance(releases_json, dict) else {}

    # Merge OSV and Trivy
    merged_data = merge_vuln_datasets(osv_data, trivy_data)

    # Apply inclusions and exclusions
    final_data = apply_exclusions_and_inclusions(
        merged_data,
        exclude_json,
        include_json,
        releases_data,
        verbose=args.verbose
    )

    # Write output
    atomic_write_json(args.output_file, final_data)
    if args.verbose:
        print(f"Successfully generated merged vulnerability JSON: {args.output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
