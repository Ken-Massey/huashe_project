"""Functions for Chapter 1 of DB32/T 4351-2022.

Generated from the main body clauses of the source Markdown.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": "Unified clause result. Call result.to_dict() for JSON serialization.",
    "fields": {
        "clause": {"type": "str", "description": "Clause number."},
        "chapter": {"type": "str", "description": "Chapter title."},
        "section": {"type": "str", "description": "Section title."},
        "title": {"type": "str", "description": "Clause topic."},
        "applicable": {"type": "bool", "description": "Whether this clause applies to the current object."},
        "status": {"type": "str", "description": "compliant, non_compliant, not_applicable, or pending_review."},
        "result": {"type": "str", "description": "Evaluation conclusion generated from input parameters."},
        "requirements": {"type": "list[str]", "description": "Review items extracted from the clause."},
        "matched_items": {"type": "list[str]", "description": "Requirements matched by confirmed_items."},
        "missing_items": {"type": "list[str]", "description": "Requirements not matched when strict=True."},
        "inputs": {"type": "dict[str, Any]", "description": "Original call inputs."},
        "basis": {"type": "str", "description": "Source clause text used as basis."},
        "notes": {"type": "list[str]", "description": "Additional notes or reasons for non-applicability."},
    },
}


@dataclass(frozen=True)
class ClauseResult:
    clause: str
    chapter: str
    section: str
    title: str
    applicable: bool
    status: str
    result: str
    requirements: list[str]
    matched_items: list[str]
    missing_items: list[str]
    inputs: dict[str, Any]
    basis: str
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_list(values: Iterable[str] | None) -> list[str]:
    return [str(value).strip() for value in values or [] if str(value).strip()]


def _matches(requirement: str, confirmed_items: list[str]) -> bool:
    return any(item == requirement or item in requirement or requirement in item for item in confirmed_items)


def _evaluate_clause(
    *,
    clause: str,
    chapter: str,
    section: str,
    title: str,
    basis: str,
    requirements: list[str],
    applicable: bool,
    confirmed_items: Iterable[str] | None,
    measured_values: Mapping[str, Any] | None,
    notes: Iterable[str] | None,
    strict: bool,
) -> ClauseResult:
    confirmed = _as_list(confirmed_items)
    matched = [item for item in requirements if _matches(item, confirmed)]
    missing = [item for item in requirements if item not in matched] if strict else []
    if not applicable:
        status = "not_applicable"
        result = f"{clause} is not applicable to the current object."
    elif missing:
        status = "non_compliant"
        result = f"{clause} does not satisfy all clause review items; {len(missing)} item(s) missing."
    elif matched:
        status = "compliant"
        result = f"{clause} satisfies the confirmed clause review items."
    else:
        status = "pending_review"
        result = f"{clause} has no confirmed items; review against the listed requirements."
    return ClauseResult(
        clause=clause,
        chapter=chapter,
        section=section,
        title=title,
        applicable=applicable,
        status=status,
        result=result,
        requirements=requirements,
        matched_items=matched,
        missing_items=missing,
        inputs={
            "applicable": applicable,
            "confirmed_items": confirmed,
            "measured_values": dict(measured_values or {}),
            "strict": strict,
        },
        basis=basis,
        notes=_as_list(notes),
    )

CLAUSE_1_0_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_1_0_1',
 'clause': '1.0.1',
 'chapter': '总 则',
 'section': '1 总 则',
 'title': '为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。',
 'description': 'Evaluate whether the current object satisfies this clause.',
 'inputs': {'applicable': {'type': 'bool',
                           'required': False,
                           'default': True,
                           'description': 'Whether this clause applies.'},
            'confirmed_items': {'type': 'Iterable[str] | None',
                                'required': False,
                                'default': None,
                                'description': 'Satisfied clause items. Values may be exact requirements or keywords.'},
            'measured_values': {'type': 'Mapping[str, Any] | None',
                                'required': False,
                                'default': None,
                                'description': 'Related measurements, design values, grades, distances, IDs, or other '
                                               'structured data.'},
            'notes': {'type': 'Iterable[str] | None',
                      'required': False,
                      'default': None,
                      'description': 'Additional notes or non-applicability reasons.'},
            'strict': {'type': 'bool',
                       'required': False,
                       'default': True,
                       'description': 'When True, unmatched requirements are reported in missing_items.'}},
 'requirements': ['为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。'],
 'output': OUTPUT_SCHEMA}


def clause_1_0_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """1.0.1 为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。."""

    return _evaluate_clause(
        clause='1.0.1',
        chapter='总 则',
        section='1 总 则',
        title='为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。',
        basis='1.0.1 为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。',
        requirements=['为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_1_0_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_1_0_2',
 'clause': '1.0.2',
 'chapter': '总 则',
 'section': '1 总 则',
 'title': '本规程适用于江苏省内在建、已建成及已运营的城市轨道交通结构的安全保护工作。城际轨道交通和市域（郊）铁路的结构安全保护工作可参照执行。',
 'description': 'Evaluate whether the current object satisfies this clause.',
 'inputs': {'applicable': {'type': 'bool',
                           'required': False,
                           'default': True,
                           'description': 'Whether this clause applies.'},
            'confirmed_items': {'type': 'Iterable[str] | None',
                                'required': False,
                                'default': None,
                                'description': 'Satisfied clause items. Values may be exact requirements or keywords.'},
            'measured_values': {'type': 'Mapping[str, Any] | None',
                                'required': False,
                                'default': None,
                                'description': 'Related measurements, design values, grades, distances, IDs, or other '
                                               'structured data.'},
            'notes': {'type': 'Iterable[str] | None',
                      'required': False,
                      'default': None,
                      'description': 'Additional notes or non-applicability reasons.'},
            'strict': {'type': 'bool',
                       'required': False,
                       'default': True,
                       'description': 'When True, unmatched requirements are reported in missing_items.'}},
 'requirements': ['本规程适用于江苏省内在建、已建成及已运营的城市轨道交通结构的安全保护工作。城际轨道交通和市域（郊）铁路的结构安全保护工作可参照执行。'],
 'output': OUTPUT_SCHEMA}


def clause_1_0_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """1.0.2 本规程适用于江苏省内在建、已建成及已运营的城市轨道交通结构的安全保护工作。城际轨道交通和市域（郊）铁路的结构安全保护工作可参照执行。."""

    return _evaluate_clause(
        clause='1.0.2',
        chapter='总 则',
        section='1 总 则',
        title='本规程适用于江苏省内在建、已建成及已运营的城市轨道交通结构的安全保护工作。城际轨道交通和市域（郊）铁路的结构安全保护工作可参照执行。',
        basis='1.0.2 本规程适用于江苏省内在建、已建成及已运营的城市轨道交通结构的安全保护工作。城际轨道交通和市域（郊）铁路的结构安全保护工作可参照执行。',
        requirements=['本规程适用于江苏省内在建、已建成及已运营的城市轨道交通结构的安全保护工作。城际轨道交通和市域（郊）铁路的结构安全保护工作可参照执行。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_1_0_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_1_0_3',
 'clause': '1.0.3',
 'chapter': '总 则',
 'section': '1 总 则',
 'title': '城市轨道交通结构的安全保护除应符合本规程外，尚应符合国家及行业现行有关标准的规定。',
 'description': 'Evaluate whether the current object satisfies this clause.',
 'inputs': {'applicable': {'type': 'bool',
                           'required': False,
                           'default': True,
                           'description': 'Whether this clause applies.'},
            'confirmed_items': {'type': 'Iterable[str] | None',
                                'required': False,
                                'default': None,
                                'description': 'Satisfied clause items. Values may be exact requirements or keywords.'},
            'measured_values': {'type': 'Mapping[str, Any] | None',
                                'required': False,
                                'default': None,
                                'description': 'Related measurements, design values, grades, distances, IDs, or other '
                                               'structured data.'},
            'notes': {'type': 'Iterable[str] | None',
                      'required': False,
                      'default': None,
                      'description': 'Additional notes or non-applicability reasons.'},
            'strict': {'type': 'bool',
                       'required': False,
                       'default': True,
                       'description': 'When True, unmatched requirements are reported in missing_items.'}},
 'requirements': ['城市轨道交通结构的安全保护除应符合本规程外，尚应符合国家及行业现行有关标准的规定。 # 2 术语'],
 'output': OUTPUT_SCHEMA}


def clause_1_0_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """1.0.3 城市轨道交通结构的安全保护除应符合本规程外，尚应符合国家及行业现行有关标准的规定。."""

    return _evaluate_clause(
        clause='1.0.3',
        chapter='总 则',
        section='1 总 则',
        title='城市轨道交通结构的安全保护除应符合本规程外，尚应符合国家及行业现行有关标准的规定。',
        basis='1.0.3 城市轨道交通结构的安全保护除应符合本规程外，尚应符合国家及行业现行有关标准的规定。 # 2 术语',
        requirements=['城市轨道交通结构的安全保护除应符合本规程外，尚应符合国家及行业现行有关标准的规定。 # 2 术语'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_1_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_1_functions",
    "chapter": '总 则',
    "description": "DB32/T 4351-2022 chapter 1 clause function API schema.",
    "functions": {
        "clause_1_0_1": CLAUSE_1_0_1_INPUT_SCHEMA,
        "clause_1_0_2": CLAUSE_1_0_2_INPUT_SCHEMA,
        "clause_1_0_3": CLAUSE_1_0_3_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_1_0_1(confirmed_items=['为保护城市轨道交通结构，明确结构安全保护的技术要求和规范外部作业控制的技术标准，确保结构的承载能力和正常使用，制定本规程。'], strict=False)
    print(first.to_dict())
