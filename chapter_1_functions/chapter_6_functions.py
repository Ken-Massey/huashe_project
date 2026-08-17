"""Functions for Chapter 6 of DB32/T 4351-2022.

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

CLAUSE_6_1_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_1_1',
 'clause': '6.1.1',
 'chapter': '接口改造',
 'section': '6.1 一般规定',
 'title': '接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。',
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
 'requirements': ['接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。'],
 'output': OUTPUT_SCHEMA}


def clause_6_1_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.1.1 接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。."""

    return _evaluate_clause(
        clause='6.1.1',
        chapter='接口改造',
        section='6.1 一般规定',
        title='接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。',
        basis='6.1.1 接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。',
        requirements=['接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_1_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_1_2',
 'clause': '6.1.2',
 'chapter': '接口改造',
 'section': '6.1 一般规定',
 'title': '地下接口施工或改造作业对城市轨道交通结构的影响等级参照外部基坑作业执行，当未预留接口时，相应的影响等级应提高一级。',
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
 'requirements': ['地下接口施工或改造作业对城市轨道交通结构的影响等级参照外部基坑作业执行，当未预留接口时，相应的影响等级应提高一级。'],
 'output': OUTPUT_SCHEMA}


def clause_6_1_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.1.2 地下接口施工或改造作业对城市轨道交通结构的影响等级参照外部基坑作业执行，当未预留接口时，相应的影响等级应提高一级。."""

    return _evaluate_clause(
        clause='6.1.2',
        chapter='接口改造',
        section='6.1 一般规定',
        title='地下接口施工或改造作业对城市轨道交通结构的影响等级参照外部基坑作业执行，当未预留接口时，相应的影响等级应提高一级。',
        basis='6.1.2 地下接口施工或改造作业对城市轨道交通结构的影响等级参照外部基坑作业执行，当未预留接口时，相应的影响等级应提高一级。',
        requirements=['地下接口施工或改造作业对城市轨道交通结构的影响等级参照外部基坑作业执行，当未预留接口时，相应的影响等级应提高一级。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_1_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_1_3',
 'clause': '6.1.3',
 'chapter': '接口改造',
 'section': '6.1 一般规定',
 'title': '接口改造作业应符合国家、地方相关规范及技术标准的要求，应综合考虑改造作业需求和既有结构特点，除满足新建结构的自身安全外，还应保证既有结构、设施安全及线路运营安全',
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
 'requirements': ['接口改造作业应符合国家、地方相关规范及技术标准的要求，应综合考虑改造作业需求和既有结构特点，除满足新建结构的自身安全外，还应保证既有结构、设施安全及线路运营安全。 # 6.2 技术要求'],
 'output': OUTPUT_SCHEMA}


def clause_6_1_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.1.3 接口改造作业应符合国家、地方相关规范及技术标准的要求，应综合考虑改造作业需求和既有结构特点，除满足新建结构的自身安全外，还应保证既有结构、设施安全及线路运营安全."""

    return _evaluate_clause(
        clause='6.1.3',
        chapter='接口改造',
        section='6.1 一般规定',
        title='接口改造作业应符合国家、地方相关规范及技术标准的要求，应综合考虑改造作业需求和既有结构特点，除满足新建结构的自身安全外，还应保证既有结构、设施安全及线路运营安全',
        basis='6.1.3 接口改造作业应符合国家、地方相关规范及技术标准的要求，应综合考虑改造作业需求和既有结构特点，除满足新建结构的自身安全外，还应保证既有结构、设施安全及线路运营安全。 # 6.2 技术要求',
        requirements=['接口改造作业应符合国家、地方相关规范及技术标准的要求，应综合考虑改造作业需求和既有结构特点，除满足新建结构的自身安全外，还应保证既有结构、设施安全及线路运营安全。 # 6.2 技术要求'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_1',
 'clause': '6.2.1',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '接口改造作业前应查明场地环境、既有结构的设计及施工资料、结构使用情况及安全状态等，根据改造要求和目标，制定专项作业方案。存在重大影响的接口改造作业，应进行安全评',
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
 'requirements': ['接口改造作业前应查明场地环境、既有结构的设计及施工资料、结构使用情况及安全状态等，根据改造要求和目标，制定专项作业方案。存在重大影响的接口改造作业，应进行安全评估，并采取有效措施保证结构安全。'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.1 接口改造作业前应查明场地环境、既有结构的设计及施工资料、结构使用情况及安全状态等，根据改造要求和目标，制定专项作业方案。存在重大影响的接口改造作业，应进行安全评."""

    return _evaluate_clause(
        clause='6.2.1',
        chapter='接口改造',
        section='6.2 技术要求',
        title='接口改造作业前应查明场地环境、既有结构的设计及施工资料、结构使用情况及安全状态等，根据改造要求和目标，制定专项作业方案。存在重大影响的接口改造作业，应进行安全评',
        basis='6.2.1 接口改造作业前应查明场地环境、既有结构的设计及施工资料、结构使用情况及安全状态等，根据改造要求和目标，制定专项作业方案。存在重大影响的接口改造作业，应进行安全评估，并采取有效措施保证结构安全。',
        requirements=['接口改造作业前应查明场地环境、既有结构的设计及施工资料、结构使用情况及安全状态等，根据改造要求和目标，制定专项作业方案。存在重大影响的接口改造作业，应进行安全评估，并采取有效措施保证结构安全。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_2',
 'clause': '6.2.2',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '接口改造作业应明确改造内容和范围，考虑结构的整体性，按变形协调的原则进行设计，并与实施方案紧密结合，采取有效措施保证新建结构与既有结构的可靠连接。',
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
 'requirements': ['接口改造作业应明确改造内容和范围，考虑结构的整体性，按变形协调的原则进行设计，并与实施方案紧密结合，采取有效措施保证新建结构与既有结构的可靠连接。'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.2 接口改造作业应明确改造内容和范围，考虑结构的整体性，按变形协调的原则进行设计，并与实施方案紧密结合，采取有效措施保证新建结构与既有结构的可靠连接。."""

    return _evaluate_clause(
        clause='6.2.2',
        chapter='接口改造',
        section='6.2 技术要求',
        title='接口改造作业应明确改造内容和范围，考虑结构的整体性，按变形协调的原则进行设计，并与实施方案紧密结合，采取有效措施保证新建结构与既有结构的可靠连接。',
        basis='6.2.2 接口改造作业应明确改造内容和范围，考虑结构的整体性，按变形协调的原则进行设计，并与实施方案紧密结合，采取有效措施保证新建结构与既有结构的可靠连接。',
        requirements=['接口改造作业应明确改造内容和范围，考虑结构的整体性，按变形协调的原则进行设计，并与实施方案紧密结合，采取有效措施保证新建结构与既有结构的可靠连接。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_3',
 'clause': '6.2.3',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '既有结构的破除、改造和新建结构的基坑支护、开挖、降水等作业应尽量减少对既有结构的影响，避免造成结构构件',
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
 'requirements': ['既有结构的破除、改造和新建结构的基坑支护、开挖、降水等作业应尽量减少对既有结构的影响，避免造成结构构件 '
                  '损伤；当既有结构构件产生损伤时，应及时采取有效的加固措施，治理后构件应满足后续使用年限的要求。'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.3 既有结构的破除、改造和新建结构的基坑支护、开挖、降水等作业应尽量减少对既有结构的影响，避免造成结构构件."""

    return _evaluate_clause(
        clause='6.2.3',
        chapter='接口改造',
        section='6.2 技术要求',
        title='既有结构的破除、改造和新建结构的基坑支护、开挖、降水等作业应尽量减少对既有结构的影响，避免造成结构构件',
        basis='6.2.3 既有结构的破除、改造和新建结构的基坑支护、开挖、降水等作业应尽量减少对既有结构的影响，避免造成结构构件 损伤；当既有结构构件产生损伤时，应及时采取有效的加固措施，治理后构件应满足后续使用年限的要求。',
        requirements=['既有结构的破除、改造和新建结构的基坑支护、开挖、降水等作业应尽量减少对既有结构的影响，避免造成结构构件 损伤；当既有结构构件产生损伤时，应及时采取有效的加固措施，治理后构件应满足后续使用年限的要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_4',
 'clause': '6.2.4',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '改造中及改造后的既有结构和新建结构应分别进行施工和使用阶段的承载力计算、变形计算和稳定性验算。',
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
 'requirements': ['改造中及改造后的既有结构和新建结构应分别进行施工和使用阶段的承载力计算、变形计算和稳定性验算。'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.4 改造中及改造后的既有结构和新建结构应分别进行施工和使用阶段的承载力计算、变形计算和稳定性验算。."""

    return _evaluate_clause(
        clause='6.2.4',
        chapter='接口改造',
        section='6.2 技术要求',
        title='改造中及改造后的既有结构和新建结构应分别进行施工和使用阶段的承载力计算、变形计算和稳定性验算。',
        basis='6.2.4 改造中及改造后的既有结构和新建结构应分别进行施工和使用阶段的承载力计算、变形计算和稳定性验算。',
        requirements=['改造中及改造后的既有结构和新建结构应分别进行施工和使用阶段的承载力计算、变形计算和稳定性验算。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_5',
 'clause': '6.2.5',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '接口改造工程应采取安全可靠的防淹措施，以满足改造中及改造后工程的防洪和排水要求，并进行防洪防涝评估。对采用下沉式结构连接的接口工程，连接处地坪标高应低于相连城市',
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
 'requirements': ['接口改造工程应采取安全可靠的防淹措施，以满足改造中及改造后工程的防洪和排水要求，并进行防洪防涝评估。对采用下沉式结构连接的接口工程，连接处地坪标高应低于相连城市轨道交通结构的地坪标高，且外部排水系统应满足百年一遇的设防标准，采用双电源供电，严禁倒灌至车站。'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.5 接口改造工程应采取安全可靠的防淹措施，以满足改造中及改造后工程的防洪和排水要求，并进行防洪防涝评估。对采用下沉式结构连接的接口工程，连接处地坪标高应低于相连城市."""

    return _evaluate_clause(
        clause='6.2.5',
        chapter='接口改造',
        section='6.2 技术要求',
        title='接口改造工程应采取安全可靠的防淹措施，以满足改造中及改造后工程的防洪和排水要求，并进行防洪防涝评估。对采用下沉式结构连接的接口工程，连接处地坪标高应低于相连城市',
        basis='6.2.5 接口改造工程应采取安全可靠的防淹措施，以满足改造中及改造后工程的防洪和排水要求，并进行防洪防涝评估。对采用下沉式结构连接的接口工程，连接处地坪标高应低于相连城市轨道交通结构的地坪标高，且外部排水系统应满足百年一遇的设防标准，采用双电源供电，严禁倒灌至车站。',
        requirements=['接口改造工程应采取安全可靠的防淹措施，以满足改造中及改造后工程的防洪和排水要求，并进行防洪防涝评估。对采用下沉式结构连接的接口工程，连接处地坪标高应低于相连城市轨道交通结构的地坪标高，且外部排水系统应满足百年一遇的设防标准，采用双电源供电，严禁倒灌至车站。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_6',
 'clause': '6.2.6',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '改造后的接口应满足城市轨道交通结构的建筑功能需求，在新建结构与轨道交通结构之间宜视情况设置变形缝，并不得降低既有结构的使用年限、耐久性和安全性。',
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
 'requirements': ['改造后的接口应满足城市轨道交通结构的建筑功能需求，在新建结构与轨道交通结构之间宜视情况设置变形缝，并不得降低既有结构的使用年限、耐久性和安全性。'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.6 改造后的接口应满足城市轨道交通结构的建筑功能需求，在新建结构与轨道交通结构之间宜视情况设置变形缝，并不得降低既有结构的使用年限、耐久性和安全性。."""

    return _evaluate_clause(
        clause='6.2.6',
        chapter='接口改造',
        section='6.2 技术要求',
        title='改造后的接口应满足城市轨道交通结构的建筑功能需求，在新建结构与轨道交通结构之间宜视情况设置变形缝，并不得降低既有结构的使用年限、耐久性和安全性。',
        basis='6.2.6 改造后的接口应满足城市轨道交通结构的建筑功能需求，在新建结构与轨道交通结构之间宜视情况设置变形缝，并不得降低既有结构的使用年限、耐久性和安全性。',
        requirements=['改造后的接口应满足城市轨道交通结构的建筑功能需求，在新建结构与轨道交通结构之间宜视情况设置变形缝，并不得降低既有结构的使用年限、耐久性和安全性。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_2_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_2_7',
 'clause': '6.2.7',
 'chapter': '接口改造',
 'section': '6.2 技术要求',
 'title': '接口改造工程的防水等级和防水标准要求，不应低于城市轨道交通结构的相关标准，并应符合现行国家标准《地下工程防水技术规范》GB50108的规定。',
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
 'requirements': ['接口改造工程的防水等级和防水标准要求，不应低于城市轨道交通结构的相关标准，并应符合现行国家标准《地下工程防水技术规范》GB50108的规定。 # 6.3 实施要求'],
 'output': OUTPUT_SCHEMA}


def clause_6_2_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.2.7 接口改造工程的防水等级和防水标准要求，不应低于城市轨道交通结构的相关标准，并应符合现行国家标准《地下工程防水技术规范》GB50108的规定。."""

    return _evaluate_clause(
        clause='6.2.7',
        chapter='接口改造',
        section='6.2 技术要求',
        title='接口改造工程的防水等级和防水标准要求，不应低于城市轨道交通结构的相关标准，并应符合现行国家标准《地下工程防水技术规范》GB50108的规定。',
        basis='6.2.7 接口改造工程的防水等级和防水标准要求，不应低于城市轨道交通结构的相关标准，并应符合现行国家标准《地下工程防水技术规范》GB50108的规定。 # 6.3 实施要求',
        requirements=['接口改造工程的防水等级和防水标准要求，不应低于城市轨道交通结构的相关标准，并应符合现行国家标准《地下工程防水技术规范》GB50108的规定。 # 6.3 实施要求'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_1',
 'clause': '6.3.1',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '城市轨道交通结构的接口改造设计与施工，应具备以下资料：',
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
 'requirements': ['场地岩土工程勘察资料、既有结构及机电设备的设计图纸、既有结构施工记录及竣工图等资料，并应通过现场调查、测绘、物探或检测等手段进行补充。',
                  '既有结构使用现状的监测或鉴定资料，包括变形观测、裂缝观测、倾斜观测等数据。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.1 城市轨道交通结构的接口改造设计与施工，应具备以下资料：."""

    return _evaluate_clause(
        clause='6.3.1',
        chapter='接口改造',
        section='6.3 实施要求',
        title='城市轨道交通结构的接口改造设计与施工，应具备以下资料：',
        basis='6.3.1 城市轨道交通结构的接口改造设计与施工，应具备以下资料： 1 场地岩土工程勘察资料、既有结构及机电设备的设计图纸、既有结构施工记录及竣工图等资料，并应通过现场调查、测绘、物探或检测等手段进行补充。 2 既有结构使用现状的监测或鉴定资料，包括变形观测、裂缝观测、倾斜观测等数据。',
        requirements=['场地岩土工程勘察资料、既有结构及机电设备的设计图纸、既有结构施工记录及竣工图等资料，并应通过现场调查、测绘、物探或检测等手段进行补充。', '既有结构使用现状的监测或鉴定资料，包括变形观测、裂缝观测、倾斜观测等数据。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_2',
 'clause': '6.3.2',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '新建结构与既有结构的接口可采用柔性连接或刚性连接，并应满足以下要求：',
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
 'requirements': ['当采用柔性连接方式时，接口部位应设置变形缝，并采取相应的防水措施。',
                  '当采用刚性连接方式时，接口部位可采取地基加固、沉降调节桩等措施提高抗变形能力。',
                  '接口的防渗要求不低于与之相接的既有结构。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.2 新建结构与既有结构的接口可采用柔性连接或刚性连接，并应满足以下要求：."""

    return _evaluate_clause(
        clause='6.3.2',
        chapter='接口改造',
        section='6.3 实施要求',
        title='新建结构与既有结构的接口可采用柔性连接或刚性连接，并应满足以下要求：',
        basis='6.3.2 新建结构与既有结构的接口可采用柔性连接或刚性连接，并应满足以下要求： 1 当采用柔性连接方式时，接口部位应设置变形缝，并采取相应的防水措施。 2 当采用刚性连接方式时，接口部位可采取地基加固、沉降调节桩等措施提高抗变形能力。 3 接口的防渗要求不低于与之相接的既有结构。',
        requirements=['当采用柔性连接方式时，接口部位应设置变形缝，并采取相应的防水措施。', '当采用刚性连接方式时，接口部位可采取地基加固、沉降调节桩等措施提高抗变形能力。', '接口的防渗要求不低于与之相接的既有结构。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_3',
 'clause': '6.3.3',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '接口改造的基坑工程，应采取措施控制单边卸载对既有结构的影响。',
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
 'requirements': ['接口改造的基坑工程，应采取措施控制单边卸载对既有结构的影响。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.3 接口改造的基坑工程，应采取措施控制单边卸载对既有结构的影响。."""

    return _evaluate_clause(
        clause='6.3.3',
        chapter='接口改造',
        section='6.3 实施要求',
        title='接口改造的基坑工程，应采取措施控制单边卸载对既有结构的影响。',
        basis='6.3.3 接口改造的基坑工程，应采取措施控制单边卸载对既有结构的影响。',
        requirements=['接口改造的基坑工程，应采取措施控制单边卸载对既有结构的影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_4',
 'clause': '6.3.4',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '既有结构接口破除前，应对车站内现有设备、设施进行检查确认，拆除施工不得影响现有设备、设施的正常运行。',
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
 'requirements': ['既有结构接口破除前，应对车站内现有设备、设施进行检查确认，拆除施工不得影响现有设备、设施的正常运行。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.4 既有结构接口破除前，应对车站内现有设备、设施进行检查确认，拆除施工不得影响现有设备、设施的正常运行。."""

    return _evaluate_clause(
        clause='6.3.4',
        chapter='接口改造',
        section='6.3 实施要求',
        title='既有结构接口破除前，应对车站内现有设备、设施进行检查确认，拆除施工不得影响现有设备、设施的正常运行。',
        basis='6.3.4 既有结构接口破除前，应对车站内现有设备、设施进行检查确认，拆除施工不得影响现有设备、设施的正常运行。',
        requirements=['既有结构接口破除前，应对车站内现有设备、设施进行检查确认，拆除施工不得影响现有设备、设施的正常运行。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_5',
 'clause': '6.3.5',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '既有结构接口应采用静力切割的方式进行破除。未预留接口时，在距离保留结构 $300\\mathrm{mm}$ 范围内宜采用人工凿除方式，凿除范围内钢筋应保持完整性，',
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
 'requirements': ['既有结构接口应采用静力切割的方式进行破除。未预留接口时，在距离保留结构 $300\\mathrm{mm}$ 范围内宜采用人工凿除方式，凿除范围内钢筋应保持完整性，并应采取临时支撑、分块拆除等措施。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.5 既有结构接口应采用静力切割的方式进行破除。未预留接口时，在距离保留结构 $300\\mathrm{mm}$ 范围内宜采用人工凿除方式，凿除范围内钢筋应保持完整性，."""

    return _evaluate_clause(
        clause='6.3.5',
        chapter='接口改造',
        section='6.3 实施要求',
        title='既有结构接口应采用静力切割的方式进行破除。未预留接口时，在距离保留结构 $300\\mathrm{mm}$ 范围内宜采用人工凿除方式，凿除范围内钢筋应保持完整性，',
        basis='6.3.5 既有结构接口应采用静力切割的方式进行破除。未预留接口时，在距离保留结构 $300\\mathrm{mm}$ 范围内宜采用人工凿除方式，凿除范围内钢筋应保持完整性，并应采取临时支撑、分块拆除等措施。',
        requirements=['既有结构接口应采用静力切割的方式进行破除。未预留接口时，在距离保留结构 $300\\mathrm{mm}$ 范围内宜采用人工凿除方式，凿除范围内钢筋应保持完整性，并应采取临时支撑、分块拆除等措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_6',
 'clause': '6.3.6',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '新建结构应与既有结构直接连接，连接面应采用人工凿毛处理，凿毛后应清理干净，连接面宜涂刷界面剂，提高黏结强度。',
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
 'requirements': ['新建结构应与既有结构直接连接，连接面应采用人工凿毛处理，凿毛后应清理干净，连接面宜涂刷界面剂，提高黏结强度。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.6 新建结构应与既有结构直接连接，连接面应采用人工凿毛处理，凿毛后应清理干净，连接面宜涂刷界面剂，提高黏结强度。."""

    return _evaluate_clause(
        clause='6.3.6',
        chapter='接口改造',
        section='6.3 实施要求',
        title='新建结构应与既有结构直接连接，连接面应采用人工凿毛处理，凿毛后应清理干净，连接面宜涂刷界面剂，提高黏结强度。',
        basis='6.3.6 新建结构应与既有结构直接连接，连接面应采用人工凿毛处理，凿毛后应清理干净，连接面宜涂刷界面剂，提高黏结强度。',
        requirements=['新建结构应与既有结构直接连接，连接面应采用人工凿毛处理，凿毛后应清理干净，连接面宜涂刷界面剂，提高黏结强度。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_7',
 'clause': '6.3.7',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '当城市轨道交通结构未预留连接条件时，可采用植筋方式连接或凿出既有结构钢筋进行焊接。采用植筋时，植筋深度应满足设计要求；采用凿出既有结构钢筋进行焊接时，焊接长度应',
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
 'requirements': ['当城市轨道交通结构未预留连接条件时，可采用植筋方式连接或凿出既有结构钢筋进行焊接。采用植筋时，植筋深度应满足设计要求；采用凿出既有结构钢筋进行焊接时，焊接长度应符合规范要求。'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.7 当城市轨道交通结构未预留连接条件时，可采用植筋方式连接或凿出既有结构钢筋进行焊接。采用植筋时，植筋深度应满足设计要求；采用凿出既有结构钢筋进行焊接时，焊接长度应."""

    return _evaluate_clause(
        clause='6.3.7',
        chapter='接口改造',
        section='6.3 实施要求',
        title='当城市轨道交通结构未预留连接条件时，可采用植筋方式连接或凿出既有结构钢筋进行焊接。采用植筋时，植筋深度应满足设计要求；采用凿出既有结构钢筋进行焊接时，焊接长度应',
        basis='6.3.7 当城市轨道交通结构未预留连接条件时，可采用植筋方式连接或凿出既有结构钢筋进行焊接。采用植筋时，植筋深度应满足设计要求；采用凿出既有结构钢筋进行焊接时，焊接长度应符合规范要求。',
        requirements=['当城市轨道交通结构未预留连接条件时，可采用植筋方式连接或凿出既有结构钢筋进行焊接。采用植筋时，植筋深度应满足设计要求；采用凿出既有结构钢筋进行焊接时，焊接长度应符合规范要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_6_3_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_6_3_8',
 'clause': '6.3.8',
 'chapter': '接口改造',
 'section': '6.3 实施要求',
 'title': '接口改造作业应满足以下要求：',
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
 'requirements': ['细化组织设计，尽量缩短工期，以减小对城市轨道交通正常运营的影响。',
                  '采取临时防雨、防淹措施，确保雨水不倒灌至既有结构接口处，并做好施工期间运营车站内乘客的疏导及防护工作。',
                  '采取有效措施控制施工现场的各种粉尘、废气、废弃物、噪声、振动等对周围环境造成的污染和危害。 #'],
 'output': OUTPUT_SCHEMA}


def clause_6_3_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """6.3.8 接口改造作业应满足以下要求：."""

    return _evaluate_clause(
        clause='6.3.8',
        chapter='接口改造',
        section='6.3 实施要求',
        title='接口改造作业应满足以下要求：',
        basis='6.3.8 接口改造作业应满足以下要求： 1 细化组织设计，尽量缩短工期，以减小对城市轨道交通正常运营的影响。 2 采取临时防雨、防淹措施，确保雨水不倒灌至既有结构接口处，并做好施工期间运营车站内乘客的疏导及防护工作。 3 采取有效措施控制施工现场的各种粉尘、废气、废弃物、噪声、振动等对周围环境造成的污染和危害。 # 7 安全监测 # 7.1 一般规定',
        requirements=['细化组织设计，尽量缩短工期，以减小对城市轨道交通正常运营的影响。', '采取临时防雨、防淹措施，确保雨水不倒灌至既有结构接口处，并做好施工期间运营车站内乘客的疏导及防护工作。', '采取有效措施控制施工现场的各种粉尘、废气、废弃物、噪声、振动等对周围环境造成的污染和危害。 #'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_6_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_6_functions",
    "chapter": '接口改造',
    "description": "DB32/T 4351-2022 chapter 6 clause function API schema.",
    "functions": {
        "clause_6_1_1": CLAUSE_6_1_1_INPUT_SCHEMA,
        "clause_6_1_2": CLAUSE_6_1_2_INPUT_SCHEMA,
        "clause_6_1_3": CLAUSE_6_1_3_INPUT_SCHEMA,
        "clause_6_2_1": CLAUSE_6_2_1_INPUT_SCHEMA,
        "clause_6_2_2": CLAUSE_6_2_2_INPUT_SCHEMA,
        "clause_6_2_3": CLAUSE_6_2_3_INPUT_SCHEMA,
        "clause_6_2_4": CLAUSE_6_2_4_INPUT_SCHEMA,
        "clause_6_2_5": CLAUSE_6_2_5_INPUT_SCHEMA,
        "clause_6_2_6": CLAUSE_6_2_6_INPUT_SCHEMA,
        "clause_6_2_7": CLAUSE_6_2_7_INPUT_SCHEMA,
        "clause_6_3_1": CLAUSE_6_3_1_INPUT_SCHEMA,
        "clause_6_3_2": CLAUSE_6_3_2_INPUT_SCHEMA,
        "clause_6_3_3": CLAUSE_6_3_3_INPUT_SCHEMA,
        "clause_6_3_4": CLAUSE_6_3_4_INPUT_SCHEMA,
        "clause_6_3_5": CLAUSE_6_3_5_INPUT_SCHEMA,
        "clause_6_3_6": CLAUSE_6_3_6_INPUT_SCHEMA,
        "clause_6_3_7": CLAUSE_6_3_7_INPUT_SCHEMA,
        "clause_6_3_8": CLAUSE_6_3_8_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_6_1_1(confirmed_items=['接口改造作业应充分考虑其对已运营车站的影响，且应满足车站消防疏散、防洪、人防、安保、系统设备等的正常使用功能和安全要求。'], strict=False)
    print(first.to_dict())
