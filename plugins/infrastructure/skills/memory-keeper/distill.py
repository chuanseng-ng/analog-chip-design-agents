#!/usr/bin/env python3
"""
distill.py — Memory-Keeper helper: parse experiences.jsonl and emit a structured
distillation summary for an analog-chip-design domain.

Usage:
    python3 distill.py <domain> [--min-records N] [--memory-root PATH]

Outputs a JSON object to stdout that the memory-keeper skill uses to decide what new
entries to add to knowledge.md. Exits with code 2 when the record count is below the
threshold (skip).

Exit codes:
    0  — summary emitted; enough records
    1  — unexpected error
    2  — skipped; fewer than --min-records records
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

# Memory domain folder names — the 14 design domains + infrastructure + meta.
VALID_DOMAINS = [
    "architecture",
    "modeling",
    "circuit",
    "sim",
    "ams-verification",
    "layout",
    "physical-verification",
    "extraction",
    "post-layout",
    "reliability",
    "characterization",
    "rf",
    "em",
    "ams-integration",
    "infrastructure",
    "meta",
]

# Numeric key_metrics fields per domain (used for range computation).
METRIC_FIELDS = {
    "architecture": ["noise_budget_nv", "power_budget_mw", "area_estimate_um2"],
    "modeling": ["model_error_pct", "sim_speedup_x", "rnm_coverage_pct"],
    "circuit": ["dc_gain_db", "phase_margin_deg", "gbw_hz", "power_mw", "erc_errors"],
    "sim": ["worst_pm_deg", "worst_gain_db", "mc_yield_sigma", "failing_corners", "convergence_failures"],
    "ams-verification": ["functional_coverage_pct", "rnm_mismatch_count", "regression_failures"],
    "layout": ["matching_sigma_pct", "density_pct", "area_um2"],
    "physical-verification": ["drc_violations", "lvs_errors", "antenna_violations"],
    "extraction": ["r_count", "c_count", "coupling_caps"],
    "post-layout": ["worst_pm_deg", "spec_degradation_pct", "failing_corners"],
    "reliability": ["em_margin_pct", "ir_drop_pct", "esd_violations"],
    "characterization": ["lib_arcs", "char_error_pct", "corners_covered"],
    "rf": ["nf_db", "gain_db", "iip3_dbm", "phase_noise_dbc_hz"],
    "em": ["q_factor", "srf_ghz", "fit_error_pct"],
    "ams-integration": ["top_lvs_errors", "ams_sim_pass", "connect_rule_errors"],
    "infrastructure": ["tools_detected", "tools_missing", "wrappers_deployed", "mcp_servers_configured"],
    "meta": ["cross_domain_iterations", "fix_requests_processed", "fix_requests_abandoned"],
}


def load_records(jsonl_path: Path) -> list:
    records = []
    malformed = 0
    if not jsonl_path.exists():
        return records
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                malformed += 1
                print(f"  [warn] malformed JSON on line {lineno}, skipping", file=sys.stderr)
                continue
            if not isinstance(obj, dict):
                malformed += 1
                print(f"  [warn] line {lineno} is valid JSON but not an object, skipping", file=sys.stderr)
                continue
            records.append(obj)
    if malformed:
        print(f"  [warn] {malformed} malformed line(s) ignored", file=sys.stderr)
    return records


def compute_metric_ranges(records: list, domain: str) -> dict:
    fields = METRIC_FIELDS.get(domain, [])
    ranges = {}
    for field in fields:
        values = []
        for rec in records:
            km = rec.get("key_metrics", {}) or {}
            v = km.get(field)
            if isinstance(v, (int, float)):
                values.append(v)
        if not values:
            continue
        ranges[field] = {
            "min": min(values),
            "max": max(values),
            "median": statistics.median(values),
            "latest": values[-1],
            "count": len(values),
        }
    return ranges


def extract_issue_fix_pairs(records: list) -> list:
    pair_counter = Counter()
    for rec in records:
        issues = rec.get("issues_encountered") or []
        fixes = rec.get("fixes_applied") or []
        if issues and fixes and len(issues) == len(fixes):
            for iss, fix in zip(issues, fixes):
                pair_counter[(iss.strip(), fix.strip())] += 1
        else:
            for iss in issues:
                pair_counter[(iss.strip(), None)] += 1
            for fix in fixes:
                pair_counter[(None, fix.strip())] += 1
    return [{"issue": i, "fix": f, "count": c} for (i, f), c in pair_counter.most_common()]


def extract_tool_flag_candidates(records: list) -> list:
    import re
    flag_pattern = re.compile(r"(`[^`]+`|(?:(?:^|\s))(--?\w[\w\-]*))", re.MULTILINE)
    seen = set()
    candidates = []
    for rec in records:
        sources = list(rec.get("fixes_applied") or []) + [rec.get("notes") or ""]
        for text in sources:
            for match in flag_pattern.finditer(text):
                token = match.group(0).strip("`").strip()
                if token and token not in seen:
                    seen.add(token)
                    candidates.append(token)
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Distil experiences.jsonl for an analog-design domain")
    parser.add_argument("domain", choices=VALID_DOMAINS, help="Domain name")
    parser.add_argument("--min-records", type=int, default=5, metavar="N",
                        help="Minimum record count required (default: 5)")
    parser.add_argument("--memory-root", default=None, metavar="PATH",
                        help="Path to the memory/ directory (default: auto-detect)")
    args = parser.parse_args()

    if args.memory_root:
        memory_root = Path(args.memory_root)
    else:
        # plugins/infrastructure/skills/memory-keeper/ → repo root is parents[4]
        memory_root = Path(__file__).resolve().parents[4] / "memory"

    jsonl_path = memory_root / args.domain / "experiences.jsonl"
    records = load_records(jsonl_path)
    n = len(records)

    if n < args.min_records:
        print(json.dumps({
            "skipped": True,
            "domain": args.domain,
            "record_count": n,
            "min_records": args.min_records,
            "reason": f"Only {n} record(s); threshold is {args.min_records}",
        }), flush=True)
        sys.exit(2)

    timestamps = sorted(r["timestamp"] for r in records if isinstance(r.get("timestamp"), str))
    signoff_count = sum(1 for r in records if r.get("signoff_achieved") is True)

    summary = {
        "skipped": False,
        "domain": args.domain,
        "record_count": n,
        "date_range": [timestamps[0] if timestamps else None, timestamps[-1] if timestamps else None],
        "signoff_rate": round(signoff_count / n, 3) if n else 0.0,
        "issue_fix_pairs": extract_issue_fix_pairs(records),
        "tool_flag_candidates": extract_tool_flag_candidates(records),
        "metric_ranges": compute_metric_ranges(records, args.domain),
        "free_notes": [r["notes"] for r in records if r.get("notes") and isinstance(r["notes"], str)],
    }
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
