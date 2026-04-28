#!/usr/bin/env python3
"""Harness state manager — targeted reads/writes to avoid full-file cat.

Usage (run from project root):
  python _workspace/state.py checkpoint get [--field KEY]
  python _workspace/state.py checkpoint update --field KEY --value VALUE
  python _workspace/state.py checkpoint status

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


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


# ── checkpoint ───────────────────────────────────────────────────────────────

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
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    try:
        value = json.loads(args.value)
    except (json.JSONDecodeError, TypeError):
        value = args.value
    data[args.field] = value
    data["last_updated"] = now_ts()
    atomic_write(CHECKPOINT, json.dumps(data, indent=2, ensure_ascii=False))
    print(f"checkpoint.{args.field} = {value}")


def cmd_checkpoint_status(args) -> None:
    if not CHECKPOINT.exists():
        sys.exit("checkpoint.json not found")
    data = json.loads(CHECKPOINT.read_text())
    print(data.get("status", "unknown"))


# ── tasks ─────────────────────────────────────────────────────────────────────

def _parse_tasks() -> tuple[list[str], list[dict]]:
    """Returns (preamble_lines, rows)."""
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
    for f in files:
        try:
            t = json.loads(Path(f).read_text())
        except Exception as e:
            print(f"skip {f}: {e}", file=sys.stderr)
            continue
        tid = t.get("task_id", "")
        if not tid:
            print(f"skip {f}: missing task_id", file=sys.stderr)
            continue
        if tid in row_map:
            row_map[tid]["status"] = t.get("status", row_map[tid]["status"])
            if t.get("evidence"):
                row_map[tid]["evidence"] = t["evidence"]
            if t.get("artifact_path"):
                row_map[tid]["output"] = t["artifact_path"]
        else:
            row_map[tid] = {
                "id":       tid,
                "agent":    t.get("agent", ""),
                "task":     "",
                "status":   t.get("status", "todo"),
                "evidence": t.get("evidence", ""),
                "output":   t.get("artifact_path", ""),
            }
    atomic_write(TASKS_MD, _render_tasks(preamble, list(row_map.values())))
    print(f"collected {len(files)} task files → tasks.md updated")


# ── findings ──────────────────────────────────────────────────────────────────

def _parse_findings(text: str) -> tuple[str, dict[str, str]]:
    """Returns (preamble, {section_name: full_section_text})."""
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

    cg = cp_sub.add_parser("get", help="Print checkpoint (or single field)")
    cg.add_argument("--field", default=None, metavar="KEY")
    cg.set_defaults(func=cmd_checkpoint_get)

    cu = cp_sub.add_parser("update", help="Set a single checkpoint field")
    cu.add_argument("--field", required=True, metavar="KEY")
    cu.add_argument("--value", required=True, metavar="VALUE",
                    help="JSON-parseable value or plain string")
    cu.set_defaults(func=cmd_checkpoint_update)

    cs = cp_sub.add_parser("status", help="Print status field only")
    cs.set_defaults(func=cmd_checkpoint_status)

    # tasks
    tk = res.add_parser("tasks")
    tk_sub = tk.add_subparsers(dest="action", required=True)

    tl = tk_sub.add_parser("list", help="List tasks (optionally filtered by status)")
    tl.add_argument("--status", default=None,
                    choices=["todo", "in-progress", "done", "blocked"])
    tl.set_defaults(func=cmd_tasks_list)

    tu = tk_sub.add_parser("update", help="Update a task row")
    tu.add_argument("--id", required=True)
    tu.add_argument("--status", required=True,
                    choices=["todo", "in-progress", "done", "blocked"])
    tu.add_argument("--evidence", default=None)
    tu.add_argument("--output", default=None, metavar="PATH")
    tu.set_defaults(func=cmd_tasks_update)

    tc = tk_sub.add_parser("collect",
                           help="GLOB task_*.json and merge into tasks.md")
    tc.set_defaults(func=cmd_tasks_collect)

    # findings
    fn = res.add_parser("findings")
    fn_sub = fn.add_subparsers(dest="action", required=True)

    fg = fn_sub.add_parser("get", help="Print findings (or one section)")
    fg.add_argument("--section", default=None, metavar="SECTION")
    fg.set_defaults(func=cmd_findings_get)

    fa = fn_sub.add_parser("append", help="Append a bullet to a section")
    fa.add_argument("--section", required=True, metavar="SECTION")
    fa.add_argument("--text", required=True)
    fa.set_defaults(func=cmd_findings_append)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
