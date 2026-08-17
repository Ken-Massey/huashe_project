import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "config" / "input_schema.json"
DEFAULT_INPUT = ROOT / "examples" / "project_input.example.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"Only local references are supported: {reference}")
    value: Any = root_schema
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def matches_type(value: Any, expected: str) -> bool:
    checks = {
        "null": value is None,
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
    }
    return checks.get(expected, True)


def validate(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], path: str = "$" ) -> list[str]:
    if "$ref" in schema:
        schema = resolve_ref(root_schema, schema["$ref"])

    errors: list[str] = []
    expected_types = schema.get("type")
    if expected_types:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(matches_type(value, expected) for expected in expected_types):
            return [f"{path}: expected type {expected_types}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not in {schema['enum']!r}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}.{name}: required field is missing")
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in properties:
                    errors.append(f"{path}.{name}: unknown field")
        for name, child in value.items():
            if name in properties:
                errors.extend(validate(child, properties[name], root_schema, f"{path}.{name}"))

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: requires at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path}: array items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate(item, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{path}: string is shorter than {schema['minLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is less than minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is greater than maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: {value} must be greater than {schema['exclusiveMinimum']}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a stage-one project input JSON file.")
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    schema = load_json(args.schema)
    data = load_json(args.input)
    errors = validate(data, schema, schema)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"VALIDATION OK: {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
