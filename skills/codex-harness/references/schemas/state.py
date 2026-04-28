#!/usr/bin/env python3
"""Harness state manager — targeted reads/writes to avoid full-file cat.

Usage (run from project root):
  python _workspace/state.py checkpoint get [--field KEY]
  python _workspace/state.py checkpoint update --field KEY --value VALUE
  python _workspace/state.py checkpoint status
  python _workspace/state.py checkpoint append-stage --stage NAME [--completed-at TS] [--user-approved]
  python _workspace/state.py checkpoint append-step  --stage NAME --step NAME --iterations N [--completed-at TS]

  python _workspace/state.py tasks list [--status todo|in-progress|done|blocked]
  python _workspace/state.py tasks update --id ID --status STATUS [--evidence TEXT] [--output PATH]
  python _workspace/state.py tasks collect

  python _workspace/state.py findings get [--section SECTION]
  python _workspace/state.py findings append --section SECTION --text TEXT
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent
CHECKPOINT = WORKSPACE / "checkpoint.json"
TASKS_MD = WORKSPACE / "tasks.md"
FINDINGS_MD = WORKSPACE / "findings.md"
TASK_GLOB = str(WORKSPACE / "tasks" / "task_*.json")

_HISTORY_FIELDS = frozenset({"stage_history", "step_history"})

_CHECKPOINT_REQUIRED = frozenset({
    "execution_id", "plan_name", "status", "current_stage", "current_step",
    "active_pattern", "stage_history", "step_history", "stage_artifacts",
    "handoff_chain", "tasks_snapshot", "shared_variables", "last_updated",
})
_CHECKPOINT_STATUS_ENUM = {"in_progress", "partial", "blocked", "completed"}
_CHECKPOINT_PATTERN_ENUM = {
    "pipeline", "fan_out_fan_in", "expert_pool",
    "producer_reviewer", "supervisor", "hierarchical", "handoff",
}
_TS_RE = re.compile(r"^\d{8}_\d{6}$")

_TASK_REQUIRED = frozenset({"id", "agent", "stage", "step", "status", "timestamp"})
_TASK_STATUS_ENUM = {"todo", "in-progress", "done", "blocked"}
_TASK_ID_RE = re.compile(r"^task_[a-zA-Z0-9_-]+_\d+$")
_AGENT_RE = re.compile(r"^@[a-zA-Z0-9_-]+$")


# ── validators ────────────────────────────────────────────────────────────────

def _errors_checkpoint(data: dict) -> list[str]:
    errs: list[str] = []
    missing = _CHECKPOINT_REQUIRED - data.keys()
    if missing:
        errs.append(f"missing required fields: {sorted(missing)}")
    if "status" in data and data["status"] not in _CHECKPOINT_STATUS_ENUM:
        errs.append(f"status '{data['status']}' not in {sorted(_CHECKPOINT_STATUS_ENUM)}")
    if "active_pattern" in data and data["active_pattern"] not in _CHECKPOINT_PATTERN_ENUM:
        errs.append(f"active_pattern '{data['active_pattern']}' not in {sorted(_CHECKPOINT_PATTERN_ENUM)}")
    for ts_field in ("execution_id", "last_updated"):
        if ts_field in data and not _TS_RE.match(str(data[ts_field])):
            errs.append(f"{ts_field} must match YYYYMMDD_HHMMSS, got '{data[ts_field]}'")
    if data.get("status") == "blocked":
        for f in ("blocked_reason", "blocked_agent"):
            if not data.get(f):
                errs.append(f"status=blocked requires '{f}'")
    return errs


def _errors_task(data: dict) -> list[str]:
    errs: list[str] = []
    missing = _TASK_REQUIRED - data.keys()
    if missing:
        errs.append(f"missing required fields: {sorted(missing)}")
    if "status" in data and data["status"] not in _TASK_STATUS_ENUM:
        errs.append(f"status '{data['status']}' not in {sorted(_TASK_STATUS_ENUM)}")
    if "id" in data and not _TASK_ID_RE.match(str(data["id"])):
        errs.append(f"id '{data['id']}' must match task_<name>_<seq>")
    if "agent" in data and not _AGENT_RE.match(str(data["agent"])):
        errs.append(f"agent '{data['agent']}' must start with @")
    if "timestamp" in data and not _TS_RE.match(str(data["timestamp"])):
        errs.append(f"timestamp must match YYYYMMDD_HHMMSS, got '{data['timestamp']}'")
    if data.get("status") == "done":
        for f in ("evidence", "artifact"):
            if not data.get(f):
                errs.append(f"status=done requires '{f}'")
    if data.get("status") == "blocked" and not data.get("blocked_reason"):
        errs.append("status=blocked requires 'blocked_reason'")
    return errs


def _validate_checkpoint(data: dict, label: str = "checkpoint.json") -> None:
    errs = _errors_checkpoint(data)
    if errs:
        sys.exit(f"validation error ({label}):\n" + "\n".join(f"  - {e}" for e in errs))


def _validate_task(data: dict, label: str) -> None:
    errs = _errors_task(data)
    if errs:
        sys.exit(f"validation error ({label}):\n" + "\n".join(f"  - {e}" for e in errs))


# ── utils ─────────────────────────────────────────────────────────────────────

def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


# ── checkpoint ────────────────────────────────────────────────────────────────

def cmd_checkpoint_get(args) -> None:
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    if args.field:
        val = data.get(args.field)
        if val is None:
            sys.exit(f"field '{args.field}' not found")
        print(json.dumps(val) if isinstance(val, (dict, list)) else val)
    else:
        print(CHECKPOINT.read_text(), end="")


def cmd_checkpoint_update(args) -> None:
    if args.field in _HISTORY_FIELDS:
        sys.exit(
            f"'{args.field}' is append-only. "
            "Use 'checkpoint append-stage' or 'checkpoint append-step'."
        )
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    try:
        value = json.loads(args.value)
    except (json.JSONDecodeError, TypeError):
        value = args.value
    data[args.field] = value
    data["last_updated"] = now_ts()
    _validate_checkpoint(data)
    atomic_write(CHECKPOINT, json.dumps(data, indent=2, ensure_ascii=False))
    print(f"checkpoint.{args.field} = {value}")


def cmd_checkpoint_status(args) -> None:
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    print(data.get("status", "unknown"))


def cmd_checkpoint_append_stage(args) -> None:
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    entry: dict = {
        "stage": args.stage,
        "completed_at": args.completed_at or now_ts(),
    }
    if args.user_approved:
        entry["user_approved"] = True
    data.setdefault("stage_history", []).append(entry)
    data["last_updated"] = now_ts()
    _validate_checkpoint(data)
    atomic_write(CHECKPOINT, json.dumps(data, indent=2, ensure_ascii=False))
    print(f"stage_history ← {entry}")


def cmd_checkpoint_append_step(args) -> None:
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    entry: dict = {
        "stage": args.stage,
        "step": args.step,
        "iterations": args.iterations,
        "completed_at": args.completed_at or now_ts(),
    }
    data.setdefault("step_history", []).append(entry)
    data["last_updated"] = now_ts()
    _validate_checkpoint(data)
    atomic_write(CHECKPOINT, json.dumps(data, indent=2, ensure_ascii=False))
    print(f"step_history ← {entry}")


# ── tasks ─────────────────────────────────────────────────────────────────────

def _parse_tasks() -> tuple[list[str], list[dict]]:
    if not TASKS_MD.exists():
        return [], []
    lines = TASKS_MD.read_text(encoding="utf-8").splitlines()
    preamble, rows, in_table = [], [], False
    for line in lines:
        if not in_table and line.startswith("|") and "ID" in line and "Agent" in line:
            in_table = True
            continue
        if not in_table:
            preamble.append(line)
            continue
        if re.match(r"^\|[-| ]+\|$", line.rstrip()):
            continue
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 4:
            rows.append({
                "id":       parts[0],
                "agent":    parts[1],
                "task":     parts[2],
                "status":   parts[3],
                "evidence": parts[4] if len(parts) > 4 else "",
                "output":   parts[5] if len(parts) > 5 else "",
            })
    return preamble, rows


def _render_tasks(preamble: list[str], rows: list[dict]) -> str:
    out = "\n".join(preamble) + ("\n" if preamble else "")
    out += "| ID | Agent | Task | Status | Evidence | Output Path |\n"
    out += "|----|-------|------|--------|----------|-------------|\n"
    for r in rows:
        out += (f"| {r['id']} | {r['agent']} | {r['task']} | {r['status']}"
                f" | {r['evidence'] or '-'} | {r['output']} |\n")
    return out


def cmd_tasks_list(args) -> None:
    _, rows = _parse_tasks()
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    if not rows:
        print("(none)")
        return
    for r in rows:
        line = f"[{r['id']}] {r['agent']} | {r['status']} | {r['task']}"
        if r["evidence"] and r["evidence"] != "-":
            line += f" | {r['evidence']}"
        print(line)


def cmd_tasks_update(args) -> None:
    preamble, rows = _parse_tasks()
    for r in rows:
        if r["id"] == args.id:
            r["status"] = args.status
            if args.evidence:
                r["evidence"] = args.evidence
            if args.output:
                r["output"] = args.output
            atomic_write(TASKS_MD, _render_tasks(preamble, rows))
            print(f"task {args.id} → {args.status}")
            return
    sys.exit(f"task id '{args.id}' not found")


def cmd_tasks_collect(args) -> None:
    files = sorted(glob.glob(TASK_GLOB))
    if not files:
        print("no task_*.json files found")
        return
    preamble, rows = _parse_tasks()
    row_map = {r["id"]: r for r in rows}
    skipped = 0
    for f in files:
        try:
            t = json.loads(Path(f).read_text())
        except Exception as e:
            print(f"skip {f}: {e}", file=sys.stderr)
            skipped += 1
            continue
        tid = t.get("id", "")
        if not tid:
            print(f"skip {f}: missing 'id' field", file=sys.stderr)
            skipped += 1
            continue
        errs = _errors_task(t)
        if errs:
            print(f"skip {f}: " + "; ".join(errs), file=sys.stderr)
            skipped += 1
            continue
        if tid in row_map:
            row_map[tid]["status"] = t.get("status", row_map[tid]["status"])
            if t.get("evidence"):
                row_map[tid]["evidence"] = t["evidence"]
            if t.get("artifact"):
                row_map[tid]["output"] = t["artifact"]
        else:
            row_map[tid] = {
                "id":       tid,
                "agent":    t.get("agent", ""),
                "task":     "",
                "status":   t.get("status", "todo"),
                "evidence": t.get("evidence", ""),
                "output":   t.get("artifact", ""),
            }
    collected = len(files) - skipped
    atomic_write(TASKS_MD, _render_tasks(preamble, list(row_map.values())))
    print(f"collected {collected}/{len(files)} task files → tasks.md updated"
          + (f" ({skipped} skipped)" if skipped else ""))


# ── findings ──────────────────────────────────────────────────────────────────

def _parse_findings(text: str) -> tuple[str, dict[str, str]]:
    sections, preamble_lines, current, buf = {}, [], None, []
    for line in text.splitlines(keepends=True):
        m = re.match(r"^## \[(.+?)\]", line)
        if m:
            if current is not None:
                sections[current] = "".join(buf)
            current, buf = m.group(1), [line]
        elif current is None:
            preamble_lines.append(line)
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "".join(buf)
    return "".join(preamble_lines), sections


def cmd_findings_get(args) -> None:
    if not FINDINGS_MD.exists():
        sys.exit("findings.md not found")
    text = FINDINGS_MD.read_text(encoding="utf-8")
    if args.section:
        _, sections = _parse_findings(text)
        if args.section not in sections:
            sys.exit(f"section '[{args.section}]' not found")
        print(sections[args.section], end="")
    else:
        print(text, end="")


def cmd_findings_append(args) -> None:
    if not FINDINGS_MD.exists():
        sys.exit("findings.md not found")
    text = FINDINGS_MD.read_text(encoding="utf-8")
    preamble, sections = _parse_findings(text)
    if args.section not in sections:
        sections[args.section] = f"## [{args.section}]\n"
    sections[args.section] = sections[args.section].rstrip("\n") + f"\n- {args.text}\n"
    atomic_write(FINDINGS_MD, preamble + "".join(sections.values()))
    print(f"appended to [{args.section}]")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(prog="state.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    res = p.add_subparsers(dest="resource", required=True)

    # checkpoint
    cp = res.add_parser("checkpoint")
    cp_sub = cp.add_subparsers(dest="action", required=True)

    cg = cp_sub.add_parser("get")
    cg.add_argument("--field", default=None, metavar="KEY")
    cg.set_defaults(func=cmd_checkpoint_get)

    cu = cp_sub.add_parser("update", help="Set a single field (history fields blocked)")
    cu.add_argument("--field", required=True, metavar="KEY")
    cu.add_argument("--value", required=True, metavar="VALUE")
    cu.set_defaults(func=cmd_checkpoint_update)

    cs = cp_sub.add_parser("status")
    cs.set_defaults(func=cmd_checkpoint_status)

    cas = cp_sub.add_parser("append-stage")
    cas.add_argument("--stage", required=True)
    cas.add_argument("--completed-at", default=None, metavar="YYYYMMDD_HHMMSS")
    cas.add_argument("--user-approved", action="store_true")
    cas.set_defaults(func=cmd_checkpoint_append_stage)

    cass = cp_sub.add_parser("append-step")
    cass.add_argument("--stage", required=True)
    cass.add_argument("--step", required=True)
    cass.add_argument("--iterations", required=True, type=int)
    cass.add_argument("--completed-at", default=None, metavar="YYYYMMDD_HHMMSS")
    cass.set_defaults(func=cmd_checkpoint_append_step)

    # tasks
    tk = res.add_parser("tasks")
    tk_sub = tk.add_subparsers(dest="action", required=True)

    tl = tk_sub.add_parser("list")
    tl.add_argument("--status", default=None,
                    choices=["todo", "in-progress", "done", "blocked"])
    tl.set_defaults(func=cmd_tasks_list)

    tu = tk_sub.add_parser("update")
    tu.add_argument("--id", required=True)
    tu.add_argument("--status", required=True,
                    choices=["todo", "in-progress", "done", "blocked"])
    tu.add_argument("--evidence", default=None)
    tu.add_argument("--output", default=None, metavar="PATH")
    tu.set_defaults(func=cmd_tasks_update)

    tc = tk_sub.add_parser("collect")
    tc.set_defaults(func=cmd_tasks_collect)

    # findings
    fn = res.add_parser("findings")
    fn_sub = fn.add_subparsers(dest="action", required=True)

    fg = fn_sub.add_parser("get")
    fg.add_argument("--section", default=None, metavar="SECTION")
    fg.set_defaults(func=cmd_findings_get)

    fa = fn_sub.add_parser("append")
    fa.add_argument("--section", required=True, metavar="SECTION")
    fa.add_argument("--text", required=True)
    fa.set_defaults(func=cmd_findings_append)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
