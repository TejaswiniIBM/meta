# Implementing Trivy for `zopen audit`: To-Do & Task List

This document outlines the step-by-step tasks required to integrate [Aqua Security Trivy](https://github.com/aquasecurity/trivy) vulnerability scanning into `zopen audit` for the zopen community.

---

## Overview of Architecture

1. **Server-Side Enrichment (Track B - Primary)**:
   - Run Trivy during nightly CI/CD jobs against package release commits / lockfiles.
   - Merge Trivy findings with OSV database findings into the consolidated `zopen_vulnerability.json`.
   - Update `bin/zopen-audit` to parse and display extended vulnerability attributes (e.g., fixed versions, severity levels, source attribution) without breaking backward compatibility.

2. **Client-Side Scanning (Track C - Optional/On-Demand)**:
   - Add flags (`--trivy`, `--trivy-only`, `--trivy-severity`, `--trivy-offline`) to `bin/zopen-audit` for live local scanning on z/OS where Trivy is available.
   - Merge live scan results with cached JSON results and report unified findings.

---

## Task Checklist

### Phase 0: Prerequisites & Setup
- [ ] **P0.1 Pin Trivy Version & Tooling**
  - [ ] Determine stable Trivy version and configure `TRIVY_VERSION` in CI variables.
  - [ ] Verify sha256 checksums during automated downloads.
  - [ ] Add Python dependencies to `tools/requirements-vuln.txt` (`aiohttp`, `certifi`, `cvsslib`).
- [ ] **P0.2 Feasibility & Schema Verification**
  - [ ] Benchmark Trivy scan runtime and memory across sample C, Python, Node, Go, and Rust ports.
  - [ ] Confirm backward-compatible JSON schema extension for `zopen_vulnerability.json`.
  - [ ] Establish shellcheck and unit test baseline for `bin/zopen-audit` and Python tools.

---

### Track B: Server-Side Trivy Enrichment for `zopen audit`
- [ ] **B1 Create `tools/create_trivy_json.py`**
  - [ ] Accept arguments: `--releases-json`, `--output-file`, `--cache-file`, `--jobs`, `--severity`, `--trivy`.
  - [ ] Execute `trivy` scans using safe `subprocess.run(shell=False)` with timeouts.
  - [ ] Normalize Trivy schema:
    - [ ] Map `UNKNOWN` severity to `LOW` (or preserve explicit unknown).
    - [ ] Extract `VulnerabilityID`, `PkgName`, `InstalledVersion`, `FixedVersion`, `Title`/`Description`.
  - [ ] Implement caching mechanism keyed on `(package, commit, db_version)`.
  - [ ] Write output atomically via temporary files and `os.replace`.
- [ ] **B2 Create `tools/merge_vuln_sources.py`**
  - [ ] Merge OSV and Trivy findings by primary key `(package, release, vuln_id)`.
  - [ ] Retain OSV details when both sources report the same vulnerability; pick highest severity.
  - [ ] Apply `cve_exclude.json` and `cve_include.json` filters after merging.
  - [ ] Gracefully fallback to OSV-only dataset if Trivy scan fails or returns empty data.
- [ ] **B3 Test Suite for Vulnerability Generation (`tools/tests`)**
  - [ ] Unit tests for Trivy parser and schema normalizer.
  - [ ] Unit tests for multi-source de-duplication and severity resolution.
  - [ ] Exclude / include list filtering tests.
  - [ ] Regression test ensuring OSV-only inputs produce byte-identical output to legacy generator.
- [ ] **B4 Update Vulnerability Documentation Tool**
  - [ ] Update `tools/create_vulnerability_doc.py` to display fixed versions and vulnerability sources.
- [ ] **B5 Update Client Script: `bin/zopen-audit`**
  - [ ] Update `jq` query at line 168 to extract `fixed_version` and format details while preserving tab-separated columns (`[.severity, .id, .details]`).
  - [ ] Add default fallback arm in severity `case` evaluation (line 219) for unknown severities.
  - [ ] Maintain existing package lookup, `--upgrade`, and `--remove` logic.
  - [ ] Verify that existing OSV-only output format remains identical.
- [ ] **B6 CI/CD Workflow Integration**
  - [ ] Add GitHub Actions workflow `.github/workflows/vulnerability_scan.yml` (or update nightly workflow).
  - [ ] Set up caching for the Trivy database (`trivy-db`).
  - [ ] Ensure Trivy errors fail soft without blocking deployment of OSV data.
- [ ] **B7 Validation & End-to-End Testing**
  - [ ] Run dry-run scan against `api-cache-test` tag.
  - [ ] Verify `bin/zopen-audit` correctly parses enriched JSON data.
  - [ ] Verify `cve_exclude.json` suppressions are respected across `zopen audit`, `Vulnerabilities.md`, and feeds.

---

### Track C: Optional Client-Side `zopen audit --trivy` (Local Scanning)
- [ ] **C1 CLI Options & Input Validation**
  - [ ] Add `--trivy`, `--trivy-only`, `--trivy-severity`, and `--trivy-offline` flags to `bin/zopen-audit`.
  - [ ] Validate `--trivy-severity` input (allow only `A-Z`, commas).
  - [ ] Validate availability of `trivy` executable before proceeding with local scan.
- [ ] **C2 Local Package Scanning Logic**
  - [ ] Implement `trivyScanPackage()` using per-process temporary files (`${TMPDIR:-/tmp}/zopen-audit-trivy.$$.${pkg}.json`).
  - [ ] Tag intermediate JSON files appropriately on z/OS (`chtag -tc 819`).
  - [ ] Combine local scan findings with cached database findings using `sort -u`.
  - [ ] Handle `--upgrade` comparisons for local-only findings appropriately.
  - [ ] Clean up temporary files on exit / traps.

---

### Documentation & Rollout
- [ ] **D1 Documentation Updates**
  - [ ] Update `printHelp()` in `bin/zopen-audit`.
  - [ ] Update `meta/docs/Guides/ThePackageManager.md` with audit details and examples.
  - [ ] Update man page `man/man1/zopen-audit.1` and reference documentation.
  - [ ] Update `meta/CHANGELOG.md`.
- [ ] **D2 Final Review & Sign-off**
  - [ ] Verify shellcheck clean status on `bin/zopen-audit`.
  - [ ] Review false-positive rate and tune default filters.
