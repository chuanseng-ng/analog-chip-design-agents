#!/usr/bin/env python3
"""qor_trends.py — trend analog/RF QoR metrics across design runs.

Reads the per-domain ``memory/<domain>/experiences.jsonl`` records written by the
orchestrators and trends their ``key_metrics`` over time for a named design, with
regression alerts (e.g. phase margin dropping, NF rising, yield-sigma falling).

The record shape is the one every orchestrator upserts (see, e.g.,
``plugins/meta/agents/pipeline-orchestrator.md`` §Memory):

    {"run_id": "...", "timestamp": "<ISO-8601>", "domain": "post-layout",
     "design_name": "my_ldo", "pdk": "sky130", "tool_used": "ngspice",
     "key_metrics": {"worst_pm_deg": 58.2, ...}, "signoff_achieved": true, ...}

Pure standard library — no third-party dependencies.

Examples
--------
    python3 tools/qor_trends.py --design my_ldo
    python3 tools/qor_trends.py --design my_lna --metric nf_db --metric gain_db
    python3 tools/qor_trends.py --design my_ldo --group-by pdk --format csv
    python3 tools/qor_trends.py --list-designs
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

# Direction of "better" for known metrics. Metrics not listed are still trended,
# but no regression alert is raised for them (direction unknown).
HIGHER_IS_BETTER = {
    "dc_gain_db", "gbw_hz", "phase_margin_deg", "worst_pm_deg", "psrr_db", "cmrr_db",
    "gain_db", "iip3_dbm", "p1db_dbm", "pae_pct", "k_factor", "mc_yield_sigma",
    "em_margin", "em_margin_pct", "q_factor", "srf_ghz", "functional_coverage_pct",
    "rnm_coverage_pct", "sim_speedup_x", "lib_arcs", "corners_covered",
}
LOWER_IS_BETTER = {
    "input_noise", "input_noise_nv_rthz", "power_mw", "nf_db", "area_um2",
    "ir_drop_pct", "offset_mv", "offset_mv_max", "phase_noise_dbc_hz", "evm_pct",
    "spec_degradation_pct", "fit_error_pct", "char_error_pct", "model_error_pct",
    "thd_db", "s11_db", "top_lvs_errors", "lvs_errors", "drc_violations",
    "antenna_violations", "esd_violations", "connect_rule_errors",
    "rnm_mismatch_count", "regression_failures", "failing_corners", "coupling_caps",
}

# Headline metrics surfaced first (PLAN.md §10), when present in the data.
HEADLINE = [
    "dc_gain_db", "phase_margin_deg", "worst_pm_deg", "input_noise", "power_mw",
    "nf_db", "gain_db", "iip3_dbm", "mc_yield_sigma", "area_um2", "em_margin",
    "ir_drop_pct", "top_lvs_errors", "ams_sim_pass", "connect_rule_errors",
]


def direction(metric):
    if metric in HIGHER_IS_BETTER:
        return "higher"
    if metric in LOWER_IS_BETTER:
        return "lower"
    return None


def load_records(memory_dir, domain=None):
    """Yield (path, record) for every JSON line in memory/<domain>/experiences.jsonl."""
    pattern = os.path.join(memory_dir, domain or "*", "experiences.jsonl")
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path) as fh:
                for lineno, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield path, json.loads(line)
                    except json.JSONDecodeError as exc:
                        print(f"WARN: {path}:{lineno}: skipping malformed JSON ({exc})",
                              file=sys.stderr)
        except OSError as exc:
            print(f"WARN: cannot read {path}: {exc}", file=sys.stderr)


def as_number(value):
    """Coerce metric values to float where sensible (bool/int/float/numeric str)."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def collect_points(memory_dir, design, domain, metrics_filter):
    """Return points: list of dicts {timestamp, domain, pdk, tool, run_id, metric, value}."""
    points = []
    for _path, rec in load_records(memory_dir, domain):
        if design is not None and rec.get("design_name") != design:
            continue
        km = rec.get("key_metrics") or {}
        if not isinstance(km, dict):
            continue
        for metric, raw in km.items():
            if metrics_filter and metric not in metrics_filter:
                continue
            value = as_number(raw)
            if value is None:
                continue
            points.append({
                "timestamp": rec.get("timestamp") or "",
                "domain": rec.get("domain") or "?",
                "pdk": rec.get("pdk") or "?",
                "tool": rec.get("tool_used") or "?",
                "run_id": rec.get("run_id") or "?",
                "metric": metric,
                "value": value,
            })
    points.sort(key=lambda p: (p["metric"], p["timestamp"], p["run_id"]))
    return points


def metric_sort_key(metric):
    return (HEADLINE.index(metric) if metric in HEADLINE else len(HEADLINE), metric)


def summarize(points, group_by, threshold_pct):
    """Group points and compute first/last/delta + regression alerts.

    Returns (rows, alerts) where each row is a dict and alerts is a list of strings.
    """
    groups = defaultdict(list)
    for p in points:
        key = p[group_by] if group_by != "none" else "all"
        groups[(p["metric"], key)].append(p)

    rows, alerts = [], []
    for (metric, key) in sorted(groups, key=lambda mk: (metric_sort_key(mk[0]), mk[1])):
        series = groups[(metric, key)]  # already time-sorted from collect_points
        first, last = series[0]["value"], series[-1]["value"]
        delta = last - first
        pct = (delta / abs(first) * 100.0) if first else (0.0 if delta == 0 else float("inf"))
        dirn = direction(metric)
        regressed = False
        if dirn == "higher":
            regressed = delta < 0 and abs(pct) >= threshold_pct
        elif dirn == "lower":
            regressed = delta > 0 and abs(pct) >= threshold_pct
        rows.append({
            "metric": metric, "group": key, "n": len(series),
            "first": first, "last": last, "delta": delta, "pct": pct,
            "direction": dirn or "-", "regressed": regressed,
        })
        if regressed:
            arrow = "fell" if dirn == "higher" else "rose"
            alerts.append(
                f"REGRESSION  {metric} [{group_by}={key}] {arrow} "
                f"{first:.4g} → {last:.4g} ({pct:+.1f}%, {dirn}-is-better) over {len(series)} runs"
            )
    return rows, alerts


def print_table(rows, group_by):
    if not rows:
        print("No matching metrics found.")
        return
    header = ["metric", group_by if group_by != "none" else "group",
              "n", "first", "last", "delta", "pct", "alert"]
    widths = [max(len(header[0]), max(len(r["metric"]) for r in rows)),
              max(len(header[1]), max(len(str(r["group"])) for r in rows)),
              3, 10, 10, 10, 9, 5]

    def fmt(v, w, num=False):
        s = f"{v:.4g}" if num and isinstance(v, float) else str(v)
        return s.ljust(w)

    print("  ".join(fmt(h, widths[i]) for i, h in enumerate(header)))
    print("  ".join("-" * widths[i] for i in range(len(header))))
    for r in rows:
        cells = [
            fmt(r["metric"], widths[0]), fmt(r["group"], widths[1]),
            fmt(r["n"], widths[2]), fmt(r["first"], widths[3], True),
            fmt(r["last"], widths[4], True), fmt(r["delta"], widths[5], True),
            fmt(f"{r['pct']:+.1f}%", widths[6]),
            fmt("⚠" if r["regressed"] else "", widths[7]),
        ]
        print("  ".join(cells))


def print_csv(rows):
    writer = csv.writer(sys.stdout)
    writer.writerow(["metric", "group", "n", "first", "last", "delta", "pct", "direction", "regressed"])
    for r in rows:
        writer.writerow([r["metric"], r["group"], r["n"], r["first"], r["last"],
                         r["delta"], f"{r['pct']:.2f}", r["direction"], int(r["regressed"])])


def list_designs(memory_dir):
    designs = set()
    for _path, rec in load_records(memory_dir):
        name = rec.get("design_name")
        if name:
            designs.add(name)
    if designs:
        print("Designs found:")
        for d in sorted(designs):
            print(f"  {d}")
    else:
        print(f"No experiences.jsonl records found under {memory_dir}/")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--design", help="Filter to this design_name")
    parser.add_argument("--memory-dir", default="memory",
                        help="Root of the per-domain memory store (default: memory)")
    parser.add_argument("--domain", help="Restrict to a single domain's experiences.jsonl")
    parser.add_argument("--metric", action="append", dest="metrics",
                        help="Restrict to this metric (repeatable)")
    parser.add_argument("--group-by", choices=["pdk", "tool", "domain", "none"],
                        default="none", help="Group trends by this dimension")
    parser.add_argument("--format", choices=["table", "csv"], default="table")
    parser.add_argument("--threshold-pct", type=float, default=5.0,
                        help="Regression alert threshold in %% (default: 5.0)")
    parser.add_argument("--list-designs", action="store_true",
                        help="List design names found and exit")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.memory_dir):
        print(f"ERROR: memory dir not found: {args.memory_dir}", file=sys.stderr)
        return 2

    if args.list_designs:
        list_designs(args.memory_dir)
        return 0

    metrics_filter = set(args.metrics) if args.metrics else None
    points = collect_points(args.memory_dir, args.design, args.domain, metrics_filter)
    rows, alerts = summarize(points, args.group_by, args.threshold_pct)

    if args.format == "csv":
        print_csv(rows)
    else:
        scope = f"design={args.design}" if args.design else "all designs"
        print(f"QoR trends — {scope}"
              + (f", domain={args.domain}" if args.domain else "")
              + (f", group-by={args.group_by}" if args.group_by != "none" else "")
              + f"  ({len(points)} data points)\n")
        print_table(rows, args.group_by)
        print()
        if alerts:
            print(f"{len(alerts)} regression alert(s):")
            for a in alerts:
                print(f"  {a}")
        else:
            print("No regressions detected.")

    # Non-zero exit when regressions exist, so CI/automation can gate on it.
    return 1 if alerts and args.format != "csv" else 0


if __name__ == "__main__":
    sys.exit(main())
