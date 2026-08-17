"""Functions for Chapter 5 of DB32/T 4351-2022.

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

CLAUSE_5_1_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_1_1',
 'clause': '5.1.1',
 'chapter': '外部作业控制',
 'section': '5.1 一般规定',
 'title': '在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。',
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
 'requirements': ['在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。'],
 'output': OUTPUT_SCHEMA}


def clause_5_1_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.1.1 在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。."""

    return _evaluate_clause(
        clause='5.1.1',
        chapter='外部作业控制',
        section='5.1 一般规定',
        title='在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。',
        basis='5.1.1 在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。',
        requirements=['在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_1_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_1_2',
 'clause': '5.1.2',
 'chapter': '外部作业控制',
 'section': '5.1 一般规定',
 'title': '外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑各项作业对城市轨道交通结构',
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
 'requirements': ['外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑各项作业对城市轨道交通结构产生的叠加影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_1_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.1.2 外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑各项作业对城市轨道交通结构."""

    return _evaluate_clause(
        clause='5.1.2',
        chapter='外部作业控制',
        section='5.1 一般规定',
        title='外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑各项作业对城市轨道交通结构',
        basis='5.1.2 外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑各项作业对城市轨道交通结构产生的叠加影响。',
        requirements=['外部作业工程实施方案包括外部作业设计和施工方案、安全评估、轨道交通结构专项保护方案和应急预案等。同一场地存在多项外部作业时，应综合考虑各项作业对城市轨道交通结构产生的叠加影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_1_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_1_3',
 'clause': '5.1.3',
 'chapter': '外部作业控制',
 'section': '5.1 一般规定',
 'title': '临近城市轨道交通线路建设对振动、噪声等敏感的建（物）筑物时，应充分考虑城市轨道交通运营对其产生的环境影响，并做好相关控制措施。',
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
 'requirements': ['临近城市轨道交通线路建设对振动、噪声等敏感的建（物）筑物时，应充分考虑城市轨道交通运营对其产生的环境影响，并做好相关控制措施。'],
 'output': OUTPUT_SCHEMA}


def clause_5_1_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.1.3 临近城市轨道交通线路建设对振动、噪声等敏感的建（物）筑物时，应充分考虑城市轨道交通运营对其产生的环境影响，并做好相关控制措施。."""

    return _evaluate_clause(
        clause='5.1.3',
        chapter='外部作业控制',
        section='5.1 一般规定',
        title='临近城市轨道交通线路建设对振动、噪声等敏感的建（物）筑物时，应充分考虑城市轨道交通运营对其产生的环境影响，并做好相关控制措施。',
        basis='5.1.3 临近城市轨道交通线路建设对振动、噪声等敏感的建（物）筑物时，应充分考虑城市轨道交通运营对其产生的环境影响，并做好相关控制措施。',
        requirements=['临近城市轨道交通线路建设对振动、噪声等敏感的建（物）筑物时，应充分考虑城市轨道交通运营对其产生的环境影响，并做好相关控制措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_1_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_1_4',
 'clause': '5.1.4',
 'chapter': '外部作业控制',
 'section': '5.1 一般规定',
 'title': '外部作业造成城市轨道交通结构损伤时，应及时采取加固措施，加固后的轨道交通结构承载能力、正常使用功能及耐久性能等应满足后续使用年限内的安全运营要求。',
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
 'requirements': ['外部作业造成城市轨道交通结构损伤时，应及时采取加固措施，加固后的轨道交通结构承载能力、正常使用功能及耐久性能等应满足后续使用年限内的安全运营要求。'],
 'output': OUTPUT_SCHEMA}


def clause_5_1_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.1.4 外部作业造成城市轨道交通结构损伤时，应及时采取加固措施，加固后的轨道交通结构承载能力、正常使用功能及耐久性能等应满足后续使用年限内的安全运营要求。."""

    return _evaluate_clause(
        clause='5.1.4',
        chapter='外部作业控制',
        section='5.1 一般规定',
        title='外部作业造成城市轨道交通结构损伤时，应及时采取加固措施，加固后的轨道交通结构承载能力、正常使用功能及耐久性能等应满足后续使用年限内的安全运营要求。',
        basis='5.1.4 外部作业造成城市轨道交通结构损伤时，应及时采取加固措施，加固后的轨道交通结构承载能力、正常使用功能及耐久性能等应满足后续使用年限内的安全运营要求。',
        requirements=['外部作业造成城市轨道交通结构损伤时，应及时采取加固措施，加固后的轨道交通结构承载能力、正常使用功能及耐久性能等应满足后续使用年限内的安全运营要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_1_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_1_5',
 'clause': '5.1.5',
 'chapter': '外部作业控制',
 'section': '5.1 一般规定',
 'title': '外部作业应综合考虑施工、工后沉降或运营振动等对城市轨道交通结构造成的直接不利影响，同时也应考虑因外部作业导致周边建（构）筑物、地下管线变形过大或破坏对轨道交通结',
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
 'requirements': ['外部作业应综合考虑施工、工后沉降或运营振动等对城市轨道交通结构造成的直接不利影响，同时也应考虑因外部作业导致周边建（构）筑物、地下管线变形过大或破坏对轨道交通结构造成的间接不利影响。 # 5.2 '
                  '基坑工程'],
 'output': OUTPUT_SCHEMA}


def clause_5_1_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.1.5 外部作业应综合考虑施工、工后沉降或运营振动等对城市轨道交通结构造成的直接不利影响，同时也应考虑因外部作业导致周边建（构）筑物、地下管线变形过大或破坏对轨道交通结."""

    return _evaluate_clause(
        clause='5.1.5',
        chapter='外部作业控制',
        section='5.1 一般规定',
        title='外部作业应综合考虑施工、工后沉降或运营振动等对城市轨道交通结构造成的直接不利影响，同时也应考虑因外部作业导致周边建（构）筑物、地下管线变形过大或破坏对轨道交通结',
        basis='5.1.5 外部作业应综合考虑施工、工后沉降或运营振动等对城市轨道交通结构造成的直接不利影响，同时也应考虑因外部作业导致周边建（构）筑物、地下管线变形过大或破坏对轨道交通结构造成的间接不利影响。 # 5.2 基坑工程',
        requirements=['外部作业应综合考虑施工、工后沉降或运营振动等对城市轨道交通结构造成的直接不利影响，同时也应考虑因外部作业导致周边建（构）筑物、地下管线变形过大或破坏对轨道交通结构造成的间接不利影响。 # 5.2 基坑工程'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_1',
 'clause': '5.2.1',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '外部基坑工程应遵循“近浅远深，近小远大，先远后近”的设计和施工原则，并应综合考虑基坑施工全过程及上部',
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
 'requirements': ['外部基坑工程应遵循“近浅远深，近小远大，先远后近”的设计和施工原则，并应综合考虑基坑施工全过程及上部 建筑施工对城市轨道交通结构的不利影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.1 外部基坑工程应遵循“近浅远深，近小远大，先远后近”的设计和施工原则，并应综合考虑基坑施工全过程及上部."""

    return _evaluate_clause(
        clause='5.2.1',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='外部基坑工程应遵循“近浅远深，近小远大，先远后近”的设计和施工原则，并应综合考虑基坑施工全过程及上部',
        basis='5.2.1 外部基坑工程应遵循“近浅远深，近小远大，先远后近”的设计和施工原则，并应综合考虑基坑施工全过程及上部 建筑施工对城市轨道交通结构的不利影响。',
        requirements=['外部基坑工程应遵循“近浅远深，近小远大，先远后近”的设计和施工原则，并应综合考虑基坑施工全过程及上部 建筑施工对城市轨道交通结构的不利影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_2',
 'clause': '5.2.2',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '外部基坑的不同部位可采用不同的外部作业影响等级，相邻部位的级差不宜大于一级，并应设置可靠的过渡措施。',
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
 'requirements': ['外部基坑的不同部位可采用不同的外部作业影响等级，相邻部位的级差不宜大于一级，并应设置可靠的过渡措施。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.2 外部基坑的不同部位可采用不同的外部作业影响等级，相邻部位的级差不宜大于一级，并应设置可靠的过渡措施。."""

    return _evaluate_clause(
        clause='5.2.2',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='外部基坑的不同部位可采用不同的外部作业影响等级，相邻部位的级差不宜大于一级，并应设置可靠的过渡措施。',
        basis='5.2.2 外部基坑的不同部位可采用不同的外部作业影响等级，相邻部位的级差不宜大于一级，并应设置可靠的过渡措施。',
        requirements=['外部基坑的不同部位可采用不同的外部作业影响等级，相邻部位的级差不宜大于一级，并应设置可靠的过渡措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_3',
 'clause': '5.2.3',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '当外部基坑横跨城市轨道交通结构上方时，宜采取分坑措施将外部基坑分为上方基坑和侧方基坑，根据其不同属性分别进行设计与施工，并综合考虑各分坑的叠加影响。',
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
 'requirements': ['当外部基坑横跨城市轨道交通结构上方时，宜采取分坑措施将外部基坑分为上方基坑和侧方基坑，根据其不同属性分别进行设计与施工，并综合考虑各分坑的叠加影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.3 当外部基坑横跨城市轨道交通结构上方时，宜采取分坑措施将外部基坑分为上方基坑和侧方基坑，根据其不同属性分别进行设计与施工，并综合考虑各分坑的叠加影响。."""

    return _evaluate_clause(
        clause='5.2.3',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='当外部基坑横跨城市轨道交通结构上方时，宜采取分坑措施将外部基坑分为上方基坑和侧方基坑，根据其不同属性分别进行设计与施工，并综合考虑各分坑的叠加影响。',
        basis='5.2.3 当外部基坑横跨城市轨道交通结构上方时，宜采取分坑措施将外部基坑分为上方基坑和侧方基坑，根据其不同属性分别进行设计与施工，并综合考虑各分坑的叠加影响。',
        requirements=['当外部基坑横跨城市轨道交通结构上方时，宜采取分坑措施将外部基坑分为上方基坑和侧方基坑，根据其不同属性分别进行设计与施工，并综合考虑各分坑的叠加影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_4',
 'clause': '5.2.4',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。',
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
 'requirements': ['当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.4 当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。."""

    return _evaluate_clause(
        clause='5.2.4',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。',
        basis='5.2.4 当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。',
        requirements=['当外部基坑位于城市轨道交通结构正上方时，竖向净距控制宜满足本规程表3.3.1的相关规定，有特殊要求时应通过专项评估确定既有结构上方的残余覆土厚度。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_5',
 'clause': '5.2.5',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '对于软土地区规模较大的外部基坑工程，应采取分区或分坑措施降低单体基坑的开挖面积，并明确单体基坑的施工时序，减少时空效应影响。',
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
 'requirements': ['对于软土地区规模较大的外部基坑工程，应采取分区或分坑措施降低单体基坑的开挖面积，并明确单体基坑的施工时序，减少时空效应影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.5 对于软土地区规模较大的外部基坑工程，应采取分区或分坑措施降低单体基坑的开挖面积，并明确单体基坑的施工时序，减少时空效应影响。."""

    return _evaluate_clause(
        clause='5.2.5',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='对于软土地区规模较大的外部基坑工程，应采取分区或分坑措施降低单体基坑的开挖面积，并明确单体基坑的施工时序，减少时空效应影响。',
        basis='5.2.5 对于软土地区规模较大的外部基坑工程，应采取分区或分坑措施降低单体基坑的开挖面积，并明确单体基坑的施工时序，减少时空效应影响。',
        requirements=['对于软土地区规模较大的外部基坑工程，应采取分区或分坑措施降低单体基坑的开挖面积，并明确单体基坑的施工时序，减少时空效应影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_6',
 'clause': '5.2.6',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '当外部基坑横跨城市轨道交通结构时，分坑措施宜符合下列规定：',
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
 'requirements': ['基坑沿既有结构纵向分区长度不宜超过基坑与既有结构的竖向净距。', '既有结构上方地下室宜增加抗浮措施。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.6 当外部基坑横跨城市轨道交通结构时，分坑措施宜符合下列规定：."""

    return _evaluate_clause(
        clause='5.2.6',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='当外部基坑横跨城市轨道交通结构时，分坑措施宜符合下列规定：',
        basis='5.2.6 当外部基坑横跨城市轨道交通结构时，分坑措施宜符合下列规定： 1 采取地基土体加固措施时，加固体与轨道交通结构的水平及竖向净距均不宜小于 $2\\mathrm{m}$ 。 2 单体基坑施工对轨道交通结构影响较大，且结构安全状态达到3级及以上时应从严控制，必要时可在基坑内设置临时压重措施。 3 基坑沿既有结构纵向分区长度不宜超过基坑与既有结构的竖向净距。 4 既有结构上方地下室宜增加抗浮措施。',
        requirements=['基坑沿既有结构纵向分区长度不宜超过基坑与既有结构的竖向净距。', '既有结构上方地下室宜增加抗浮措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_7',
 'clause': '5.2.7',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则。重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。',
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
 'requirements': ['基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则。重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.7 基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则。重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。."""

    return _evaluate_clause(
        clause='5.2.7',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则。重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。',
        basis='5.2.7 基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则。重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。',
        requirements=['基坑土方开挖时应充分考虑时空效应，遵循“分层、分块、限时”的原则。重型机械设备、土方运输车辆的行进路线应避开城市轨道交通正上方区域，地面荷载应满足设计要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_8',
 'clause': '5.2.8',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '应保证基坑工程的围护结构及支撑系统与城市轨道交通结构的安全距离，当外部作业影响等级为特级、一级或有特殊要求时，应采用整体刚度较大的支护结构体系，并匹配相应的施工',
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
 'requirements': ['应保证基坑工程的围护结构及支撑系统与城市轨道交通结构的安全距离，当外部作业影响等级为特级、一级或有特殊要求时，应采用整体刚度较大的支护结构体系，并匹配相应的施工辅助措施以降低施工影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.8 应保证基坑工程的围护结构及支撑系统与城市轨道交通结构的安全距离，当外部作业影响等级为特级、一级或有特殊要求时，应采用整体刚度较大的支护结构体系，并匹配相应的施工."""

    return _evaluate_clause(
        clause='5.2.8',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='应保证基坑工程的围护结构及支撑系统与城市轨道交通结构的安全距离，当外部作业影响等级为特级、一级或有特殊要求时，应采用整体刚度较大的支护结构体系，并匹配相应的施工',
        basis='5.2.8 应保证基坑工程的围护结构及支撑系统与城市轨道交通结构的安全距离，当外部作业影响等级为特级、一级或有特殊要求时，应采用整体刚度较大的支护结构体系，并匹配相应的施工辅助措施以降低施工影响。',
        requirements=['应保证基坑工程的围护结构及支撑系统与城市轨道交通结构的安全距离，当外部作业影响等级为特级、一级或有特殊要求时，应采用整体刚度较大的支护结构体系，并匹配相应的施工辅助措施以降低施工影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_9_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_9',
 'clause': '5.2.9',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '支撑体系应根据基坑安全等级、规模、平面形状及城市轨道交通保护要求综合确定。当轨道交通结构安全保护要求较高或有特殊要求时，针对钢支撑体系可采用自动伺服系统。',
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
 'requirements': ['支撑体系应根据基坑安全等级、规模、平面形状及城市轨道交通保护要求综合确定。当轨道交通结构安全保护要求较高或有特殊要求时，针对钢支撑体系可采用自动伺服系统。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_9(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.9 支撑体系应根据基坑安全等级、规模、平面形状及城市轨道交通保护要求综合确定。当轨道交通结构安全保护要求较高或有特殊要求时，针对钢支撑体系可采用自动伺服系统。."""

    return _evaluate_clause(
        clause='5.2.9',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='支撑体系应根据基坑安全等级、规模、平面形状及城市轨道交通保护要求综合确定。当轨道交通结构安全保护要求较高或有特殊要求时，针对钢支撑体系可采用自动伺服系统。',
        basis='5.2.9 支撑体系应根据基坑安全等级、规模、平面形状及城市轨道交通保护要求综合确定。当轨道交通结构安全保护要求较高或有特殊要求时，针对钢支撑体系可采用自动伺服系统。',
        requirements=['支撑体系应根据基坑安全等级、规模、平面形状及城市轨道交通保护要求综合确定。当轨道交通结构安全保护要求较高或有特殊要求时，针对钢支撑体系可采用自动伺服系统。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_10_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_10',
 'clause': '5.2.10',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。',
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
 'requirements': ['基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_10(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.10 基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。."""

    return _evaluate_clause(
        clause='5.2.10',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。',
        basis='5.2.10 基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。',
        requirements=['基坑开挖影响深度内的潜水、微承压水与承压水控制应符合本规程第5.5节的相关规定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_11_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_11',
 'clause': '5.2.11',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露，邻近城市轨道交通结构侧的底板混凝土宜延伸至围护结构边。基坑内的局部深坑宜在浅部底板施工完',
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
 'requirements': ['基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露，邻近城市轨道交通结构侧的底板混凝土宜延伸至围护结构边。基坑内的局部深坑宜在浅部底板施工完成后开挖。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_11(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.11 基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露，邻近城市轨道交通结构侧的底板混凝土宜延伸至围护结构边。基坑内的局部深坑宜在浅部底板施工完."""

    return _evaluate_clause(
        clause='5.2.11',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露，邻近城市轨道交通结构侧的底板混凝土宜延伸至围护结构边。基坑内的局部深坑宜在浅部底板施工完',
        basis='5.2.11 基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露，邻近城市轨道交通结构侧的底板混凝土宜延伸至围护结构边。基坑内的局部深坑宜在浅部底板施工完成后开挖。',
        requirements=['基坑开挖至基底设计高程时，应及时施做垫层和结构底板，严禁基坑长时间暴露，邻近城市轨道交通结构侧的底板混凝土宜延伸至围护结构边。基坑内的局部深坑宜在浅部底板施工完成后开挖。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_12_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_12',
 'clause': '5.2.12',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '临近城市轨道交通结构侧的基坑围护结构宜与地下室结构侧墙密贴，且地下室结构宜按一级防水要求设计。',
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
 'requirements': ['临近城市轨道交通结构侧的基坑围护结构宜与地下室结构侧墙密贴，且地下室结构宜按一级防水要求设计。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_12(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.12 临近城市轨道交通结构侧的基坑围护结构宜与地下室结构侧墙密贴，且地下室结构宜按一级防水要求设计。."""

    return _evaluate_clause(
        clause='5.2.12',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='临近城市轨道交通结构侧的基坑围护结构宜与地下室结构侧墙密贴，且地下室结构宜按一级防水要求设计。',
        basis='5.2.12 临近城市轨道交通结构侧的基坑围护结构宜与地下室结构侧墙密贴，且地下室结构宜按一级防水要求设计。',
        requirements=['临近城市轨道交通结构侧的基坑围护结构宜与地下室结构侧墙密贴，且地下室结构宜按一级防水要求设计。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_13_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_13',
 'clause': '5.2.13',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '临近城市轨道交通结构侧的基坑围护结构与地下室结构之间存在空隙时，宜采用素混凝土回填密实，不得采用杂填土、建筑垃圾等性质较差或不稳定的材料。当空隙较大且回填素混凝',
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
 'requirements': ['临近城市轨道交通结构侧的基坑围护结构与地下室结构之间存在空隙时，宜采用素混凝土回填密实，不得采用杂填土、建筑垃圾等性质较差或不稳定的材料。当空隙较大且回填素混凝土不经济时，可在地下室各层楼板标高处浇筑不小于 '
                  '$600\\mathrm{mm}$ 厚的混凝土或不小于 $400\\mathrm{mm}$ 厚的钢筋混凝土支撑板带。'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_13(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.13 临近城市轨道交通结构侧的基坑围护结构与地下室结构之间存在空隙时，宜采用素混凝土回填密实，不得采用杂填土、建筑垃圾等性质较差或不稳定的材料。当空隙较大且回填素混凝."""

    return _evaluate_clause(
        clause='5.2.13',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='临近城市轨道交通结构侧的基坑围护结构与地下室结构之间存在空隙时，宜采用素混凝土回填密实，不得采用杂填土、建筑垃圾等性质较差或不稳定的材料。当空隙较大且回填素混凝',
        basis='5.2.13 临近城市轨道交通结构侧的基坑围护结构与地下室结构之间存在空隙时，宜采用素混凝土回填密实，不得采用杂填土、建筑垃圾等性质较差或不稳定的材料。当空隙较大且回填素混凝土不经济时，可在地下室各层楼板标高处浇筑不小于 $600\\mathrm{mm}$ 厚的混凝土或不小于 $400\\mathrm{mm}$ 厚的钢筋混凝土支撑板带。',
        requirements=['临近城市轨道交通结构侧的基坑围护结构与地下室结构之间存在空隙时，宜采用素混凝土回填密实，不得采用杂填土、建筑垃圾等性质较差或不稳定的材料。当空隙较大且回填素混凝土不经济时，可在地下室各层楼板标高处浇筑不小于 $600\\mathrm{mm}$ 厚的混凝土或不小于 $400\\mathrm{mm}$ 厚的钢筋混凝土支撑板带。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_2_14_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_2_14',
 'clause': '5.2.14',
 'chapter': '外部作业控制',
 'section': '5.2 基坑工程',
 'title': '临近城市轨道交通结构侧的基坑支撑拆除及换撑应采取安全可靠的作业方案，并应采用影响较小的支撑拆除方式。',
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
 'requirements': ['临近城市轨道交通结构侧的基坑支撑拆除及换撑应采取安全可靠的作业方案，并应采用影响较小的支撑拆除方式。 # 5.3 隧道工程'],
 'output': OUTPUT_SCHEMA}


def clause_5_2_14(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.2.14 临近城市轨道交通结构侧的基坑支撑拆除及换撑应采取安全可靠的作业方案，并应采用影响较小的支撑拆除方式。."""

    return _evaluate_clause(
        clause='5.2.14',
        chapter='外部作业控制',
        section='5.2 基坑工程',
        title='临近城市轨道交通结构侧的基坑支撑拆除及换撑应采取安全可靠的作业方案，并应采用影响较小的支撑拆除方式。',
        basis='5.2.14 临近城市轨道交通结构侧的基坑支撑拆除及换撑应采取安全可靠的作业方案，并应采用影响较小的支撑拆除方式。 # 5.3 隧道工程',
        requirements=['临近城市轨道交通结构侧的基坑支撑拆除及换撑应采取安全可靠的作业方案，并应采用影响较小的支撑拆除方式。 # 5.3 隧道工程'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_1',
 'clause': '5.3.1',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '新建隧道上穿、下穿或侧穿城市轨道交通结构时，应综合考虑工程地质与水文地质条件、穿越净距、场地环境等因素选用合理的工法，并应优先选用施工扰动较小的盾构法、顶管法等',
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
 'requirements': ['新建隧道上穿、下穿或侧穿城市轨道交通结构时，应综合考虑工程地质与水文地质条件、穿越净距、场地环境等因素选用合理的工法，并应优先选用施工扰动较小的盾构法、顶管法等非开挖工法。'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.1 新建隧道上穿、下穿或侧穿城市轨道交通结构时，应综合考虑工程地质与水文地质条件、穿越净距、场地环境等因素选用合理的工法，并应优先选用施工扰动较小的盾构法、顶管法等."""

    return _evaluate_clause(
        clause='5.3.1',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='新建隧道上穿、下穿或侧穿城市轨道交通结构时，应综合考虑工程地质与水文地质条件、穿越净距、场地环境等因素选用合理的工法，并应优先选用施工扰动较小的盾构法、顶管法等',
        basis='5.3.1 新建隧道上穿、下穿或侧穿城市轨道交通结构时，应综合考虑工程地质与水文地质条件、穿越净距、场地环境等因素选用合理的工法，并应优先选用施工扰动较小的盾构法、顶管法等非开挖工法。',
        requirements=['新建隧道上穿、下穿或侧穿城市轨道交通结构时，应综合考虑工程地质与水文地质条件、穿越净距、场地环境等因素选用合理的工法，并应优先选用施工扰动较小的盾构法、顶管法等非开挖工法。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_2',
 'clause': '5.3.2',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '新建隧道与城市轨道交通结构交叉时，线路宜设计为直线，并优先以大角度从结构上方穿越；从结构下方穿越时应符',
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
 'requirements': ['新建隧道与城市轨道交通结构交叉时，线路宜设计为直线，并优先以大角度从结构上方穿越；从结构下方穿越时应符 合表3.3.1和第3.3.4条的相关规定，并应避开变形缝、结构开洞等薄弱位置。'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.2 新建隧道与城市轨道交通结构交叉时，线路宜设计为直线，并优先以大角度从结构上方穿越；从结构下方穿越时应符."""

    return _evaluate_clause(
        clause='5.3.2',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='新建隧道与城市轨道交通结构交叉时，线路宜设计为直线，并优先以大角度从结构上方穿越；从结构下方穿越时应符',
        basis='5.3.2 新建隧道与城市轨道交通结构交叉时，线路宜设计为直线，并优先以大角度从结构上方穿越；从结构下方穿越时应符 合表3.3.1和第3.3.4条的相关规定，并应避开变形缝、结构开洞等薄弱位置。',
        requirements=['新建隧道与城市轨道交通结构交叉时，线路宜设计为直线，并优先以大角度从结构上方穿越；从结构下方穿越时应符 合表3.3.1和第3.3.4条的相关规定，并应避开变形缝、结构开洞等薄弱位置。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_3',
 'clause': '5.3.3',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '新建隧道施工前，应对城市轨道交通结构进行变形和受力验算，制定抗隆起、抗沉降专项方案和应急预案。当不满足控制指标时，应采取地层预加固、隧道刚度增强等措施，以降低穿',
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
 'requirements': ['新建隧道施工前，应对城市轨道交通结构进行变形和受力验算，制定抗隆起、抗沉降专项方案和应急预案。当不满足控制指标时，应采取地层预加固、隧道刚度增强等措施，以降低穿越施工对既有结构的影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.3 新建隧道施工前，应对城市轨道交通结构进行变形和受力验算，制定抗隆起、抗沉降专项方案和应急预案。当不满足控制指标时，应采取地层预加固、隧道刚度增强等措施，以降低穿."""

    return _evaluate_clause(
        clause='5.3.3',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='新建隧道施工前，应对城市轨道交通结构进行变形和受力验算，制定抗隆起、抗沉降专项方案和应急预案。当不满足控制指标时，应采取地层预加固、隧道刚度增强等措施，以降低穿',
        basis='5.3.3 新建隧道施工前，应对城市轨道交通结构进行变形和受力验算，制定抗隆起、抗沉降专项方案和应急预案。当不满足控制指标时，应采取地层预加固、隧道刚度增强等措施，以降低穿越施工对既有结构的影响。',
        requirements=['新建隧道施工前，应对城市轨道交通结构进行变形和受力验算，制定抗隆起、抗沉降专项方案和应急预案。当不满足控制指标时，应采取地层预加固、隧道刚度增强等措施，以降低穿越施工对既有结构的影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_4',
 'clause': '5.3.4',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '新建隧道采用盾构法、顶管法等非开挖工法施工时，应符合以下规定：',
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
 'requirements': ['穿越施工前设置试验段，根据试验结果优化并确定施工参数。',
                  '在结构交叉段宜设置特殊管片并增加预留注浆孔数量，遵循微扰动掘进原则，减小穿越影响。',
                  '不得在穿越影响区内进行换刀、停机和姿态大幅度调整等作业。',
                  '实施高精度自动化监测。'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.4 新建隧道采用盾构法、顶管法等非开挖工法施工时，应符合以下规定：."""

    return _evaluate_clause(
        clause='5.3.4',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='新建隧道采用盾构法、顶管法等非开挖工法施工时，应符合以下规定：',
        basis='5.3.4 新建隧道采用盾构法、顶管法等非开挖工法施工时，应符合以下规定： 1 穿越施工前设置试验段，根据试验结果优化并确定施工参数。 2 在结构交叉段宜设置特殊管片并增加预留注浆孔数量，遵循微扰动掘进原则，减小穿越影响。 3 不得在穿越影响区内进行换刀、停机和姿态大幅度调整等作业。 4 实施高精度自动化监测。',
        requirements=['穿越施工前设置试验段，根据试验结果优化并确定施工参数。', '在结构交叉段宜设置特殊管片并增加预留注浆孔数量，遵循微扰动掘进原则，减小穿越影响。', '不得在穿越影响区内进行换刀、停机和姿态大幅度调整等作业。', '实施高精度自动化监测。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_5',
 'clause': '5.3.5',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '新建隧道穿越施工时不宜进行降水作业，如需降水应进行专项论证。',
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
 'requirements': ['新建隧道穿越施工时不宜进行降水作业，如需降水应进行专项论证。'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.5 新建隧道穿越施工时不宜进行降水作业，如需降水应进行专项论证。."""

    return _evaluate_clause(
        clause='5.3.5',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='新建隧道穿越施工时不宜进行降水作业，如需降水应进行专项论证。',
        basis='5.3.5 新建隧道穿越施工时不宜进行降水作业，如需降水应进行专项论证。',
        requirements=['新建隧道穿越施工时不宜进行降水作业，如需降水应进行专项论证。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_6',
 'clause': '5.3.6',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '新建隧道为有水、有压管道时，应加强接头渗漏和腐蚀防护，防止结构渗漏对轨道交通结构造成不利影响。',
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
 'requirements': ['新建隧道为有水、有压管道时，应加强接头渗漏和腐蚀防护，防止结构渗漏对轨道交通结构造成不利影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.6 新建隧道为有水、有压管道时，应加强接头渗漏和腐蚀防护，防止结构渗漏对轨道交通结构造成不利影响。."""

    return _evaluate_clause(
        clause='5.3.6',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='新建隧道为有水、有压管道时，应加强接头渗漏和腐蚀防护，防止结构渗漏对轨道交通结构造成不利影响。',
        basis='5.3.6 新建隧道为有水、有压管道时，应加强接头渗漏和腐蚀防护，防止结构渗漏对轨道交通结构造成不利影响。',
        requirements=['新建隧道为有水、有压管道时，应加强接头渗漏和腐蚀防护，防止结构渗漏对轨道交通结构造成不利影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_3_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_3_7',
 'clause': '5.3.7',
 'chapter': '外部作业控制',
 'section': '5.3 隧道工程',
 'title': '软弱地层中盾构法或顶管法隧道近距离侧穿城市轨道交通结构时，宜采取设置隔离桩、地层加固等措施，加固措施应选用扰动较小的施工工法。',
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
 'requirements': ['软弱地层中盾构法或顶管法隧道近距离侧穿城市轨道交通结构时，宜采取设置隔离桩、地层加固等措施，加固措施应选用扰动较小的施工工法。 # 5.4 基础工程'],
 'output': OUTPUT_SCHEMA}


def clause_5_3_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.3.7 软弱地层中盾构法或顶管法隧道近距离侧穿城市轨道交通结构时，宜采取设置隔离桩、地层加固等措施，加固措施应选用扰动较小的施工工法。."""

    return _evaluate_clause(
        clause='5.3.7',
        chapter='外部作业控制',
        section='5.3 隧道工程',
        title='软弱地层中盾构法或顶管法隧道近距离侧穿城市轨道交通结构时，宜采取设置隔离桩、地层加固等措施，加固措施应选用扰动较小的施工工法。',
        basis='5.3.7 软弱地层中盾构法或顶管法隧道近距离侧穿城市轨道交通结构时，宜采取设置隔离桩、地层加固等措施，加固措施应选用扰动较小的施工工法。 # 5.4 基础工程',
        requirements=['软弱地层中盾构法或顶管法隧道近距离侧穿城市轨道交通结构时，宜采取设置隔离桩、地层加固等措施，加固措施应选用扰动较小的施工工法。 # 5.4 基础工程'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_1',
 'clause': '5.4.1',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '浅基础作业在城市轨道交通结构上产生的附加荷载与其他附加荷载叠加后不宜超过 $20\\mathrm{kPa}$ 。',
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
 'requirements': ['浅基础作业在城市轨道交通结构上产生的附加荷载与其他附加荷载叠加后不宜超过 $20\\mathrm{kPa}$ 。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.1 浅基础作业在城市轨道交通结构上产生的附加荷载与其他附加荷载叠加后不宜超过 $20\\mathrm{kPa}$ 。."""

    return _evaluate_clause(
        clause='5.4.1',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='浅基础作业在城市轨道交通结构上产生的附加荷载与其他附加荷载叠加后不宜超过 $20\\mathrm{kPa}$ 。',
        basis='5.4.1 浅基础作业在城市轨道交通结构上产生的附加荷载与其他附加荷载叠加后不宜超过 $20\\mathrm{kPa}$ 。',
        requirements=['浅基础作业在城市轨道交通结构上产生的附加荷载与其他附加荷载叠加后不宜超过 $20\\mathrm{kPa}$ 。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_2',
 'clause': '5.4.2',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '地基处理作业应采用对环境影响小、施工质量好的施工工艺，不宜采用预压、强夯、挤（振、冲）等对环境影响较大的作业方式，并应预先在城市轨道交通结构安全影响范围外进行试',
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
 'requirements': ['地基处理作业应采用对环境影响小、施工质量好的施工工艺，不宜采用预压、强夯、挤（振、冲）等对环境影响较大的作业方式，并应预先在城市轨道交通结构安全影响范围外进行试验施工，以确定施工工艺和参数。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.2 地基处理作业应采用对环境影响小、施工质量好的施工工艺，不宜采用预压、强夯、挤（振、冲）等对环境影响较大的作业方式，并应预先在城市轨道交通结构安全影响范围外进行试."""

    return _evaluate_clause(
        clause='5.4.2',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='地基处理作业应采用对环境影响小、施工质量好的施工工艺，不宜采用预压、强夯、挤（振、冲）等对环境影响较大的作业方式，并应预先在城市轨道交通结构安全影响范围外进行试',
        basis='5.4.2 地基处理作业应采用对环境影响小、施工质量好的施工工艺，不宜采用预压、强夯、挤（振、冲）等对环境影响较大的作业方式，并应预先在城市轨道交通结构安全影响范围外进行试验施工，以确定施工工艺和参数。',
        requirements=['地基处理作业应采用对环境影响小、施工质量好的施工工艺，不宜采用预压、强夯、挤（振、冲）等对环境影响较大的作业方式，并应预先在城市轨道交通结构安全影响范围外进行试验施工，以确定施工工艺和参数。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_3',
 'clause': '5.4.3',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '桩基作业应综合考虑下列因素对城市轨道交通结构的不利影响：',
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
 'requirements': ['桩基的成孔质量。', '不同桩型及成桩工艺的振动效应、挤土效应。', '上部结构通过桩基传递至土层中的附加应力。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.3 桩基作业应综合考虑下列因素对城市轨道交通结构的不利影响：."""

    return _evaluate_clause(
        clause='5.4.3',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='桩基作业应综合考虑下列因素对城市轨道交通结构的不利影响：',
        basis='5.4.3 桩基作业应综合考虑下列因素对城市轨道交通结构的不利影响： 1 桩基的成孔质量。 2 不同桩型及成桩工艺的振动效应、挤土效应。 3 上部结构通过桩基传递至土层中的附加应力。',
        requirements=['桩基的成孔质量。', '不同桩型及成桩工艺的振动效应、挤土效应。', '上部结构通过桩基传递至土层中的附加应力。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_4',
 'clause': '5.4.4',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '对距离城市轨道交通隧道 $2D$ （ $D$ 为隧道外径或宽度）范围内的非嵌岩桩，其桩底深度宜超过隧道底部0.5D（影响等级为一级及以上时取1.0D），并不小于',
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
 'requirements': ['对距离城市轨道交通隧道 $2D$ （ $D$ 为隧道外径或宽度）范围内的非嵌岩桩，其桩底深度宜超过隧道底部0.5D（影响等级为一级及以上时取1.0D），并不小于3m。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.4 对距离城市轨道交通隧道 $2D$ （ $D$ 为隧道外径或宽度）范围内的非嵌岩桩，其桩底深度宜超过隧道底部0.5D（影响等级为一级及以上时取1.0D），并不小于."""

    return _evaluate_clause(
        clause='5.4.4',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='对距离城市轨道交通隧道 $2D$ （ $D$ 为隧道外径或宽度）范围内的非嵌岩桩，其桩底深度宜超过隧道底部0.5D（影响等级为一级及以上时取1.0D），并不小于',
        basis='5.4.4 对距离城市轨道交通隧道 $2D$ （ $D$ 为隧道外径或宽度）范围内的非嵌岩桩，其桩底深度宜超过隧道底部0.5D（影响等级为一级及以上时取1.0D），并不小于3m。',
        requirements=['对距离城市轨道交通隧道 $2D$ （ $D$ 为隧道外径或宽度）范围内的非嵌岩桩，其桩底深度宜超过隧道底部0.5D（影响等级为一级及以上时取1.0D），并不小于3m。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_5',
 'clause': '5.4.5',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '桩基作业应优先选用对施工影响小的非挤土桩。当采用挤土或半挤土桩时，应评估挤土效应对城市轨道交通结构的影响，并采取预钻孔、设置防挤沟或隔离墙等措施。',
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
 'requirements': ['桩基作业应优先选用对施工影响小的非挤土桩。当采用挤土或半挤土桩时，应评估挤土效应对城市轨道交通结构的影响，并采取预钻孔、设置防挤沟或隔离墙等措施。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.5 桩基作业应优先选用对施工影响小的非挤土桩。当采用挤土或半挤土桩时，应评估挤土效应对城市轨道交通结构的影响，并采取预钻孔、设置防挤沟或隔离墙等措施。."""

    return _evaluate_clause(
        clause='5.4.5',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='桩基作业应优先选用对施工影响小的非挤土桩。当采用挤土或半挤土桩时，应评估挤土效应对城市轨道交通结构的影响，并采取预钻孔、设置防挤沟或隔离墙等措施。',
        basis='5.4.5 桩基作业应优先选用对施工影响小的非挤土桩。当采用挤土或半挤土桩时，应评估挤土效应对城市轨道交通结构的影响，并采取预钻孔、设置防挤沟或隔离墙等措施。',
        requirements=['桩基作业应优先选用对施工影响小的非挤土桩。当采用挤土或半挤土桩时，应评估挤土效应对城市轨道交通结构的影响，并采取预钻孔、设置防挤沟或隔离墙等措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_6',
 'clause': '5.4.6',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '钻孔桩距离城市轨道交通结构较近时，可采取减少桩径、提高泥浆护壁质量、间隔跳开施工等措施提高成桩质量，减少孔壁坍塌等不利影响；有特殊要求时，应采取减少施工影响的措',
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
 'requirements': ['钻孔桩距离城市轨道交通结构较近时，可采取减少桩径、提高泥浆护壁质量、间隔跳开施工等措施提高成桩质量，减少孔壁坍塌等不利影响；有特殊要求时，应采取减少施工影响的措施，如套筒护壁或加固土体等。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.6 钻孔桩距离城市轨道交通结构较近时，可采取减少桩径、提高泥浆护壁质量、间隔跳开施工等措施提高成桩质量，减少孔壁坍塌等不利影响；有特殊要求时，应采取减少施工影响的措."""

    return _evaluate_clause(
        clause='5.4.6',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='钻孔桩距离城市轨道交通结构较近时，可采取减少桩径、提高泥浆护壁质量、间隔跳开施工等措施提高成桩质量，减少孔壁坍塌等不利影响；有特殊要求时，应采取减少施工影响的措',
        basis='5.4.6 钻孔桩距离城市轨道交通结构较近时，可采取减少桩径、提高泥浆护壁质量、间隔跳开施工等措施提高成桩质量，减少孔壁坍塌等不利影响；有特殊要求时，应采取减少施工影响的措施，如套筒护壁或加固土体等。',
        requirements=['钻孔桩距离城市轨道交通结构较近时，可采取减少桩径、提高泥浆护壁质量、间隔跳开施工等措施提高成桩质量，减少孔壁坍塌等不利影响；有特殊要求时，应采取减少施工影响的措施，如套筒护壁或加固土体等。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_7',
 'clause': '5.4.7',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '采用套筒施工时，套筒回旋下压、成孔与成桩等应连续进行，同时应结合地层条件，确定套筒壁厚、分节长度。',
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
 'requirements': ['采用套筒施工时，套筒回旋下压、成孔与成桩等应连续进行，同时应结合地层条件，确定套筒壁厚、分节长度。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.7 采用套筒施工时，套筒回旋下压、成孔与成桩等应连续进行，同时应结合地层条件，确定套筒壁厚、分节长度。."""

    return _evaluate_clause(
        clause='5.4.7',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='采用套筒施工时，套筒回旋下压、成孔与成桩等应连续进行，同时应结合地层条件，确定套筒壁厚、分节长度。',
        basis='5.4.7 采用套筒施工时，套筒回旋下压、成孔与成桩等应连续进行，同时应结合地层条件，确定套筒壁厚、分节长度。',
        requirements=['采用套筒施工时，套筒回旋下压、成孔与成桩等应连续进行，同时应结合地层条件，确定套筒壁厚、分节长度。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_4_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_4_8',
 'clause': '5.4.8',
 'chapter': '外部作业控制',
 'section': '5.4 基础工程',
 'title': '桩基施工前应进行试桩确定施工工艺，试桩数量不宜小于3根；成桩施工顺序应遵循“先近后远、跳桩施工”的原则，并符合下列规定：',
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
 'requirements': ['对垂直于既有结构轴线的横向排桩，应遵循“先近后远”的实施原则。', '对平行于既有结构轴线的纵向排桩，宜遵循“先中间后两端”的实施原则。', '对沿既有结构轴线两侧的桩基，宜对称实施。'],
 'output': OUTPUT_SCHEMA}


def clause_5_4_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.4.8 桩基施工前应进行试桩确定施工工艺，试桩数量不宜小于3根；成桩施工顺序应遵循“先近后远、跳桩施工”的原则，并符合下列规定：."""

    return _evaluate_clause(
        clause='5.4.8',
        chapter='外部作业控制',
        section='5.4 基础工程',
        title='桩基施工前应进行试桩确定施工工艺，试桩数量不宜小于3根；成桩施工顺序应遵循“先近后远、跳桩施工”的原则，并符合下列规定：',
        basis='5.4.8 桩基施工前应进行试桩确定施工工艺，试桩数量不宜小于3根；成桩施工顺序应遵循“先近后远、跳桩施工”的原则，并符合下列规定： 1 对垂直于既有结构轴线的横向排桩，应遵循“先近后远”的实施原则。 2 对平行于既有结构轴线的纵向排桩，宜遵循“先中间后两端”的实施原则。 3 对沿既有结构轴线两侧的桩基，宜对称实施。 4 控制挤土桩的沉桩速率，单日沉桩数量不宜过多，并根据监测情况及时调整。 # 5.5 降水工程',
        requirements=['对垂直于既有结构轴线的横向排桩，应遵循“先近后远”的实施原则。', '对平行于既有结构轴线的纵向排桩，宜遵循“先中间后两端”的实施原则。', '对沿既有结构轴线两侧的桩基，宜对称实施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_5_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_5_1',
 'clause': '5.5.1',
 'chapter': '外部作业控制',
 'section': '5.5 降水工程',
 'title': '城市轨道交通控制保护区内的降水工程，应采取措施避免降水作业期间的流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及',
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
 'requirements': ['城市轨道交通控制保护区内的降水工程，应采取措施避免降水作业期间的流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及降水施工影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_5_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.5.1 城市轨道交通控制保护区内的降水工程，应采取措施避免降水作业期间的流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及."""

    return _evaluate_clause(
        clause='5.5.1',
        chapter='外部作业控制',
        section='5.5 降水工程',
        title='城市轨道交通控制保护区内的降水工程，应采取措施避免降水作业期间的流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及',
        basis='5.5.1 城市轨道交通控制保护区内的降水工程，应采取措施避免降水作业期间的流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及降水施工影响。',
        requirements=['城市轨道交通控制保护区内的降水工程，应采取措施避免降水作业期间的流砂、管涌、坑底突涌及降水引起的地层较大沉降等破坏，编制合理的降水方案，预估承压水水位降低情况及降水施工影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_5_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_5_2',
 'clause': '5.5.2',
 'chapter': '外部作业控制',
 'section': '5.5 降水工程',
 'title': '当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。',
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
 'requirements': ['当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。'],
 'output': OUTPUT_SCHEMA}


def clause_5_5_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.5.2 当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。."""

    return _evaluate_clause(
        clause='5.5.2',
        chapter='外部作业控制',
        section='5.5 降水工程',
        title='当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。',
        basis='5.5.2 当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。',
        requirements=['当外部降水作业引起城市轨道交通结构周边地下水位变化时，应验算既有结构的受力安全。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_5_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_5_3',
 'clause': '5.5.3',
 'chapter': '外部作业控制',
 'section': '5.5 降水工程',
 'title': '城市轨道交通结构周边为深厚砂层、软土等特殊性地层时，宜采用合适的排水、降水、截水或回灌等地下水控制技术，以控制既有结构周边地层的水位变化幅度。',
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
 'requirements': ['城市轨道交通结构周边为深厚砂层、软土等特殊性地层时，宜采用合适的排水、降水、截水或回灌等地下水控制技术，以控制既有结构周边地层的水位变化幅度。'],
 'output': OUTPUT_SCHEMA}


def clause_5_5_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.5.3 城市轨道交通结构周边为深厚砂层、软土等特殊性地层时，宜采用合适的排水、降水、截水或回灌等地下水控制技术，以控制既有结构周边地层的水位变化幅度。."""

    return _evaluate_clause(
        clause='5.5.3',
        chapter='外部作业控制',
        section='5.5 降水工程',
        title='城市轨道交通结构周边为深厚砂层、软土等特殊性地层时，宜采用合适的排水、降水、截水或回灌等地下水控制技术，以控制既有结构周边地层的水位变化幅度。',
        basis='5.5.3 城市轨道交通结构周边为深厚砂层、软土等特殊性地层时，宜采用合适的排水、降水、截水或回灌等地下水控制技术，以控制既有结构周边地层的水位变化幅度。',
        requirements=['城市轨道交通结构周边为深厚砂层、软土等特殊性地层时，宜采用合适的排水、降水、截水或回灌等地下水控制技术，以控制既有结构周边地层的水位变化幅度。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_5_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_5_4',
 'clause': '5.5.4',
 'chapter': '外部作业控制',
 'section': '5.5 降水工程',
 'title': '降水对城市轨道交通结构会产生重大影响的外部作业宜采用封闭截水设计，并在作业前进行抽水试验，也可通过水下声呐等检测技术检测截水系统的隔水效果和质量。',
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
 'requirements': ['降水对城市轨道交通结构会产生重大影响的外部作业宜采用封闭截水设计，并在作业前进行抽水试验，也可通过水下声呐等检测技术检测截水系统的隔水效果和质量。'],
 'output': OUTPUT_SCHEMA}


def clause_5_5_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.5.4 降水对城市轨道交通结构会产生重大影响的外部作业宜采用封闭截水设计，并在作业前进行抽水试验，也可通过水下声呐等检测技术检测截水系统的隔水效果和质量。."""

    return _evaluate_clause(
        clause='5.5.4',
        chapter='外部作业控制',
        section='5.5 降水工程',
        title='降水对城市轨道交通结构会产生重大影响的外部作业宜采用封闭截水设计，并在作业前进行抽水试验，也可通过水下声呐等检测技术检测截水系统的隔水效果和质量。',
        basis='5.5.4 降水对城市轨道交通结构会产生重大影响的外部作业宜采用封闭截水设计，并在作业前进行抽水试验，也可通过水下声呐等检测技术检测截水系统的隔水效果和质量。',
        requirements=['降水对城市轨道交通结构会产生重大影响的外部作业宜采用封闭截水设计，并在作业前进行抽水试验，也可通过水下声呐等检测技术检测截水系统的隔水效果和质量。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_5_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_5_5',
 'clause': '5.5.5',
 'chapter': '外部作业控制',
 'section': '5.5 降水工程',
 'title': '强透水性地层中，若因客观条件难以形成封闭止水系统，可采取下列措施减少降水对城市轨道交通结构的影响：',
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
 'requirements': ['采用悬挂式竖向隔水帷幕和水平封底隔渗相结合的方案。', '按照近浅远深的原则布置降水系统。', '增大止水帷幕深度、设置坑外地下水回灌井。', '分区分坑按需降水。'],
 'output': OUTPUT_SCHEMA}


def clause_5_5_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.5.5 强透水性地层中，若因客观条件难以形成封闭止水系统，可采取下列措施减少降水对城市轨道交通结构的影响：."""

    return _evaluate_clause(
        clause='5.5.5',
        chapter='外部作业控制',
        section='5.5 降水工程',
        title='强透水性地层中，若因客观条件难以形成封闭止水系统，可采取下列措施减少降水对城市轨道交通结构的影响：',
        basis='5.5.5 强透水性地层中，若因客观条件难以形成封闭止水系统，可采取下列措施减少降水对城市轨道交通结构的影响： 1 采用悬挂式竖向隔水帷幕和水平封底隔渗相结合的方案。 2 按照近浅远深的原则布置降水系统。 3 增大止水帷幕深度、设置坑外地下水回灌井。 4 分区分坑按需降水。',
        requirements=['采用悬挂式竖向隔水帷幕和水平封底隔渗相结合的方案。', '按照近浅远深的原则布置降水系统。', '增大止水帷幕深度、设置坑外地下水回灌井。', '分区分坑按需降水。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_5_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_5_6',
 'clause': '5.5.6',
 'chapter': '外部作业控制',
 'section': '5.5 降水工程',
 'title': '当需要抽降承压水时，降水作业还应符合下列规定：',
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
 'requirements': ['坑内降压井的滤管底部宜高于止水帷幕底，其高差应根据水文地质条件和降水试验或地区经验综合确定。', '选择合适的滤网、滤料，并确保成孔和回填滤料的施工质量，防止抽水带走土层中的细颗粒。'],
 'output': OUTPUT_SCHEMA}


def clause_5_5_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.5.6 当需要抽降承压水时，降水作业还应符合下列规定：."""

    return _evaluate_clause(
        clause='5.5.6',
        chapter='外部作业控制',
        section='5.5 降水工程',
        title='当需要抽降承压水时，降水作业还应符合下列规定：',
        basis='5.5.6 当需要抽降承压水时，降水作业还应符合下列规定： 1 坑内降压井的滤管底部宜高于止水帷幕底，其高差应根据水文地质条件和降水试验或地区经验综合确定。 2 选择合适的滤网、滤料，并确保成孔和回填滤料的施工质量，防止抽水带走土层中的细颗粒。 3 根据现场抽水试验及渗流场计算结果，结合开挖工况，根据“按需降压”的原则确定降水方案。 # 5.6 其他工程',
        requirements=['坑内降压井的滤管底部宜高于止水帷幕底，其高差应根据水文地质条件和降水试验或地区经验综合确定。', '选择合适的滤网、滤料，并确保成孔和回填滤料的施工质量，防止抽水带走土层中的细颗粒。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_6_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_6_1',
 'clause': '5.6.1',
 'chapter': '外部作业控制',
 'section': '5.6 其他工程',
 'title': '道路与桥梁工程等外部作业应综合考虑堆载和卸载、施工荷载、道路使用期间的车辆荷载等对城市轨道交通结构安全的影响。',
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
 'requirements': ['道路与桥梁工程等外部作业应综合考虑堆载和卸载、施工荷载、道路使用期间的车辆荷载等对城市轨道交通结构安全的影响。'],
 'output': OUTPUT_SCHEMA}


def clause_5_6_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.6.1 道路与桥梁工程等外部作业应综合考虑堆载和卸载、施工荷载、道路使用期间的车辆荷载等对城市轨道交通结构安全的影响。."""

    return _evaluate_clause(
        clause='5.6.1',
        chapter='外部作业控制',
        section='5.6 其他工程',
        title='道路与桥梁工程等外部作业应综合考虑堆载和卸载、施工荷载、道路使用期间的车辆荷载等对城市轨道交通结构安全的影响。',
        basis='5.6.1 道路与桥梁工程等外部作业应综合考虑堆载和卸载、施工荷载、道路使用期间的车辆荷载等对城市轨道交通结构安全的影响。',
        requirements=['道路与桥梁工程等外部作业应综合考虑堆载和卸载、施工荷载、道路使用期间的车辆荷载等对城市轨道交通结构安全的影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_6_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_6_2',
 'clause': '5.6.2',
 'chapter': '外部作业控制',
 'section': '5.6 其他工程',
 'title': '城市轨道交通控制保护区内的地下管线工程应符合下列规定：',
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
 'requirements': ['采用顶管法施工时，应考虑工作井的基坑、进出洞加固措施、工作井后背墙的支承力对轨道交通结构的不利影响；穿越城市轨道交通施工区段宜采取跟踪注浆措施。',
                  '采用拖拉管施工时，应严格控制导向钻孔轴线，管线与回钻扩孔之间的空隙应注浆充填饱满。',
                  '管道接头部位应采取可靠的密封、刚度加强或土体加固等措施，防止接头渗漏引起的轨道交通结构周边水土流失。',
                  '采用钢管、铸铁等易腐蚀材料的管道，应结合轨道交通杂散电流的影响采取主动防护措施。'],
 'output': OUTPUT_SCHEMA}


def clause_5_6_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.6.2 城市轨道交通控制保护区内的地下管线工程应符合下列规定：."""

    return _evaluate_clause(
        clause='5.6.2',
        chapter='外部作业控制',
        section='5.6 其他工程',
        title='城市轨道交通控制保护区内的地下管线工程应符合下列规定：',
        basis='5.6.2 城市轨道交通控制保护区内的地下管线工程应符合下列规定： 1 采用顶管法施工时，应考虑工作井的基坑、进出洞加固措施、工作井后背墙的支承力对轨道交通结构的不利影响；穿越城市轨道交通施工区段宜采取跟踪注浆措施。 2 采用拖拉管施工时，应严格控制导向钻孔轴线，管线与回钻扩孔之间的空隙应注浆充填饱满。 3 采用明挖法施工时，应符合本规程第5.2节基坑工程的规定。 4输油、输气、供水等压力管道不应下穿轨道交通地下和地面结构。 5 管道接头部位应采取可靠的密封、刚度加强或土体加固等措施，防止接头渗漏引起的轨道交通结构周边水土流失。 6 采用钢管、铸铁等易腐蚀材料的管道，应结合轨道交通杂散电流的影响采取主动防护措施。',
        requirements=['采用顶管法施工时，应考虑工作井的基坑、进出洞加固措施、工作井后背墙的支承力对轨道交通结构的不利影响；穿越城市轨道交通施工区段宜采取跟踪注浆措施。', '采用拖拉管施工时，应严格控制导向钻孔轴线，管线与回钻扩孔之间的空隙应注浆充填饱满。', '管道接头部位应采取可靠的密封、刚度加强或土体加固等措施，防止接头渗漏引起的轨道交通结构周边水土流失。', '采用钢管、铸铁等易腐蚀材料的管道，应结合轨道交通杂散电流的影响采取主动防护措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_6_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_6_3',
 'clause': '5.6.3',
 'chapter': '外部作业控制',
 'section': '5.6 其他工程',
 'title': '城市轨道交通控制保护区内的爆破作业应符合下列规定：',
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
 'requirements': ['应采取控制爆破作业，不得进行硐室爆破、深孔爆破等药量较大的爆破作业。'],
 'output': OUTPUT_SCHEMA}


def clause_5_6_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.6.3 城市轨道交通控制保护区内的爆破作业应符合下列规定：."""

    return _evaluate_clause(
        clause='5.6.3',
        chapter='外部作业控制',
        section='5.6 其他工程',
        title='城市轨道交通控制保护区内的爆破作业应符合下列规定：',
        basis='5.6.3 城市轨道交通控制保护区内的爆破作业应符合下列规定： 1 不应在轨道交通控制保护区内进行爆破作业。由于特殊情况需要爆破作业的，应进行爆破安全评估和爆破设计与施工 技术论证，并满足本规程第3.3.1条和现行国家标准《爆破安全规程》GB6722的规定。 2 爆破作业在轨道交通结构上产生的振动速度不应超过 $2.5\\mathrm{cm / s}$ ，有特殊要求或安装有精密设备时，振动速度应从严控制；爆破作业时间应选择在轨道交通非运营期间进行。 3 应采取控制爆破作业，不得进行硐室爆破、深孔爆破等药量较大的爆破作业。',
        requirements=['应采取控制爆破作业，不得进行硐室爆破、深孔爆破等药量较大的爆破作业。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_5_6_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_5_6_4',
 'clause': '5.6.4',
 'chapter': '外部作业控制',
 'section': '5.6 其他工程',
 'title': '城市轨道交通控制保护区内的其他作业，应符合下列规定：',
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
 'requirements': ['冻结法外部作业应采取措施降低地层冻胀、融沉对结构产生的不利影响。',
                  '河道整治等水利工程应综合考虑河道疏浚、堤防加固、蓄水等作业对轨道交通结构的不利影响。',
                  '建（构）筑物拆除时，应采取有效措施控制倒塌或坠落物体对轨道交通结构产生的冲击和振动影响。 #'],
 'output': OUTPUT_SCHEMA}


def clause_5_6_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """5.6.4 城市轨道交通控制保护区内的其他作业，应符合下列规定：."""

    return _evaluate_clause(
        clause='5.6.4',
        chapter='外部作业控制',
        section='5.6 其他工程',
        title='城市轨道交通控制保护区内的其他作业，应符合下列规定：',
        basis='5.6.4 城市轨道交通控制保护区内的其他作业，应符合下列规定： 1 冻结法外部作业应采取措施降低地层冻胀、融沉对结构产生的不利影响。 2 塔吊等起重吊装设备与轨道交通结构的净距应满足表3.3.1的要求，其作业半径不应覆盖轨道交通地面或高架结构，并与既有结构保持一定的安全距离，且应采取有效措施防止起重吊装设备倾倒。 3 钻探（孔）作业与轨道交通结构的净距应严格满足表3.3.1的要求，探孔完成后应采取有效封堵措施。 4 河道整治等水利工程应综合考虑河道疏浚、堤防加固、蓄水等作业对轨道交通结构的不利影响。 5 建（构）筑物拆除时，应采取有效措施控制倒塌或坠落物体对轨道交通结构产生的冲击和振动影响。 # 6 接口改造 # 6.1 一般规定',
        requirements=['冻结法外部作业应采取措施降低地层冻胀、融沉对结构产生的不利影响。', '河道整治等水利工程应综合考虑河道疏浚、堤防加固、蓄水等作业对轨道交通结构的不利影响。', '建（构）筑物拆除时，应采取有效措施控制倒塌或坠落物体对轨道交通结构产生的冲击和振动影响。 #'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_5_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_5_functions",
    "chapter": '外部作业控制',
    "description": "DB32/T 4351-2022 chapter 5 clause function API schema.",
    "functions": {
        "clause_5_1_1": CLAUSE_5_1_1_INPUT_SCHEMA,
        "clause_5_1_2": CLAUSE_5_1_2_INPUT_SCHEMA,
        "clause_5_1_3": CLAUSE_5_1_3_INPUT_SCHEMA,
        "clause_5_1_4": CLAUSE_5_1_4_INPUT_SCHEMA,
        "clause_5_1_5": CLAUSE_5_1_5_INPUT_SCHEMA,
        "clause_5_2_1": CLAUSE_5_2_1_INPUT_SCHEMA,
        "clause_5_2_2": CLAUSE_5_2_2_INPUT_SCHEMA,
        "clause_5_2_3": CLAUSE_5_2_3_INPUT_SCHEMA,
        "clause_5_2_4": CLAUSE_5_2_4_INPUT_SCHEMA,
        "clause_5_2_5": CLAUSE_5_2_5_INPUT_SCHEMA,
        "clause_5_2_6": CLAUSE_5_2_6_INPUT_SCHEMA,
        "clause_5_2_7": CLAUSE_5_2_7_INPUT_SCHEMA,
        "clause_5_2_8": CLAUSE_5_2_8_INPUT_SCHEMA,
        "clause_5_2_9": CLAUSE_5_2_9_INPUT_SCHEMA,
        "clause_5_2_10": CLAUSE_5_2_10_INPUT_SCHEMA,
        "clause_5_2_11": CLAUSE_5_2_11_INPUT_SCHEMA,
        "clause_5_2_12": CLAUSE_5_2_12_INPUT_SCHEMA,
        "clause_5_2_13": CLAUSE_5_2_13_INPUT_SCHEMA,
        "clause_5_2_14": CLAUSE_5_2_14_INPUT_SCHEMA,
        "clause_5_3_1": CLAUSE_5_3_1_INPUT_SCHEMA,
        "clause_5_3_2": CLAUSE_5_3_2_INPUT_SCHEMA,
        "clause_5_3_3": CLAUSE_5_3_3_INPUT_SCHEMA,
        "clause_5_3_4": CLAUSE_5_3_4_INPUT_SCHEMA,
        "clause_5_3_5": CLAUSE_5_3_5_INPUT_SCHEMA,
        "clause_5_3_6": CLAUSE_5_3_6_INPUT_SCHEMA,
        "clause_5_3_7": CLAUSE_5_3_7_INPUT_SCHEMA,
        "clause_5_4_1": CLAUSE_5_4_1_INPUT_SCHEMA,
        "clause_5_4_2": CLAUSE_5_4_2_INPUT_SCHEMA,
        "clause_5_4_3": CLAUSE_5_4_3_INPUT_SCHEMA,
        "clause_5_4_4": CLAUSE_5_4_4_INPUT_SCHEMA,
        "clause_5_4_5": CLAUSE_5_4_5_INPUT_SCHEMA,
        "clause_5_4_6": CLAUSE_5_4_6_INPUT_SCHEMA,
        "clause_5_4_7": CLAUSE_5_4_7_INPUT_SCHEMA,
        "clause_5_4_8": CLAUSE_5_4_8_INPUT_SCHEMA,
        "clause_5_5_1": CLAUSE_5_5_1_INPUT_SCHEMA,
        "clause_5_5_2": CLAUSE_5_5_2_INPUT_SCHEMA,
        "clause_5_5_3": CLAUSE_5_5_3_INPUT_SCHEMA,
        "clause_5_5_4": CLAUSE_5_5_4_INPUT_SCHEMA,
        "clause_5_5_5": CLAUSE_5_5_5_INPUT_SCHEMA,
        "clause_5_5_6": CLAUSE_5_5_6_INPUT_SCHEMA,
        "clause_5_6_1": CLAUSE_5_6_1_INPUT_SCHEMA,
        "clause_5_6_2": CLAUSE_5_6_2_INPUT_SCHEMA,
        "clause_5_6_3": CLAUSE_5_6_3_INPUT_SCHEMA,
        "clause_5_6_4": CLAUSE_5_6_4_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_5_1_1(confirmed_items=['在城市轨道交通控制保护区内进行外部作业前，应根据作业场地、工程地质和水文地质条件、轨道交通结构现状，确定既有结构的安全控制标准和外部作业工程的实施方案。'], strict=False)
    print(first.to_dict())
