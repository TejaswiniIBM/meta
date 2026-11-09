#!/usr/bin/env python3
"""
zopen community Trivy Vulnerability JSON Generator

This tool scans zopen community package releases using Aqua Security Trivy,
normalizes findings into the zopen vulnerability schema, and generates a
cached JSON vulnerability report.
"""

import argparse
import concurrent.futures
import json
import logging
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

HEADER = """
zopen community Trivy Vulnerability JSON Generator
Fetches zopen community releases and generates a list of packages and associated CVEs using Trivy.
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
        "--releases-json",
        dest="releases_json",
        default="https://github.com/zopencommunity/meta/releases/download/api-cache/zopen_releases.json",
        help="Path or URL to zopen_releases.json"
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        required=True,
        help="The full path to store the output JSON file to"
    )
    parser.add_argument(
        "--cache-file",
        dest="cache_file",
        default=None,
        help="Path to scan cache file to avoid re-scanning unchanged commits"
    )
    parser.add_argument(
        "--jobs",
        dest="jobs",
        type=int,
        default=4,
        help="Number of concurrent scanning jobs (default: 4)"
    )
    parser.add_argument(
        "--severity",
        dest="severity",
        default="UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL",
        help="Severities to scan for (comma-separated, default: UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)"
    )
    parser.add_argument(
        "--trivy",
        dest="trivy_bin",
        default="trivy",
        help="Path to trivy executable (default: trivy)"
    )
    parser.add_argument(
        "--ignorefile",
        dest="ignorefile",
        default=None,
        help="Path to .trivyignore file"
    )
    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        default=300,
        help="Scan timeout in seconds per release (default: 300)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()


def load_json_source(source: str, verbose: bool = False) -> Dict[str, Any]:
    """Loads JSON from either a local file or an HTTP/HTTPS URL."""
    if source.startswith("http://") or source.startswith("https://"):
        if verbose:
            print(f"Fetching releases JSON from URL: {source}")
        req = urllib.request.Request(
            source,
            headers={"User-Agent": "zopen-trivy-scanner"}
        )
        context = ssl.create_default_context()
        with urllib.request.urlopen(req, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    else:
        if verbose:
            print(f"Reading releases JSON from local file: {source}")
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)


def map_severity(raw_severity: Optional[str]) -> str:
    """Normalizes raw Trivy severity string into standard zopen severity buckets."""
    if not raw_severity:
        return "LOW"
    sev = raw_severity.strip().upper()
    if sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return sev
    if sev in ("UNKNOWN", "NONE", "UNASSIGNED"):
        return "LOW"
    return "LOW"


def get_trivy_db_version(trivy_bin: str) -> str:
    """Retrieves Trivy version/db metadata for cache invalidation."""
    try:
        proc = subprocess.run(
            [trivy_bin, "version", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            ver = data.get("Version", "unknown")
            db_meta = data.get("VulnerabilityDB", {}).get("UpdatedAt", "")
            return f"{ver}_{db_meta}"
    except Exception:
        pass
    return "default_version"


def scan_release_trivy(
    trivy_bin: str,
    project: str,
    release_name: str,
    commit_sha: str,
    release_timestamp: str,
    severity: str,
    ignorefile: Optional[str],
    timeout: int,
    verbose: bool
) -> Tuple[str, str, str, str, Optional[List[Dict[str, Any]]]]:
    """
    Scans a given release commit using Trivy.
    Returns: (project, release_name, release_timestamp, commit_sha, list_of_cves_or_none)
    """
    repo_url = f"https://github.com/zopencommunity/{project}"
    cmd = [
        trivy_bin,
        "repo",
        repo_url,
        "--commit",
        commit_sha,
        "--format",
        "json",
        "--quiet",
        "--severity",
        severity,
        "--scanners",
        "vuln",
        "--timeout",
        f"{timeout}s"
    ]

    if ignorefile and os.path.exists(ignorefile):
        cmd.extend(["--ignorefile", ignorefile])

    if verbose:
        print(f"Scanning {project} @ {commit_sha} ({release_name})...")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False
        )
        if not proc.stdout.strip():
            if verbose:
                print(f"Empty stdout for {project} @ {commit_sha}; stderr: {proc.stderr}")
            return (project, release_name, release_timestamp, commit_sha, None)

        scan_result = json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        print(f"Timeout scanning {project} @ {commit_sha} after {timeout}s", file=sys.stderr)
        return (project, release_name, release_timestamp, commit_sha, None)
    except json.JSONDecodeError as jde:
        print(f"Failed to parse Trivy JSON output for {project} @ {commit_sha}: {jde}", file=sys.stderr)
        return (project, release_name, release_timestamp, commit_sha, None)
    except Exception as e:
        print(f"Error scanning {project} @ {commit_sha}: {e}", file=sys.stderr)
        return (project, release_name, release_timestamp, commit_sha, None)

    results = scan_result.get("Results", [])
    extracted_cves: List[Dict[str, Any]] = []

    for result in results:
        vulns = result.get("Vulnerabilities", [])
        if not vulns:
            continue
        for vuln in vulns:
            vuln_id = vuln.get("VulnerabilityID")
            if not vuln_id:
                continue

            details = vuln.get("Title") or vuln.get("Description") or ""
            # Clean up newlines in details
            details = " ".join(details.split())
            if len(details) > 300:
                details = details[:297] + "..."

            sev = map_severity(vuln.get("Severity"))
            cve_entry = {
                "id": vuln_id,
                "details": details,
                "published": vuln.get("PublishedDate", ""),
                "severity": sev,
                "package": vuln.get("PkgName", ""),
                "installed_version": vuln.get("InstalledVersion", ""),
                "fixed_version": vuln.get("FixedVersion", ""),
                "source": "trivy"
            }
            extracted_cves.append(cve_entry)

    # De-duplicate CVEs by ID within the same release
    deduped_cves: Dict[str, Dict[str, Any]] = {}
    for cve in extracted_cves:
        cve_id = cve["id"]
        if cve_id not in deduped_cves:
            deduped_cves[cve_id] = cve
        else:
            # Keep higher severity if duplicate within Trivy results
            existing_sev = SEVERITY_ORDER.get(deduped_cves[cve_id]["severity"], 0)
            new_sev = SEVERITY_ORDER.get(cve["severity"], 0)
            if new_sev > existing_sev:
                deduped_cves[cve_id] = cve

    return (project, release_name, release_timestamp, commit_sha, list(deduped_cves.values()))


def atomic_write_json(file_path: str, data: Any) -> None:
    """Atomically writes JSON to the specified destination path."""
    dest_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(dest_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dest_dir, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=4)
        temp_name = tf.name
    os.replace(temp_name, file_path)


def main() -> int:
    args = parse_args()

    # Verify trivy binary if executable scanning is needed
    trivy_path = shutil.which(args.trivy_bin)
    if not trivy_path:
        print(f"Warning: Trivy binary '{args.trivy_bin}' not found in PATH.", file=sys.stderr)

    try:
        releases_json = load_json_source(args.releases_json, verbose=args.verbose)
    except Exception as e:
        print(f"Error loading releases JSON from {args.releases_json}: {e}", file=sys.stderr)
        return 1

    releases_data = releases_json.get("release_data", {})
    if not releases_data:
        print("No release_data found in releases JSON.", file=sys.stderr)
        atomic_write_json(args.output_file, {})
        return 0

    cache: Dict[str, Any] = {}
    if args.cache_file and os.path.exists(args.cache_file):
        try:
            with open(args.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if args.verbose:
                print(f"Loaded {len(cache)} cached scan entries.")
        except Exception as e:
            if args.verbose:
                print(f"Could not load cache file: {e}")
            cache = {}

    db_version = get_trivy_db_version(args.trivy_bin) if trivy_path else "unavailable"

    scan_tasks = []
    project_info: Dict[str, Dict[str, Any]] = defaultdict(dict)
    new_cache: Dict[str, Any] = dict(cache)

    for project, releases in releases_data.items():
        for release in releases:
            assets = release.get("assets", [])
            if not assets:
                continue
            asset = assets[0]
            # Prioritize upstream commitsha if present, otherwise community_commitsha
            commit_sha = asset.get("commitsha") or asset.get("community_commitsha")
            release_timestamp = asset.get("release")
            release_name = release.get("name", "")

            if not commit_sha or not release_timestamp:
                continue

            cache_key = f"{project}:{commit_sha}:{db_version}"
            if cache_key in cache:
                cached_cves = cache[cache_key]
                if cached_cves:
                    project_info[project][release_timestamp] = {
                        "release_name": release_name,
                        "commit_sha": commit_sha,
                        "CVEs": cached_cves
                    }
                continue

            if trivy_path:
                scan_tasks.append((
                    args.trivy_bin,
                    project,
                    release_name,
                    commit_sha,
                    release_timestamp,
                    args.severity,
                    args.ignorefile,
                    args.timeout,
                    args.verbose
                ))

    if scan_tasks:
        if args.verbose:
            print(f"Starting {len(scan_tasks)} scan tasks across {args.jobs} worker threads...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
            futures = [executor.submit(scan_release_trivy, *task) for task in scan_tasks]
            for future in concurrent.futures.as_completed(futures):
                try:
                    project, release_name, release_timestamp, commit_sha, cves = future.result()
                    cache_key = f"{project}:{commit_sha}:{db_version}"
                    if cves is not None:
                        new_cache[cache_key] = cves
                        if cves:
                            project_info[project][release_timestamp] = {
                                "release_name": release_name,
                                "commit_sha": commit_sha,
                                "CVEs": cves
                            }
                except Exception as e:
                    print(f"Scan task failed with error: {e}", file=sys.stderr)

    # Save output atomically
    atomic_write_json(args.output_file, project_info)
    if args.verbose:
        print(f"Successfully wrote Trivy vulnerability output to: {args.output_file}")

    # Save updated cache atomically
    if args.cache_file:
        atomic_write_json(args.cache_file, new_cache)
        if args.verbose:
            print(f"Successfully saved cache to: {args.cache_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
