import re
import sys
import types
import importlib.util
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def desc_summary(mod):
    d = mod.DESCRIPTOR
    msgs = {}
    enums = {}
    for name, msg in d.message_types_by_name.items():
        field_rows = []
        for field in msg.fields:
            if field.message_type is not None:
                type_ref = f"msg:{field.message_type.full_name}"
            elif field.enum_type is not None:
                type_ref = f"enum:{field.enum_type.full_name}"
            else:
                type_ref = ""
            field_rows.append((field.number, field.name, field.type, field.label, type_ref))
        msgs[name] = field_rows
    for name, enum in d.enum_types_by_name.items():
        enums[name] = [(value.number, value.name) for value in enum.values]
    return msgs, enums


def compare(name, local_mod, ref_mod):
    l_msgs, l_enums = desc_summary(local_mod)
    r_msgs, r_enums = desc_summary(ref_mod)
    issues = []

    only_local_msgs = sorted(set(l_msgs) - set(r_msgs))
    only_ref_msgs = sorted(set(r_msgs) - set(l_msgs))
    if only_local_msgs or only_ref_msgs:
        issues.append(("message_set", only_local_msgs, only_ref_msgs))

    for key in sorted(set(l_msgs) & set(r_msgs)):
        if l_msgs[key] != r_msgs[key]:
            issues.append(("message_fields", key))

    only_local_enums = sorted(set(l_enums) - set(r_enums))
    only_ref_enums = sorted(set(r_enums) - set(l_enums))
    if only_local_enums or only_ref_enums:
        issues.append(("enum_set", only_local_enums, only_ref_enums))

    for key in sorted(set(l_enums) & set(r_enums)):
        if l_enums[key] != r_enums[key]:
            issues.append(("enum_values", key))

    print(f"[{name}] issues={len(issues)}")
    for issue in issues[:20]:
        print("  ", issue)
    return issues


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    repomix = root / "docs/repomix-output-spotware-OpenApiPy-full.md"
    text = repomix.read_text()

    pattern = re.compile(
        r"## File: (ctrader_open_api/messages/(?:OpenApi(?:CommonModel|Common|Model)?Messages_pb2\.py))\n(`{3,})python\n(.*?)\n\2",
        re.S,
    )
    blocks = {m.group(1): m.group(3) for m in pattern.finditer(text)}

    needed = [
        "ctrader_open_api/messages/OpenApiCommonMessages_pb2.py",
        "ctrader_open_api/messages/OpenApiCommonModelMessages_pb2.py",
        "ctrader_open_api/messages/OpenApiModelMessages_pb2.py",
        "ctrader_open_api/messages/OpenApiMessages_pb2.py",
    ]

    missing = [name for name in needed if name not in blocks]
    if missing:
        print("MISSING_BLOCKS", missing)
        return 2

    ref_dir = root / ".tmp_ref_pb2"
    ref_dir.mkdir(exist_ok=True)
    for rel in needed:
        (ref_dir / Path(rel).name).write_text(blocks[rel])

    sys.modules["ctc"] = types.ModuleType("ctc")
    sys.modules["ctc.messages"] = types.ModuleType("ctc.messages")

    local_common_model = load_module(
        root / "src/ctc/messages/OpenApiCommonModelMessages_pb2.py",
        "ctc.messages.OpenApiCommonModelMessages_pb2",
    )
    local_common = load_module(
        root / "src/ctc/messages/OpenApiCommonMessages_pb2.py",
        "ctc.messages.OpenApiCommonMessages_pb2",
    )
    local_model = load_module(
        root / "src/ctc/messages/OpenApiModelMessages_pb2.py",
        "ctc.messages.OpenApiModelMessages_pb2",
    )
    local_msgs = load_module(
        root / "src/ctc/messages/OpenApiMessages_pb2.py",
        "ctc.messages.OpenApiMessages_pb2",
    )

    sys.modules["ctrader_open_api"] = types.ModuleType("ctrader_open_api")
    sys.modules["ctrader_open_api.messages"] = types.ModuleType("ctrader_open_api.messages")

    ref_common_model = load_module(
        ref_dir / "OpenApiCommonModelMessages_pb2.py",
        "ctrader_open_api.messages.OpenApiCommonModelMessages_pb2",
    )
    ref_common = load_module(
        ref_dir / "OpenApiCommonMessages_pb2.py",
        "ctrader_open_api.messages.OpenApiCommonMessages_pb2",
    )
    ref_model = load_module(
        ref_dir / "OpenApiModelMessages_pb2.py",
        "ctrader_open_api.messages.OpenApiModelMessages_pb2",
    )
    ref_msgs = load_module(
        ref_dir / "OpenApiMessages_pb2.py",
        "ctrader_open_api.messages.OpenApiMessages_pb2",
    )

    all_issues = []
    all_issues.extend(compare("OpenApiCommonMessages", local_common, ref_common))
    all_issues.extend(compare("OpenApiCommonModelMessages", local_common_model, ref_common_model))
    all_issues.extend(compare("OpenApiModelMessages", local_model, ref_model))
    all_issues.extend(compare("OpenApiMessages", local_msgs, ref_msgs))

    print("TOTAL_ISSUES", len(all_issues))
    return 1 if all_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
