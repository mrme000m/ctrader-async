#!/usr/bin/env python3
"""Static protobuf assignment audit.

Scans source files for patterns like:
    req = ProtoOA...()
    req.someField = ...
and verifies `someField` exists on the protobuf message descriptor.
"""

from __future__ import annotations

import ast
import os
import sys
import types
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "ctc"
MSG_DIR = SRC / "messages"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_pb2_field_map() -> tuple[dict[str, set[str]], set[str]]:
    sys.modules.setdefault("ctc", types.ModuleType("ctc"))
    sys.modules.setdefault("ctc.messages", types.ModuleType("ctc.messages"))

    cmm = _load_module(MSG_DIR / "OpenApiCommonModelMessages_pb2.py", "ctc.messages.OpenApiCommonModelMessages_pb2")
    cm = _load_module(MSG_DIR / "OpenApiCommonMessages_pb2.py", "ctc.messages.OpenApiCommonMessages_pb2")
    mm = _load_module(MSG_DIR / "OpenApiModelMessages_pb2.py", "ctc.messages.OpenApiModelMessages_pb2")
    m = _load_module(MSG_DIR / "OpenApiMessages_pb2.py", "ctc.messages.OpenApiMessages_pb2")

    modules = [cmm, cm, mm, m]
    field_map: dict[str, set[str]] = {}
    msg_names: set[str] = set()
    for mod in modules:
        for name in dir(mod):
            obj = getattr(mod, name)
            if hasattr(obj, "DESCRIPTOR") and hasattr(obj.DESCRIPTOR, "fields"):
                fields = {f.name for f in obj.DESCRIPTOR.fields}
                if fields:
                    field_map[name] = fields
                    msg_names.add(name)
    return field_map, msg_names


class AssignmentVisitor(ast.NodeVisitor):
    def __init__(self, msg_names: set[str]):
        self.msg_names = msg_names
        self.var_to_msg: dict[str, str] = {}
        self.assignments: list[tuple[int, str, str, str]] = []  # line, var, msg, field

    def visit_Assign(self, node: ast.Assign):
        # Track var = ProtoXxx()
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and call.func.id in self.msg_names:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_to_msg[target.id] = call.func.id

        # Track var.field = ...
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                var = target.value.id
                field = target.attr
                msg = self.var_to_msg.get(var)
                if msg:
                    self.assignments.append((node.lineno, var, msg, field))

        self.generic_visit(node)



def main() -> int:
    field_map, msg_names = load_pb2_field_map()

    findings: list[tuple[Path, int, str, str, str]] = []
    py_files = sorted(SRC.rglob("*.py"))

    for path in py_files:
        # skip generated protobuf modules
        if path.name.endswith("_pb2.py"):
            continue
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError:
            continue

        visitor = AssignmentVisitor(msg_names)
        visitor.visit(tree)

        for lineno, var, msg, field in visitor.assignments:
            if field not in field_map.get(msg, set()):
                findings.append((path, lineno, var, msg, field))

    print("=" * 80)
    print("PROTOBUF ASSIGNMENT FIELD AUDIT")
    print("=" * 80)
    print(f"Scanned files: {len(py_files)}")
    print(f"Invalid assignments found: {len(findings)}")

    if findings:
        print("\nPotential mismatches:")
        for path, line, var, msg, field in findings[:200]:
            rel = path.relative_to(ROOT)
            print(f"  {rel}:{line}  {var}.{field} (message {msg})")
        return 1

    print("\n✅ No invalid protobuf field assignments detected in static scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
