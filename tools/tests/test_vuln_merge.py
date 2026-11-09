#!/usr/bin/env python3
"""
Unit and regression test suite for Trivy integration and vulnerability merger.
Works with both pytest and standard python unittest.
"""

import json
import os
import sys
import tempfile
import unittest

# Add meta/tools to sys.path for direct imports
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from create_trivy_json import map_severity, SEVERITY_ORDER
from merge_vuln_sources import (
    choose_higher_severity,
    merge_cve_entries,
    merge_vuln_datasets,
    apply_exclusions_and_inclusions,
    atomic_write_json
)


class TestTrivyVulnIntegration(unittest.TestCase):

    def test_map_severity(self):
        self.assertEqual(map_severity("CRITICAL"), "CRITICAL")
        self.assertEqual(map_severity("critical"), "CRITICAL")
        self.assertEqual(map_severity("HIGH"), "HIGH")
        self.assertEqual(map_severity("MEDIUM"), "MEDIUM")
        self.assertEqual(map_severity("LOW"), "LOW")
        self.assertEqual(map_severity("UNKNOWN"), "LOW")
        self.assertEqual(map_severity("NONE"), "LOW")
        self.assertEqual(map_severity(None), "LOW")
        self.assertEqual(map_severity(""), "LOW")

    def test_choose_higher_severity(self):
        self.assertEqual(choose_higher_severity("LOW", "HIGH"), "HIGH")
        self.assertEqual(choose_higher_severity("CRITICAL", "MEDIUM"), "CRITICAL")
        self.assertEqual(choose_higher_severity("MEDIUM", "LOW"), "MEDIUM")
        self.assertEqual(choose_higher_severity("HIGH", "HIGH"), "HIGH")
        self.assertEqual(choose_higher_severity("UNKNOWN", "LOW"), "LOW")
        self.assertEqual(choose_higher_severity(None, "CRITICAL"), "CRITICAL")

    def test_merge_cve_entries(self):
        osv_cve = {
            "id": "CVE-2023-1001",
            "details": "OSV Description of buffer overflow",
            "published": "2023-01-01T00:00:00Z",
            "severity": "MEDIUM",
            "source": "osv"
        }
        trivy_cve = {
            "id": "CVE-2023-1001",
            "details": "Trivy short title",
            "published": "2023-01-01T00:00:00Z",
            "severity": "HIGH",
            "package": "curl",
            "installed_version": "7.88.0",
            "fixed_version": "7.88.1",
            "source": "trivy"
        }

        merged = merge_cve_entries(osv_cve, trivy_cve)
        self.assertEqual(merged["id"], "CVE-2023-1001")
        self.assertEqual(merged["severity"], "HIGH")
        self.assertEqual(merged["details"], "OSV Description of buffer overflow")
        self.assertEqual(merged["fixed_version"], "7.88.1")
        self.assertEqual(merged["package"], "curl")
        self.assertEqual(merged["source"], "osv,trivy")

    def test_merge_vuln_datasets(self):
        osv_data = {
            "curl": {
                "20230101000000": {
                    "release_name": "curl-7.88.0",
                    "commit_sha": "abc1234",
                    "CVEs": [
                        {
                            "id": "CVE-2023-0001",
                            "details": "OSV-only finding",
                            "severity": "LOW"
                        },
                        {
                            "id": "CVE-2023-0002",
                            "details": "Overlapping finding",
                            "severity": "LOW"
                        }
                    ]
                }
            }
        }

        trivy_data = {
            "curl": {
                "20230101000000": {
                    "release_name": "curl-7.88.0",
                    "commit_sha": "abc1234",
                    "CVEs": [
                        {
                            "id": "CVE-2023-0002",
                            "details": "Trivy detail",
                            "severity": "CRITICAL",
                            "fixed_version": "7.88.1"
                        },
                        {
                            "id": "CVE-2023-0003",
                            "details": "Trivy-only finding",
                            "severity": "HIGH",
                            "fixed_version": "7.88.2"
                        }
                    ]
                }
            }
        }

        merged = merge_vuln_datasets(osv_data, trivy_data)
        self.assertIn("curl", merged)
        self.assertIn("20230101000000", merged["curl"])

        cves = {c["id"]: c for c in merged["curl"]["20230101000000"]["CVEs"]}
        self.assertEqual(len(cves), 3)

        # OSV-only
        self.assertEqual(cves["CVE-2023-0001"]["source"], "osv")
        self.assertEqual(cves["CVE-2023-0001"]["severity"], "LOW")

        # Overlapping (Trivy escalated to CRITICAL)
        self.assertEqual(cves["CVE-2023-0002"]["source"], "osv,trivy")
        self.assertEqual(cves["CVE-2023-0002"]["severity"], "CRITICAL")
        self.assertEqual(cves["CVE-2023-0002"]["fixed_version"], "7.88.1")

        # Trivy-only
        self.assertEqual(cves["CVE-2023-0003"]["source"], "trivy")
        self.assertEqual(cves["CVE-2023-0003"]["severity"], "HIGH")
        self.assertEqual(cves["CVE-2023-0003"]["fixed_version"], "7.88.2")

    def test_exclusions_and_inclusions(self):
        vuln_data = {
            "openssl": {
                "20230501000000": {
                    "release_name": "openssl-3.0.8",
                    "commit_sha": "def5678",
                    "CVEs": [
                        {"id": "CVE-2023-9999", "details": "False positive", "severity": "HIGH"},
                        {"id": "CVE-2023-1111", "details": "Real bug", "severity": "MEDIUM"}
                    ]
                }
            }
        }

        exclude_json = {
            "openssl": [
                {"id": "CVE-2023-9999", "versions": ["3.0.8"]}
            ]
        }

        include_json = {
            "openssl": [
                {
                    "id": "CVE-2023-7777",
                    "details": "Manual backport advisory",
                    "severity": "CRITICAL",
                    "versions": ["3.0.8"]
                }
            ]
        }

        releases_data = {
            "openssl": [
                {
                    "name": "openssl-3.0.8",
                    "assets": [
                        {
                            "release": "20230501000000",
                            "version": "3.0.8"
                        }
                    ]
                }
            ]
        }

        filtered = apply_exclusions_and_inclusions(
            vuln_data,
            exclude_json,
            include_json,
            releases_data
        )

        cve_ids = [c["id"] for c in filtered["openssl"]["20230501000000"]["CVEs"]]
        self.assertNotIn("CVE-2023-9999", cve_ids)  # Excluded
        self.assertIn("CVE-2023-1111", cve_ids)      # Kept
        self.assertIn("CVE-2023-7777", cve_ids)      # Included

    def test_fail_soft_behavior(self):
        osv_data = {
            "bash": {
                "20230101000000": {
                    "release_name": "bash-5.2",
                    "commit_sha": "11223344",
                    "CVEs": [
                        {"id": "CVE-2022-3715", "details": "Heap overflow", "severity": "HIGH"}
                    ]
                }
            }
        }
        # When trivy data is empty
        merged = merge_vuln_datasets(osv_data, {})
        self.assertEqual(len(merged["bash"]["20230101000000"]["CVEs"]), 1)
        self.assertEqual(merged["bash"]["20230101000000"]["CVEs"][0]["id"], "CVE-2022-3715")

    def test_atomic_write_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "subdir", "test.json")
            sample_data = {"key": "value", "count": 42}

            atomic_write_json(target_path, sample_data)
            self.assertTrue(os.path.exists(target_path))

            with open(target_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded, sample_data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
