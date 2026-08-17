"""Functions for Chapter 2 of DB32/T 4351-2022.

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

CLAUSE_2_0_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_1',
 'clause': '2.0.1',
 'chapter': '术语',
 'section': '2 术语',
 'title': '城市轨道交通结构 urban rail transit structure',
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
 'requirements': ['城市轨道交通结构 urban rail transit structure '
                  '保障城市轨道交通列车安全运营和结构体系稳定的主要受力结构，指城市轨道交通结构本体，包括地面和高架结构、地下结构及相关附属结构。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.1 城市轨道交通结构 urban rail transit structure."""

    return _evaluate_clause(
        clause='2.0.1',
        chapter='术语',
        section='2 术语',
        title='城市轨道交通结构 urban rail transit structure',
        basis='# 2.0.1 城市轨道交通结构 urban rail transit structure 保障城市轨道交通列车安全运营和结构体系稳定的主要受力结构，指城市轨道交通结构本体，包括地面和高架结构、地下结构及相关附属结构。',
        requirements=['城市轨道交通结构 urban rail transit structure 保障城市轨道交通列车安全运营和结构体系稳定的主要受力结构，指城市轨道交通结构本体，包括地面和高架结构、地下结构及相关附属结构。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_2',
 'clause': '2.0.2',
 'chapter': '术语',
 'section': '2 术语',
 'title': '控制保护区 control and protection area',
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
 'requirements': ['控制保护区 control and protection area 为保证城市轨道交通结构的正常使用和安全，在其结构及周边的特定范围内设置的控制和保护区域。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.2 控制保护区 control and protection area."""

    return _evaluate_clause(
        clause='2.0.2',
        chapter='术语',
        section='2 术语',
        title='控制保护区 control and protection area',
        basis='# 2.0.2 控制保护区 control and protection area 为保证城市轨道交通结构的正常使用和安全，在其结构及周边的特定范围内设置的控制和保护区域。',
        requirements=['控制保护区 control and protection area 为保证城市轨道交通结构的正常使用和安全，在其结构及周边的特定范围内设置的控制和保护区域。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_3',
 'clause': '2.0.3',
 'chapter': '术语',
 'section': '2 术语',
 'title': '特别保护区 special control and protection area',
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
 'requirements': ['特别保护区 special control and protection area 在城市轨道交通结构的控制保护区内，紧邻结构的一定范围内设置的重点保护区域。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.3 特别保护区 special control and protection area."""

    return _evaluate_clause(
        clause='2.0.3',
        chapter='术语',
        section='2 术语',
        title='特别保护区 special control and protection area',
        basis='# 2.0.3 特别保护区 special control and protection area 在城市轨道交通结构的控制保护区内，紧邻结构的一定范围内设置的重点保护区域。',
        requirements=['特别保护区 special control and protection area 在城市轨道交通结构的控制保护区内，紧邻结构的一定范围内设置的重点保护区域。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_4',
 'clause': '2.0.4',
 'chapter': '术语',
 'section': '2 术语',
 'title': '外部作业 exterior action',
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
 'requirements': ['外部作业 exterior action '
                  '在城市轨道交通结构周边进行的可能对其产生影响的各类外部工程，主要包括基坑、隧道、基础、降水及其他工程等，其他工程主要有道路、绿化、管线和水利工程及冻结、起重、钻孔和爆破等作业。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.4 外部作业 exterior action."""

    return _evaluate_clause(
        clause='2.0.4',
        chapter='术语',
        section='2 术语',
        title='外部作业 exterior action',
        basis='# 2.0.4 外部作业 exterior action 在城市轨道交通结构周边进行的可能对其产生影响的各类外部工程，主要包括基坑、隧道、基础、降水及其他工程等，其他工程主要有道路、绿化、管线和水利工程及冻结、起重、钻孔和爆破等作业。',
        requirements=['外部作业 exterior action 在城市轨道交通结构周边进行的可能对其产生影响的各类外部工程，主要包括基坑、隧道、基础、降水及其他工程等，其他工程主要有道路、绿化、管线和水利工程及冻结、起重、钻孔和爆破等作业。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_5',
 'clause': '2.0.5',
 'chapter': '术语',
 'section': '2 术语',
 'title': '安全评估 safety assessment',
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
 'requirements': ['安全评估 safety assessment '
                  '根据外部作业的设计与施工方案、城市轨道交通现状调查情况及保护方案等，通过计算分析、工程类比或相关试验等手段，评估外部作业对城市轨道交通结构安全影响程度的工作。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.5 安全评估 safety assessment."""

    return _evaluate_clause(
        clause='2.0.5',
        chapter='术语',
        section='2 术语',
        title='安全评估 safety assessment',
        basis='# 2.0.5 安全评估 safety assessment 根据外部作业的设计与施工方案、城市轨道交通现状调查情况及保护方案等，通过计算分析、工程类比或相关试验等手段，评估外部作业对城市轨道交通结构安全影响程度的工作。',
        requirements=['安全评估 safety assessment 根据外部作业的设计与施工方案、城市轨道交通现状调查情况及保护方案等，通过计算分析、工程类比或相关试验等手段，评估外部作业对城市轨道交通结构安全影响程度的工作。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_6',
 'clause': '2.0.6',
 'chapter': '术语',
 'section': '2 术语',
 'title': '影响等级 influence class',
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
 'requirements': ['影响等级 influence class 外部作业对城市轨道交通结构安全影响程度的分级。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.6 影响等级 influence class."""

    return _evaluate_clause(
        clause='2.0.6',
        chapter='术语',
        section='2 术语',
        title='影响等级 influence class',
        basis='# 2.0.6 影响等级 influence class 外部作业对城市轨道交通结构安全影响程度的分级。',
        requirements=['影响等级 influence class 外部作业对城市轨道交通结构安全影响程度的分级。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_7',
 'clause': '2.0.7',
 'chapter': '术语',
 'section': '2 术语',
 'title': '净距控制值 value for net distance control',
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
 'requirements': ['净距控制值 value for net distance control 根据外部作业和城市轨道交通结构的特点，为保护结构安全，规定的外部作业区域外边线与城市轨道交通结构外边线之间的最小净距离。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.7 净距控制值 value for net distance control."""

    return _evaluate_clause(
        clause='2.0.7',
        chapter='术语',
        section='2 术语',
        title='净距控制值 value for net distance control',
        basis='# 2.0.7 净距控制值 value for net distance control 根据外部作业和城市轨道交通结构的特点，为保护结构安全，规定的外部作业区域外边线与城市轨道交通结构外边线之间的最小净距离。',
        requirements=['净距控制值 value for net distance control 根据外部作业和城市轨道交通结构的特点，为保护结构安全，规定的外部作业区域外边线与城市轨道交通结构外边线之间的最小净距离。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_8',
 'clause': '2.0.8',
 'chapter': '术语',
 'section': '2 术语',
 'title': '安全控制标准 standard for safety control',
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
 'requirements': ['安全控制标准 standard for safety control 根据城市轨道交通结构的安全现状及其保护要求，针对外部作业的特点，为保护城市轨道交通结构安全而制定的控制标准。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.8 安全控制标准 standard for safety control."""

    return _evaluate_clause(
        clause='2.0.8',
        chapter='术语',
        section='2 术语',
        title='安全控制标准 standard for safety control',
        basis='2.0.8 安全控制标准 standard for safety control 根据城市轨道交通结构的安全现状及其保护要求，针对外部作业的特点，为保护城市轨道交通结构安全而制定的控制标准。',
        requirements=['安全控制标准 standard for safety control 根据城市轨道交通结构的安全现状及其保护要求，针对外部作业的特点，为保护城市轨道交通结构安全而制定的控制标准。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_9_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_9',
 'clause': '2.0.9',
 'chapter': '术语',
 'section': '2 术语',
 'title': '结构安全控制指标 control index for structural safety',
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
 'requirements': ['结构安全控制指标 control index for structural safety '
                  '根据城市轨道交通结构的安全现状及其保护要求，基于外部作业过程中轨道交通结构的响应特征，为保护结构安全而选用的变形或内力等控制指标。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_9(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.9 结构安全控制指标 control index for structural safety."""

    return _evaluate_clause(
        clause='2.0.9',
        chapter='术语',
        section='2 术语',
        title='结构安全控制指标 control index for structural safety',
        basis='2.0.9 结构安全控制指标 control index for structural safety 根据城市轨道交通结构的安全现状及其保护要求，基于外部作业过程中轨道交通结构的响应特征，为保护结构安全而选用的变形或内力等控制指标。',
        requirements=['结构安全控制指标 control index for structural safety 根据城市轨道交通结构的安全现状及其保护要求，基于外部作业过程中轨道交通结构的响应特征，为保护结构安全而选用的变形或内力等控制指标。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_10_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_10',
 'clause': '2.0.10',
 'chapter': '术语',
 'section': '2 术语',
 'title': '现状调查 investigation of present state',
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
 'requirements': ['现状调查 investigation of present state '
                  '现状调查指对城市轨道交通结构的状态调查，包括外部作业实施时的工前调查、过程调查及工后确认。工前调查是对既有结构初始状态的观察和记录；过程调查是外部作业过程中对既有结构状态的跟踪监控；工后确认是在外部作业完成后对既有结构状态的再次确认。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_10(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.10 现状调查 investigation of present state."""

    return _evaluate_clause(
        clause='2.0.10',
        chapter='术语',
        section='2 术语',
        title='现状调查 investigation of present state',
        basis='2.0.10 现状调查 investigation of present state 现状调查指对城市轨道交通结构的状态调查，包括外部作业实施时的工前调查、过程调查及工后确认。工前调查是对既有结构初始状态的观察和记录；过程调查是外部作业过程中对既有结构状态的跟踪监控；工后确认是在外部作业完成后对既有结构状态的再次确认。',
        requirements=['现状调查 investigation of present state 现状调查指对城市轨道交通结构的状态调查，包括外部作业实施时的工前调查、过程调查及工后确认。工前调查是对既有结构初始状态的观察和记录；过程调查是外部作业过程中对既有结构状态的跟踪监控；工后确认是在外部作业完成后对既有结构状态的再次确认。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_11_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_11',
 'clause': '2.0.11',
 'chapter': '术语',
 'section': '2 术语',
 'title': '接口改造 interface modification',
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
 'requirements': ['接口改造 interface modification 当外部工程需与城市轨道交通结构相衔接时，采用改造既有结构的方式，实现外部结构与城市轨道交通设施相连接的工程。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_11(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.11 接口改造 interface modification."""

    return _evaluate_clause(
        clause='2.0.11',
        chapter='术语',
        section='2 术语',
        title='接口改造 interface modification',
        basis='2.0.11 接口改造 interface modification 当外部工程需与城市轨道交通结构相衔接时，采用改造既有结构的方式，实现外部结构与城市轨道交通设施相连接的工程。',
        requirements=['接口改造 interface modification 当外部工程需与城市轨道交通结构相衔接时，采用改造既有结构的方式，实现外部结构与城市轨道交通设施相连接的工程。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_12_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_12',
 'clause': '2.0.12',
 'chapter': '术语',
 'section': '2 术语',
 'title': '结构安全监测 structure safety monitoring',
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
 'requirements': ['结构安全监测 structure safety monitoring '
                  '为保护城市轨道交通结构安全，采用仪器量测、现场巡查或远程视频监控等手段和方法，实时、动态地收集反映城市轨道交通结构及其周边环境对象的安全状态、变化特征及发展趋势的信息，并进行分析和反馈。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_12(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.12 结构安全监测 structure safety monitoring."""

    return _evaluate_clause(
        clause='2.0.12',
        chapter='术语',
        section='2 术语',
        title='结构安全监测 structure safety monitoring',
        basis='2.0.12 结构安全监测 structure safety monitoring 为保护城市轨道交通结构安全，采用仪器量测、现场巡查或远程视频监控等手段和方法，实时、动态地收集反映城市轨道交通结构及其周边环境对象的安全状态、变化特征及发展趋势的信息，并进行分析和反馈。',
        requirements=['结构安全监测 structure safety monitoring 为保护城市轨道交通结构安全，采用仪器量测、现场巡查或远程视频监控等手段和方法，实时、动态地收集反映城市轨道交通结构及其周边环境对象的安全状态、变化特征及发展趋势的信息，并进行分析和反馈。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_13_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_13',
 'clause': '2.0.13',
 'chapter': '术语',
 'section': '2 术语',
 'title': '监测预警等级 alarming class on monitoring',
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
 'requirements': ['监测预警等级 alarming class on monitoring 根据监测值与其相应的结构安全控制指标值的比值，对城市轨道交通结构实行监测预警管理的分级。'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_13(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.13 监测预警等级 alarming class on monitoring."""

    return _evaluate_clause(
        clause='2.0.13',
        chapter='术语',
        section='2 术语',
        title='监测预警等级 alarming class on monitoring',
        basis='2.0.13 监测预警等级 alarming class on monitoring 根据监测值与其相应的结构安全控制指标值的比值，对城市轨道交通结构实行监测预警管理的分级。',
        requirements=['监测预警等级 alarming class on monitoring 根据监测值与其相应的结构安全控制指标值的比值，对城市轨道交通结构实行监测预警管理的分级。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_2_0_14_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_2_0_14',
 'clause': '2.0.14',
 'chapter': '术语',
 'section': '2 术语',
 'title': '地下结构病害 underground structural disease',
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
 'requirements': ['地下结构病害 underground structural disease 影响城市轨道交通结构安全性和耐久性的现象，包括渗漏水、管片裂损、管片错台、收敛变形及不均匀沉降等。 # 3 基本规定 # '
                  '3.1 一般规定'],
 'output': OUTPUT_SCHEMA}


def clause_2_0_14(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """2.0.14 地下结构病害 underground structural disease."""

    return _evaluate_clause(
        clause='2.0.14',
        chapter='术语',
        section='2 术语',
        title='地下结构病害 underground structural disease',
        basis='2.0.14 地下结构病害 underground structural disease 影响城市轨道交通结构安全性和耐久性的现象，包括渗漏水、管片裂损、管片错台、收敛变形及不均匀沉降等。 # 3 基本规定 # 3.1 一般规定',
        requirements=['地下结构病害 underground structural disease 影响城市轨道交通结构安全性和耐久性的现象，包括渗漏水、管片裂损、管片错台、收敛变形及不均匀沉降等。 # 3 基本规定 # 3.1 一般规定'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_2_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_2_functions",
    "chapter": '术语',
    "description": "DB32/T 4351-2022 chapter 2 clause function API schema.",
    "functions": {
        "clause_2_0_1": CLAUSE_2_0_1_INPUT_SCHEMA,
        "clause_2_0_2": CLAUSE_2_0_2_INPUT_SCHEMA,
        "clause_2_0_3": CLAUSE_2_0_3_INPUT_SCHEMA,
        "clause_2_0_4": CLAUSE_2_0_4_INPUT_SCHEMA,
        "clause_2_0_5": CLAUSE_2_0_5_INPUT_SCHEMA,
        "clause_2_0_6": CLAUSE_2_0_6_INPUT_SCHEMA,
        "clause_2_0_7": CLAUSE_2_0_7_INPUT_SCHEMA,
        "clause_2_0_8": CLAUSE_2_0_8_INPUT_SCHEMA,
        "clause_2_0_9": CLAUSE_2_0_9_INPUT_SCHEMA,
        "clause_2_0_10": CLAUSE_2_0_10_INPUT_SCHEMA,
        "clause_2_0_11": CLAUSE_2_0_11_INPUT_SCHEMA,
        "clause_2_0_12": CLAUSE_2_0_12_INPUT_SCHEMA,
        "clause_2_0_13": CLAUSE_2_0_13_INPUT_SCHEMA,
        "clause_2_0_14": CLAUSE_2_0_14_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_2_0_1(confirmed_items=['城市轨道交通结构 urban rail transit structure 保障城市轨道交通列车安全运营和结构体系稳定的主要受力结构，指城市轨道交通结构本体，包括地面和高架结构、地下结构及相关附属结构。'], strict=False)
    print(first.to_dict())
