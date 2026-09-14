"""A real SQLite-to-CSV fixture; JSON CLI, not an MCP server or agent runner.

python3 experiments/sqlite_export.py --setup /tmp/aam-trial
echo '{"action":"status"}' | python3 experiments/sqlite_export.py /tmp/aam-trial
"""
import csv
import hashlib
import io
import json
import re
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ADAPTER_VERSION = "1.0"


def versions():
    return {"application": "SQLite", "application_version": sqlite3.sqlite_version,
            "adapter_version": ADAPTER_VERSION}


def reply(ok, code, message, next_steps, **extra):
    return {"ok": ok, "code": code, "message": message,
            "runtime": versions(), "next_steps": next_steps, **extra}


def setup(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    with closing(sqlite3.connect(root / "source.sqlite")) as db:
        db.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, quantity INTEGER)")
        db.executemany("INSERT INTO products VALUES (?, ?, ?)",
                       [(1, "Bolt", 12), (2, "Nut", 18), (3, "Washer", 24)])
        db.commit()
    manifest = {"format": "aam-experiment-discovery-only",
                "application": versions(), "instructions_action": "instructions",
                "status_action": "status", "interface": "JSON CLI: sqlite_export.py"}
    (root / "discovery.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return root


def call(root, request):
    root = Path(root).resolve()
    if not isinstance(request, dict):
        return reply(False, "INVALID_REQUEST", "Expected a JSON object.", [{"action": "instructions"}])
    action = request.get("action")
    if action == "instructions":
        return reply(True, "INSTRUCTIONS", "Export all products into a new UTF-8 CSV.", [],
                     actions={"status": "Read runtime versions and source availability; no account is required.",
                              "instructions": "Get these current instructions.",
                              "export": {"output": "New basename ending in .csv, e.g. products.csv",
                                         "expected_application_version": sqlite3.sqlite_version,
                                         "expected_adapter_version": ADAPTER_VERSION}},
                     guidance="Call status, then export using its observed versions. Read export evidence. "
                              "For OUTPUT_EXISTS choose a fresh filename; never overwrite.")
    if action == "status":
        return reply(True, "STATUS", "Runtime status observed.", [{"action": "instructions"}],
                     source_present=(root / "source.sqlite").is_file(), account_required=False)
    if action != "export":
        return reply(False, "UNKNOWN_ACTION", "Use status, instructions or export.", [{"action": "instructions"}])
    if (request.get("expected_application_version") != sqlite3.sqlite_version or
            request.get("expected_adapter_version") != ADAPTER_VERSION):
        return reply(False, "VERSION_MISMATCH", "Requested versions do not match this runtime; no export was attempted.",
                     [{"action": "status"}, {"action": "instructions"},
                      {"action": "export", "hint": "Retry with the versions observed in status after reviewing current instructions."}])
    name = request.get("output")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.csv", name):
        return reply(False, "INVALID_OUTPUT", "Output must be a CSV basename inside the trial directory.",
                     [{"action": "export", "output": "products.csv", "hint": "Keep the observed version fields."}])
    source = root / "source.sqlite"
    if not source.is_file() or source.is_symlink():
        return reply(False, "SOURCE_UNAVAILABLE", "Fixture source is missing or is a symlink.",
                     [{"action": "host", "hint": "Restore the trial fixture source, then retry; do not invent replacement rows."}])
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as db:
            db.execute("BEGIN")
            integrity = [row[0] for row in db.execute("PRAGMA quick_check")]
            if integrity != ["ok"]:
                return reply(False, "SOURCE_INVALID", "SQLite quick_check failed; no export was attempted.",
                             [{"action": "host", "hint": "Restore a known-good fixture source, then retry."}],
                             diagnostics=integrity)
            rows = db.execute("SELECT id, name, quantity FROM products ORDER BY id").fetchall()
    except sqlite3.Error as exc:
        return reply(False, "DATABASE_ERROR", str(exc),
                     [{"action": "host", "hint": "Restore the fixture database with the products table, then retry."}])
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["id", "name", "quantity"])
    writer.writerows(rows)
    payload = stream.getvalue().encode("utf-8")
    output = root / name
    try:
        with output.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        return reply(False, "OUTPUT_EXISTS", "The selected output already exists; it was not changed.",
                     [{"action": "export", "hint": "Choose a new CSV basename and retry with the same observed versions."}])
    except OSError as exc:
        return reply(False, "OUTPUT_ERROR", str(exc),
                     [{"action": "host", "hint": "Check free space and trial-directory permissions. "
                       "A partial file may exist; inspect it and retry with a fresh basename."}])
    try:
        observed = output.read_bytes()
    except OSError as exc:
        return reply(False, "READBACK_ERROR", str(exc),
                     [{"action": "host", "hint": "Inspect output availability and permissions; export is unverified."}])
    if observed != payload:
        return reply(False, "OUTPUT_CHANGED", "Read-back bytes differ from the export snapshot.",
                     [{"action": "host", "hint": "Stop concurrent modifications; inspect the output and retry with a new name."}])
    return reply(True, "EXPORTED", "Exported products and verified the output bytes against the selected snapshot.",
                 [{"action": "report", "hint": "Report the returned row count, file hash and scope; no broader database validation is implied."}],
                 evidence={"observed_at": datetime.now(timezone.utc).isoformat(),
                           "producer": "sqlite_export.py / Python sqlite3 and filesystem read-back",
                           "source": str(source), "query": "SELECT id, name, quantity FROM products ORDER BY id",
                           "quick_check": integrity, "data_rows": len(rows),
                           "output": str(output), "bytes": len(observed),
                           "sha256": hashlib.sha256(observed).hexdigest(),
                           "snapshot_bytes_match": True})


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--setup":
        print(json.dumps({"trial_directory": str(setup(sys.argv[2]))}))
    elif len(sys.argv) == 2:
        try:
            request = json.load(sys.stdin)
        except json.JSONDecodeError:
            print(json.dumps(reply(False, "INVALID_JSON", "Input must be one JSON object.",
                                   [{"action": "instructions"}])) )
            sys.exit(1)
        result = call(sys.argv[1], request)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["ok"] else 1)
    else:
        sys.exit("usage: sqlite_export.py --setup NEW_DIRECTORY | sqlite_export.py TRIAL_DIRECTORY < request.json")
