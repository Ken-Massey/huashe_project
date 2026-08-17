import argparse
import importlib.util
import json
import sys
from pathlib import Path

from common import ensure_dir, write_json


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def iter_clause_functions(module):
    for name in sorted(dir(module)):
        if name.startswith("clause_") and callable(getattr(module, name)):
            yield name, getattr(module, name)


def build_rule_inputs(case_data, use_payload):
    if use_payload:
        payload = case_data.get("rule_check_payload") or {}
        measured_values = payload.get("measured_values") or {}
        confirmed_items = payload.get("confirmed_items") or []
        notes = payload.get("notes") or []
    else:
        measured_values = {
            key: value
            for key, value in (case_data.get("measured_values") or case_data.get("attributes") or {}).items()
            if value is not None
        }
        confirmed_items = case_data.get("confirmed_items") or []
        notes = []
    return measured_values, confirmed_items, notes


def result_to_dict(result):
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if isinstance(result, dict):
        return result
    return {"raw_result": str(result)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_json_dir")
    parser.add_argument(
        "--chapter-dir",
        default="../chapter_1_functions",
        help="Folder containing chapter_1_functions.py, chapter_2_functions.py, etc.",
    )
    parser.add_argument("-o", "--output", default="outputs/rule_check_results")
    parser.add_argument(
        "--all-measured-values",
        action="store_true",
        help="Use all non-null measured_values from the full case JSON instead of rule_check_payload.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Pass strict=True to clause functions. Default is False for early-stage review.",
    )
    args = parser.parse_args()

    out_dir = Path(args.output)
    ensure_dir(out_dir)
    chapter_dir = Path(args.chapter_dir)
    chapter_files = sorted(chapter_dir.glob("chapter_*_functions.py"))
    if not chapter_files:
        raise FileNotFoundError(f"No chapter function files found in {chapter_dir}")

    modules = []
    module_errors = []
    for chapter_file in chapter_files:
        try:
            modules.append((chapter_file.name, load_module(chapter_file)))
        except Exception as exc:
            module_errors.append({"module_file": str(chapter_file), "error": repr(exc)})

    for case_path in Path(args.case_json_dir).glob("*.case.json"):
        case_data = json.loads(case_path.read_text(encoding="utf-8"))
        measured_values, confirmed_items, notes = build_rule_inputs(
            case_data,
            use_payload=not args.all_measured_values,
        )
        clause_results = []
        call_errors = []
        for module_file, module in modules:
            for function_name, function in iter_clause_functions(module):
                try:
                    result = function(
                        applicable=True,
                        confirmed_items=confirmed_items,
                        measured_values=measured_values,
                        notes=notes,
                        strict=args.strict,
                    )
                    item = result_to_dict(result)
                    item["module_file"] = module_file
                    item["function"] = function_name
                    clause_results.append(item)
                except Exception as exc:
                    call_errors.append(
                        {
                            "module_file": module_file,
                            "function": function_name,
                            "error": repr(exc),
                        }
                    )

        summary = {}
        for item in clause_results:
            status = item.get("status", "unknown")
            summary[status] = summary.get(status, 0) + 1

        output = {
            "format_version": "rule_check_result_v1",
            "doc_id": case_data.get("doc_id"),
            "source_case_json": str(case_path),
            "input_mode": "all_measured_values" if args.all_measured_values else "rule_check_payload",
            "strict": args.strict,
            "measured_values": measured_values,
            "confirmed_items": confirmed_items,
            "notes": notes,
            "summary": summary,
            "module_load_errors": module_errors,
            "call_errors": call_errors,
            "clause_results": clause_results,
        }
        out_path = out_dir / case_path.name.replace(".case.json", ".rule_check.json")
        write_json(out_path, output)
        print(f"rule checked: {out_path.name}, clauses={len(clause_results)}, summary={summary}")


if __name__ == "__main__":
    main()
