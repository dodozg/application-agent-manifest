#!/usr/bin/env python3
"""Structural/path validator for AAM discussion draft 0.1; no trust assessment."""
import json
import sys
from pathlib import Path, PurePosixPath


class ManifestError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise ManifestError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def local_file(root, value, label):
    need(nonempty(value), f"{label}: expected a nonempty relative path")
    need("\\" not in value and not value.startswith("/") and ":" not in value,
         f"{label}: only package-relative POSIX paths allowed")
    p = PurePosixPath(value)
    need(all(part not in (".", "..") for part in value.split("/")) and bool(p.parts),
         f"{label}: traversal or empty segment")
    target = root.joinpath(*p.parts)
    need(target.is_relative_to(root), f"{label}: outside package")
    current = root
    for part in p.parts:
        current = current / part
        need(not current.is_symlink(), f"{label}: symlink forbidden")
    need(target.is_file(), f"{label}: file does not exist: {value}")


def validate(path):
    path = Path(path).absolute()
    need(path.name == "application-agent.json", "expected application-agent.json")
    need(path.is_file() and not path.is_symlink(), "manifest must be a regular file")
    root = path.parent
    data = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(data, dict), "root must be an object")
    need(data.get("format") == "aam-draft-0.1", "unsupported format")
    app = data.get("application")
    need(isinstance(app, dict), "application must be an object")
    for field in ("id", "name"):
        need(nonempty(app.get(field)), f"application.{field} is required")
    versions = app.get("tested_versions")
    need(isinstance(versions, list) and bool(versions) and all(map(nonempty, versions)),
         "application.tested_versions must be nonempty strings")
    local_file(root, data.get("operator_guide"), "operator_guide")
    interfaces = data.get("interfaces")
    need(isinstance(interfaces, list) and bool(interfaces), "interfaces must be nonempty array")
    for i, interface in enumerate(interfaces):
        need(isinstance(interface, dict), f"interfaces[{i}] must be an object")
        need(interface.get("kind") in ("mcp", "api", "cli", "gui"), f"interfaces[{i}].kind invalid")
        need(nonempty(interface.get("locator")), f"interfaces[{i}].locator required")
        if "documentation" in interface:
            local_file(root, interface["documentation"], f"interfaces[{i}].documentation")
    checks = data.get("checks")
    need(isinstance(checks, dict) and bool(checks), "checks must be a nonempty object")
    for key, check in checks.items():
        need(nonempty(key) and isinstance(check, dict), "invalid check entry")
        for field in ("description", "producer", "observation"):
            need(nonempty(check.get(field)), f"checks.{key}.{field} required")
    operations = data.get("operations")
    need(isinstance(operations, list) and bool(operations), "operations must be nonempty array")
    seen = set()
    for i, op in enumerate(operations):
        need(isinstance(op, dict), f"operations[{i}] must be an object")
        ident = op.get("id")
        need(nonempty(ident) and ident not in seen, f"operations[{i}].id missing or duplicate")
        seen.add(ident)
        need(nonempty(op.get("description")), f"operations[{i}].description required")
        need(op.get("risk") in ("read", "modify", "external"), f"operations[{i}].risk invalid")
        local_file(root, op.get("workflow"), f"operations[{i}].workflow")
        evidence = op.get("evidence")
        need(isinstance(evidence, list) and bool(evidence) and
             all(nonempty(x) and x in checks for x in evidence),
             f"operations[{i}].evidence must reference checks")
    return data


if __name__ == "__main__":
    try:
        need(len(sys.argv) == 2, "usage: python3 validate.py PATH/application-agent.json")
        result = validate(sys.argv[1])
        print(f"VALID draft structure: {result['application']['name']}")
    except (ManifestError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        sys.exit(1)
