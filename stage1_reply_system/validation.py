"""Validate stage-one input objects against the local JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SCHEMA = Path(__file__).resolve().parent / "config" / "input_schema.json"


def _resolve_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"Only local references are supported: {reference}")
    value: Any = root_schema
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def _matches_type(value: Any, expected: str) -> bool:
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


def validate_value(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], path: str = "$") -> list[str]:
    if "$ref" in schema:
        schema = _resolve_ref(root_schema, schema["$ref"])
    errors: list[str] = []
    expected_types = schema.get("type")
    if expected_types:
        expected_types = [expected_types] if isinstance(expected_types, str) else expected_types
        if not any(_matches_type(value, expected) for expected in expected_types):
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
            errors.extend(f"{path}.{name}: unknown field" for name in value if name not in properties)
        for name, child in value.items():
            if name in properties:
                errors.extend(validate_value(child, properties[name], root_schema, f"{path}.{name}"))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: requires at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path}: array items must be unique")
        if schema.get("items"):
            for index, item in enumerate(value):
                errors.extend(validate_value(item, schema["items"], root_schema, f"{path}[{index}]"))
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


def validate_input(data: dict[str, Any], schema_path: str | Path = DEFAULT_SCHEMA) -> list[str]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    return validate_value(data, schema, schema)
