"""Functions for Chapter 7 of DB32/T 4351-2022.

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

CLAUSE_7_1_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_1_1',
 'clause': '7.1.1',
 'chapter': '安全监测',
 'section': '7.1 一般规定',
 'title': '在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。',
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
 'requirements': ['在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。'],
 'output': OUTPUT_SCHEMA}


def clause_7_1_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.1.1 在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。."""

    return _evaluate_clause(
        clause='7.1.1',
        chapter='安全监测',
        section='7.1 一般规定',
        title='在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。',
        basis='7.1.1 在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。',
        requirements=['在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_1_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_1_2',
 'clause': '7.1.2',
 'chapter': '安全监测',
 'section': '7.1 一般规定',
 'title': '应在外部作业实施前完成监测点的布设并采集初始值，施工过程中应进行动态监测，监测成果应能准确及时反映监测对象的变化特征和安全状态。',
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
 'requirements': ['应在外部作业实施前完成监测点的布设并采集初始值，施工过程中应进行动态监测，监测成果应能准确及时反映监测对象的变化特征和安全状态。'],
 'output': OUTPUT_SCHEMA}


def clause_7_1_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.1.2 应在外部作业实施前完成监测点的布设并采集初始值，施工过程中应进行动态监测，监测成果应能准确及时反映监测对象的变化特征和安全状态。."""

    return _evaluate_clause(
        clause='7.1.2',
        chapter='安全监测',
        section='7.1 一般规定',
        title='应在外部作业实施前完成监测点的布设并采集初始值，施工过程中应进行动态监测，监测成果应能准确及时反映监测对象的变化特征和安全状态。',
        basis='7.1.2 应在外部作业实施前完成监测点的布设并采集初始值，施工过程中应进行动态监测，监测成果应能准确及时反映监测对象的变化特征和安全状态。',
        requirements=['应在外部作业实施前完成监测点的布设并采集初始值，施工过程中应进行动态监测，监测成果应能准确及时反映监测对象的变化特征和安全状态。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_1_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_1_3',
 'clause': '7.1.3',
 'chapter': '安全监测',
 'section': '7.1 一般规定',
 'title': '监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合的综合监控方法，当外部作业影响等级为特级、一级时，宜采用自动化监测。',
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
 'requirements': ['监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合的综合监控方法，当外部作业影响等级为特级、一级时，宜采用自动化监测。'],
 'output': OUTPUT_SCHEMA}


def clause_7_1_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.1.3 监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合的综合监控方法，当外部作业影响等级为特级、一级时，宜采用自动化监测。."""

    return _evaluate_clause(
        clause='7.1.3',
        chapter='安全监测',
        section='7.1 一般规定',
        title='监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合的综合监控方法，当外部作业影响等级为特级、一级时，宜采用自动化监测。',
        basis='7.1.3 监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合的综合监控方法，当外部作业影响等级为特级、一级时，宜采用自动化监测。',
        requirements=['监测方法宜采用仪器量测、现场巡视或远程视频监控等多种手段相结合的综合监控方法，当外部作业影响等级为特级、一级时，宜采用自动化监测。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_1_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_1_4',
 'clause': '7.1.4',
 'chapter': '安全监测',
 'section': '7.1 一般规定',
 'title': '除采用常规监测方法外，可积极采用光纤光栅、三维激光扫描、近景摄影测量、微波遥感测量等新技术、新方法；新技术、新方法应用时，应进行对比验证，监测精度不应低于其替代',
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
 'requirements': ['除采用常规监测方法外，可积极采用光纤光栅、三维激光扫描、近景摄影测量、微波遥感测量等新技术、新方法；新技术、新方法应用时，应进行对比验证，监测精度不应低于其替代方法的精度要求。'],
 'output': OUTPUT_SCHEMA}


def clause_7_1_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.1.4 除采用常规监测方法外，可积极采用光纤光栅、三维激光扫描、近景摄影测量、微波遥感测量等新技术、新方法；新技术、新方法应用时，应进行对比验证，监测精度不应低于其替代."""

    return _evaluate_clause(
        clause='7.1.4',
        chapter='安全监测',
        section='7.1 一般规定',
        title='除采用常规监测方法外，可积极采用光纤光栅、三维激光扫描、近景摄影测量、微波遥感测量等新技术、新方法；新技术、新方法应用时，应进行对比验证，监测精度不应低于其替代',
        basis='7.1.4 除采用常规监测方法外，可积极采用光纤光栅、三维激光扫描、近景摄影测量、微波遥感测量等新技术、新方法；新技术、新方法应用时，应进行对比验证，监测精度不应低于其替代方法的精度要求。',
        requirements=['除采用常规监测方法外，可积极采用光纤光栅、三维激光扫描、近景摄影测量、微波遥感测量等新技术、新方法；新技术、新方法应用时，应进行对比验证，监测精度不应低于其替代方法的精度要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_1_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_1_5',
 'clause': '7.1.5',
 'chapter': '安全监测',
 'section': '7.1 一般规定',
 'title': '同一监测项目应采用相同的监测网、监测方法和监测路线，并固定监测人员、仪器和设备。',
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
 'requirements': ['同一监测项目应采用相同的监测网、监测方法和监测路线，并固定监测人员、仪器和设备。'],
 'output': OUTPUT_SCHEMA}


def clause_7_1_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.1.5 同一监测项目应采用相同的监测网、监测方法和监测路线，并固定监测人员、仪器和设备。."""

    return _evaluate_clause(
        clause='7.1.5',
        chapter='安全监测',
        section='7.1 一般规定',
        title='同一监测项目应采用相同的监测网、监测方法和监测路线，并固定监测人员、仪器和设备。',
        basis='7.1.5 同一监测项目应采用相同的监测网、监测方法和监测路线，并固定监测人员、仪器和设备。',
        requirements=['同一监测项目应采用相同的监测网、监测方法和监测路线，并固定监测人员、仪器和设备。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_1_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_1_6',
 'clause': '7.1.6',
 'chapter': '安全监测',
 'section': '7.1 一般规定',
 'title': '监测的技术标准、测量精度等应符合现行国家标准的规定。',
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
 'requirements': ['监测的技术标准、测量精度等应符合现行国家标准的规定。 # 7.2 监测项目'],
 'output': OUTPUT_SCHEMA}


def clause_7_1_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.1.6 监测的技术标准、测量精度等应符合现行国家标准的规定。."""

    return _evaluate_clause(
        clause='7.1.6',
        chapter='安全监测',
        section='7.1 一般规定',
        title='监测的技术标准、测量精度等应符合现行国家标准的规定。',
        basis='7.1.6 监测的技术标准、测量精度等应符合现行国家标准的规定。 # 7.2 监测项目',
        requirements=['监测的技术标准、测量精度等应符合现行国家标准的规定。 # 7.2 监测项目'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_1',
 'clause': '7.2.1',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '监测项目应根据外部作业影响等级确定，与各监测对象匹配，满足工程设计、施工要求，并能及时反映外部作业对城',
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
 'requirements': ['监测项目应根据外部作业影响等级确定，与各监测对象匹配，满足工程设计、施工要求，并能及时反映外部作业对城 市轨道交通结构安全的影响。'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.1 监测项目应根据外部作业影响等级确定，与各监测对象匹配，满足工程设计、施工要求，并能及时反映外部作业对城."""

    return _evaluate_clause(
        clause='7.2.1',
        chapter='安全监测',
        section='7.2 监测项目',
        title='监测项目应根据外部作业影响等级确定，与各监测对象匹配，满足工程设计、施工要求，并能及时反映外部作业对城',
        basis='7.2.1 监测项目应根据外部作业影响等级确定，与各监测对象匹配，满足工程设计、施工要求，并能及时反映外部作业对城 市轨道交通结构安全的影响。',
        requirements=['监测项目应根据外部作业影响等级确定，与各监测对象匹配，满足工程设计、施工要求，并能及时反映外部作业对城 市轨道交通结构安全的影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_2',
 'clause': '7.2.2',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '地面结构的监测项目应根据表7.2.2选择。',
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
 'requirements': ['地面结构的监测项目应根据表7.2.2选择。 表 7.2.2 地面结构监测项目 '
                  '序号监测对象监测项目外部作业影响等级特级一级二级三级四级1地面结构结构竖向位移应测应测应测宜测宜测2地面竖向位移应测应测宜测可测可测3水平位移宜测宜测可测可测可测4结构裂缝应测应测宜测可测可测5结构倾斜宜测可测可测可测可测6地面区间及出入线路基竖向位移应测应测应测宜测可测7过渡段差异沉降应测应测应测宜测宜测 '
                  '注：地面结构包括地面车站、出入口、通风亭、冷却塔、无'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.2 地面结构的监测项目应根据表7.2.2选择。."""

    return _evaluate_clause(
        clause='7.2.2',
        chapter='安全监测',
        section='7.2 监测项目',
        title='地面结构的监测项目应根据表7.2.2选择。',
        basis='# 7.2.2 地面结构的监测项目应根据表7.2.2选择。 表 7.2.2 地面结构监测项目 序号监测对象监测项目外部作业影响等级特级一级二级三级四级1地面结构结构竖向位移应测应测应测宜测宜测2地面竖向位移应测应测宜测可测可测3水平位移宜测宜测可测可测可测4结构裂缝应测应测宜测可测可测5结构倾斜宜测可测可测可测可测6地面区间及出入线路基竖向位移应测应测应测宜测可测7过渡段差异沉降应测应测应测宜测宜测 注：地面结构包括地面车站、出入口、通风亭、冷却塔、无障碍电梯、主变电站、车辆基地库房等。',
        requirements=['地面结构的监测项目应根据表7.2.2选择。 表 7.2.2 地面结构监测项目 序号监测对象监测项目外部作业影响等级特级一级二级三级四级1地面结构结构竖向位移应测应测应测宜测宜测2地面竖向位移应测应测宜测可测可测3水平位移宜测宜测可测可测可测4结构裂缝应测应测宜测可测可测5结构倾斜宜测可测可测可测可测6地面区间及出入线路基竖向位移应测应测应测宜测可测7过渡段差异沉降应测应测应测宜测宜测 注：地面结构包括地面车站、出入口、通风亭、冷却塔、无'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_3',
 'clause': '7.2.3',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '地下结构的监测项目应根据表7.2.3确定。',
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
 'requirements': ['地下结构的监测项目应根据表7.2.3确定。 表 7.2.3 地下结构监测项目 '
                  '序号监测对象监测项目外部作业影响等级特级一级二级三级四级1明挖法或矿山法地下结构竖向位移应测应测应测宜测宜测2水平位移应测应测应测宜测宜测3接缝处差异沉降应测应测应测宜测可测4结构裂缝应测应测宜测可测可测5立柱竖向位移应测宜测可测可测可测6结构倾斜宜测可测可测可测可测7盾构法或顶管法地下结构竖向位移应测应测应测宜测宜测8水平位移应测应测应测宜测可测9相对收敛应'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.3 地下结构的监测项目应根据表7.2.3确定。."""

    return _evaluate_clause(
        clause='7.2.3',
        chapter='安全监测',
        section='7.2 监测项目',
        title='地下结构的监测项目应根据表7.2.3确定。',
        basis='# 7.2.3 地下结构的监测项目应根据表7.2.3确定。 表 7.2.3 地下结构监测项目 序号监测对象监测项目外部作业影响等级特级一级二级三级四级1明挖法或矿山法地下结构竖向位移应测应测应测宜测宜测2水平位移应测应测应测宜测宜测3接缝处差异沉降应测应测应测宜测可测4结构裂缝应测应测宜测可测可测5立柱竖向位移应测宜测可测可测可测6结构倾斜宜测可测可测可测可测7盾构法或顶管法地下结构竖向位移应测应测应测宜测宜测8水平位移应测应测应测宜测可测9相对收敛应测应测宜测宜测宜测10接缝、裂缝应测应测宜测可测可测11隧道断面尺寸应测宜测宜测可测可测',
        requirements=['地下结构的监测项目应根据表7.2.3确定。 表 7.2.3 地下结构监测项目 序号监测对象监测项目外部作业影响等级特级一级二级三级四级1明挖法或矿山法地下结构竖向位移应测应测应测宜测宜测2水平位移应测应测应测宜测宜测3接缝处差异沉降应测应测应测宜测可测4结构裂缝应测应测宜测可测可测5立柱竖向位移应测宜测可测可测可测6结构倾斜宜测可测可测可测可测7盾构法或顶管法地下结构竖向位移应测应测应测宜测宜测8水平位移应测应测应测宜测可测9相对收敛应'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_4',
 'clause': '7.2.4',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '高架结构的监测项目应根据表7.2.4选择。',
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
 'requirements': ['高架结构的监测项目应根据表7.2.4选择。 表 7.2.4 高架结构监测项目 '
                  '序号监测对象监测项目外部作业影响等级特级一级二级三级四级1高架车站及高架桥梁竖向位移应测应测宜测宜测可测2相邻桥墩沉降位移差应测应测宜测宜测可测3墩台、墩顶横向位移宜测宜测可测可测可测4结构裂缝应测应测宜测可测可测5接头侧向位移(预制拼接墩柱)应测宜测可测可测可测'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.4 高架结构的监测项目应根据表7.2.4选择。."""

    return _evaluate_clause(
        clause='7.2.4',
        chapter='安全监测',
        section='7.2 监测项目',
        title='高架结构的监测项目应根据表7.2.4选择。',
        basis='# 7.2.4 高架结构的监测项目应根据表7.2.4选择。 表 7.2.4 高架结构监测项目 序号监测对象监测项目外部作业影响等级特级一级二级三级四级1高架车站及高架桥梁竖向位移应测应测宜测宜测可测2相邻桥墩沉降位移差应测应测宜测宜测可测3墩台、墩顶横向位移宜测宜测可测可测可测4结构裂缝应测应测宜测可测可测5接头侧向位移(预制拼接墩柱)应测宜测可测可测可测',
        requirements=['高架结构的监测项目应根据表7.2.4选择。 表 7.2.4 高架结构监测项目 序号监测对象监测项目外部作业影响等级特级一级二级三级四级1高架车站及高架桥梁竖向位移应测应测宜测宜测可测2相邻桥墩沉降位移差应测应测宜测宜测可测3墩台、墩顶横向位移宜测宜测可测可测可测4结构裂缝应测应测宜测可测可测5接头侧向位移(预制拼接墩柱)应测宜测可测可测可测'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_5',
 'clause': '7.2.5',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '城市轨道交通控制保护区内采用非嵌岩摩擦桩的超高层建设项目，结构封顶后还应继续进行附加变形影响测量。',
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
 'requirements': ['城市轨道交通控制保护区内采用非嵌岩摩擦桩的超高层建设项目，结构封顶后还应继续进行附加变形影响测量。'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.5 城市轨道交通控制保护区内采用非嵌岩摩擦桩的超高层建设项目，结构封顶后还应继续进行附加变形影响测量。."""

    return _evaluate_clause(
        clause='7.2.5',
        chapter='安全监测',
        section='7.2 监测项目',
        title='城市轨道交通控制保护区内采用非嵌岩摩擦桩的超高层建设项目，结构封顶后还应继续进行附加变形影响测量。',
        basis='7.2.5 城市轨道交通控制保护区内采用非嵌岩摩擦桩的超高层建设项目，结构封顶后还应继续进行附加变形影响测量。',
        requirements=['城市轨道交通控制保护区内采用非嵌岩摩擦桩的超高层建设项目，结构封顶后还应继续进行附加变形影响测量。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_6',
 'clause': '7.2.6',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '当遇到下列情况时，应对城市轨道交通结构附近的环境进行监测：',
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
 'requirements': ['外部降水作业时，应对既有结构附近的地下水位进行监测，若实施抽降承压水作业，还应监测既有结构附近的承压水位。',
                  '软土地区，轨道交通结构对外部作业敏感时，应对既有结构附近的土体分层竖向位移或深层水平位移进行监测。'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.6 当遇到下列情况时，应对城市轨道交通结构附近的环境进行监测：."""

    return _evaluate_clause(
        clause='7.2.6',
        chapter='安全监测',
        section='7.2 监测项目',
        title='当遇到下列情况时，应对城市轨道交通结构附近的环境进行监测：',
        basis='7.2.6 当遇到下列情况时，应对城市轨道交通结构附近的环境进行监测： 1 外部降水作业时，应对既有结构附近的地下水位进行监测，若实施抽降承压水作业，还应监测既有结构附近的承压水位。 2 软土地区，轨道交通结构对外部作业敏感时，应对既有结构附近的土体分层竖向位移或深层水平位移进行监测。',
        requirements=['外部降水作业时，应对既有结构附近的地下水位进行监测，若实施抽降承压水作业，还应监测既有结构附近的承压水位。', '软土地区，轨道交通结构对外部作业敏感时，应对既有结构附近的土体分层竖向位移或深层水平位移进行监测。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_7',
 'clause': '7.2.7',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '当外部作业为基坑工程时，监测项目除满足本规程的要求外，还应符合《建筑基坑工程监测技术标准》GB50497的有关规定。',
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
 'requirements': ['当外部作业为基坑工程时，监测项目除满足本规程的要求外，还应符合《建筑基坑工程监测技术标准》GB50497的有关规定。'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.7 当外部作业为基坑工程时，监测项目除满足本规程的要求外，还应符合《建筑基坑工程监测技术标准》GB50497的有关规定。."""

    return _evaluate_clause(
        clause='7.2.7',
        chapter='安全监测',
        section='7.2 监测项目',
        title='当外部作业为基坑工程时，监测项目除满足本规程的要求外，还应符合《建筑基坑工程监测技术标准》GB50497的有关规定。',
        basis='7.2.7 当外部作业为基坑工程时，监测项目除满足本规程的要求外，还应符合《建筑基坑工程监测技术标准》GB50497的有关规定。',
        requirements=['当外部作业为基坑工程时，监测项目除满足本规程的要求外，还应符合《建筑基坑工程监测技术标准》GB50497的有关规定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_8',
 'clause': '7.2.8',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '当外部作业需要采用爆破施工时，应监测城市轨道交通结构的振动速度。',
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
 'requirements': ['当外部作业需要采用爆破施工时，应监测城市轨道交通结构的振动速度。'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.8 当外部作业需要采用爆破施工时，应监测城市轨道交通结构的振动速度。."""

    return _evaluate_clause(
        clause='7.2.8',
        chapter='安全监测',
        section='7.2 监测项目',
        title='当外部作业需要采用爆破施工时，应监测城市轨道交通结构的振动速度。',
        basis='7.2.8 当外部作业需要采用爆破施工时，应监测城市轨道交通结构的振动速度。',
        requirements=['当外部作业需要采用爆破施工时，应监测城市轨道交通结构的振动速度。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_2_9_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_2_9',
 'clause': '7.2.9',
 'chapter': '安全监测',
 'section': '7.2 监测项目',
 'title': '当外部作业影响等级为特级时，应监测道床与轨道变位；当外部作业影响等级为一级时，宜监测道床与轨道变位；其他情况道床与轨道变位可根据工程实际情况选测，并应符合《城市',
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
 'requirements': ['当外部作业影响等级为特级时，应监测道床与轨道变位；当外部作业影响等级为一级时，宜监测道床与轨道变位；其他情况道床与轨道变位可根据工程实际情况选测，并应符合《城市轨道交通设施运营监测技术规范第4部分：轨道和路基》GB/T39559.4的有关规定。 '
                  '# 7.3 监测点布设'],
 'output': OUTPUT_SCHEMA}


def clause_7_2_9(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.2.9 当外部作业影响等级为特级时，应监测道床与轨道变位；当外部作业影响等级为一级时，宜监测道床与轨道变位；其他情况道床与轨道变位可根据工程实际情况选测，并应符合《城市."""

    return _evaluate_clause(
        clause='7.2.9',
        chapter='安全监测',
        section='7.2 监测项目',
        title='当外部作业影响等级为特级时，应监测道床与轨道变位；当外部作业影响等级为一级时，宜监测道床与轨道变位；其他情况道床与轨道变位可根据工程实际情况选测，并应符合《城市',
        basis='7.2.9 当外部作业影响等级为特级时，应监测道床与轨道变位；当外部作业影响等级为一级时，宜监测道床与轨道变位；其他情况道床与轨道变位可根据工程实际情况选测，并应符合《城市轨道交通设施运营监测技术规范第4部分：轨道和路基》GB/T39559.4的有关规定。 # 7.3 监测点布设',
        requirements=['当外部作业影响等级为特级时，应监测道床与轨道变位；当外部作业影响等级为一级时，宜监测道床与轨道变位；其他情况道床与轨道变位可根据工程实际情况选测，并应符合《城市轨道交通设施运营监测技术规范第4部分：轨道和路基》GB/T39559.4的有关规定。 # 7.3 监测点布设'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_3_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_3_1',
 'clause': '7.3.1',
 'chapter': '安全监测',
 'section': '7.3 监测点布设',
 'title': '监测点的布设位置、数量，应根据监测对象的类型和特征、外部作业影响等级、监测项目和监测方法的要求等综合确定，并能反映轨道交通结构和周边环境安全状态的要求。',
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
 'requirements': ['监测点的布设位置、数量，应根据监测对象的类型和特征、外部作业影响等级、监测项目和监测方法的要求等综合确定，并能反映轨道交通结构和周边环境安全状态的要求。'],
 'output': OUTPUT_SCHEMA}


def clause_7_3_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.3.1 监测点的布设位置、数量，应根据监测对象的类型和特征、外部作业影响等级、监测项目和监测方法的要求等综合确定，并能反映轨道交通结构和周边环境安全状态的要求。."""

    return _evaluate_clause(
        clause='7.3.1',
        chapter='安全监测',
        section='7.3 监测点布设',
        title='监测点的布设位置、数量，应根据监测对象的类型和特征、外部作业影响等级、监测项目和监测方法的要求等综合确定，并能反映轨道交通结构和周边环境安全状态的要求。',
        basis='7.3.1 监测点的布设位置、数量，应根据监测对象的类型和特征、外部作业影响等级、监测项目和监测方法的要求等综合确定，并能反映轨道交通结构和周边环境安全状态的要求。',
        requirements=['监测点的布设位置、数量，应根据监测对象的类型和特征、外部作业影响等级、监测项目和监测方法的要求等综合确定，并能反映轨道交通结构和周边环境安全状态的要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_3_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_3_2',
 'clause': '7.3.2',
 'chapter': '安全监测',
 'section': '7.3 监测点布设',
 'title': '监测点的埋设应便于观测，不应影响监测对象的正常受力和使用。监测点应埋设稳固、标识应清晰，并采取有效的保护措施，宜利用建设阶段已布设的基准点和监测点或长期观测的控',
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
 'requirements': ['监测点的埋设应便于观测，不应影响监测对象的正常受力和使用。监测点应埋设稳固、标识应清晰，并采取有效的保护措施，宜利用建设阶段已布设的基准点和监测点或长期观测的控制点。'],
 'output': OUTPUT_SCHEMA}


def clause_7_3_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.3.2 监测点的埋设应便于观测，不应影响监测对象的正常受力和使用。监测点应埋设稳固、标识应清晰，并采取有效的保护措施，宜利用建设阶段已布设的基准点和监测点或长期观测的控."""

    return _evaluate_clause(
        clause='7.3.2',
        chapter='安全监测',
        section='7.3 监测点布设',
        title='监测点的埋设应便于观测，不应影响监测对象的正常受力和使用。监测点应埋设稳固、标识应清晰，并采取有效的保护措施，宜利用建设阶段已布设的基准点和监测点或长期观测的控',
        basis='7.3.2 监测点的埋设应便于观测，不应影响监测对象的正常受力和使用。监测点应埋设稳固、标识应清晰，并采取有效的保护措施，宜利用建设阶段已布设的基准点和监测点或长期观测的控制点。',
        requirements=['监测点的埋设应便于观测，不应影响监测对象的正常受力和使用。监测点应埋设稳固、标识应清晰，并采取有效的保护措施，宜利用建设阶段已布设的基准点和监测点或长期观测的控制点。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_3_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_3_3',
 'clause': '7.3.3',
 'chapter': '安全监测',
 'section': '7.3 监测点布设',
 'title': '监测点的布设范围应覆盖受外部作业影响的全部城市轨道交通结构，反映影响的时间和空间的变化规律，并不宜小于本规程表4.2.2的调查范围。',
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
 'requirements': ['监测点的布设范围应覆盖受外部作业影响的全部城市轨道交通结构，反映影响的时间和空间的变化规律，并不宜小于本规程表4.2.2的调查范围。'],
 'output': OUTPUT_SCHEMA}


def clause_7_3_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.3.3 监测点的布设范围应覆盖受外部作业影响的全部城市轨道交通结构，反映影响的时间和空间的变化规律，并不宜小于本规程表4.2.2的调查范围。."""

    return _evaluate_clause(
        clause='7.3.3',
        chapter='安全监测',
        section='7.3 监测点布设',
        title='监测点的布设范围应覆盖受外部作业影响的全部城市轨道交通结构，反映影响的时间和空间的变化规律，并不宜小于本规程表4.2.2的调查范围。',
        basis='7.3.3 监测点的布设范围应覆盖受外部作业影响的全部城市轨道交通结构，反映影响的时间和空间的变化规律，并不宜小于本规程表4.2.2的调查范围。',
        requirements=['监测点的布设范围应覆盖受外部作业影响的全部城市轨道交通结构，反映影响的时间和空间的变化规律，并不宜小于本规程表4.2.2的调查范围。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_3_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_3_4',
 'clause': '7.3.4',
 'chapter': '安全监测',
 'section': '7.3 监测点布设',
 'title': '在城市轨道交通结构周边采取抽降承压水作业时，应根据降水影响范围和影响程度调整监测点的布设范围。',
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
 'requirements': ['在城市轨道交通结构周边采取抽降承压水作业时，应根据降水影响范围和影响程度调整监测点的布设范围。'],
 'output': OUTPUT_SCHEMA}


def clause_7_3_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.3.4 在城市轨道交通结构周边采取抽降承压水作业时，应根据降水影响范围和影响程度调整监测点的布设范围。."""

    return _evaluate_clause(
        clause='7.3.4',
        chapter='安全监测',
        section='7.3 监测点布设',
        title='在城市轨道交通结构周边采取抽降承压水作业时，应根据降水影响范围和影响程度调整监测点的布设范围。',
        basis='7.3.4 在城市轨道交通结构周边采取抽降承压水作业时，应根据降水影响范围和影响程度调整监测点的布设范围。',
        requirements=['在城市轨道交通结构周边采取抽降承压水作业时，应根据降水影响范围和影响程度调整监测点的布设范围。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_3_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_3_5',
 'clause': '7.3.5',
 'chapter': '安全监测',
 'section': '7.3 监测点布设',
 'title': '监测点位置应结合安全评估成果，布设在监测对象变形和内力的关键特征部位上，监测点的布置要求宜符合表7.3.5的规定。地下结构曲线段监测断面的间距可适当加密。',
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
 'requirements': ['监测点位置应结合安全评估成果，布设在监测对象变形和内力的关键特征部位上，监测点的布置要求宜符合表7.3.5的规定。地下结构曲线段监测断面的间距可适当加密。 表 7.3.5 监测点布置要求 '
                  '序号监测项目监测点位置监测断面间距强烈影响区显著影响区一般及较小影响区1竖向位移地下结构底板、拱顶、侧墙、道床；地面及高架结构底层柱、桥面、桥墩3m~5m5m~10m10m~20m2水平位移地下结构底板、拱顶、侧墙；地面及高架结构桥面、结构顶部、桥墩3'],
 'output': OUTPUT_SCHEMA}


def clause_7_3_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.3.5 监测点位置应结合安全评估成果，布设在监测对象变形和内力的关键特征部位上，监测点的布置要求宜符合表7.3.5的规定。地下结构曲线段监测断面的间距可适当加密。."""

    return _evaluate_clause(
        clause='7.3.5',
        chapter='安全监测',
        section='7.3 监测点布设',
        title='监测点位置应结合安全评估成果，布设在监测对象变形和内力的关键特征部位上，监测点的布置要求宜符合表7.3.5的规定。地下结构曲线段监测断面的间距可适当加密。',
        basis='7.3.5 监测点位置应结合安全评估成果，布设在监测对象变形和内力的关键特征部位上，监测点的布置要求宜符合表7.3.5的规定。地下结构曲线段监测断面的间距可适当加密。 表 7.3.5 监测点布置要求 序号监测项目监测点位置监测断面间距强烈影响区显著影响区一般及较小影响区1竖向位移地下结构底板、拱顶、侧墙、道床；地面及高架结构底层柱、桥面、桥墩3m~5m5m~10m10m~20m2水平位移地下结构底板、拱顶、侧墙；地面及高架结构桥面、结构顶部、桥墩3m~5m5m~10m10m~20m3相对收敛地下结构每监测断面布置不少于两条测线3m~5m5m~10m10m~20m4隧道断面变形监测断面与线路纵向垂直,点位于断面上均匀布置3m~5m或重点位置布设5m~10m或重点位置布设10m~20m或重点位置布设5接缝、裂缝结构接缝位置、裂缝位置两侧缝的两侧均匀布置6地下水水位外部作业空间与轨道交通结构之间孔间距15m~25m7土体深层水平位移临近地下结构的支护结构和土体位置按变形断面或重点位置布设8振动速度结构薄弱部位、靠近爆破位置结构薄弱部位或结构与爆破点之间 注：表中外部作业工程影响分区可参照附录A执行，对于无明确影响分区划分的其他工程可根据工程实践合理确定。',
        requirements=['监测点位置应结合安全评估成果，布设在监测对象变形和内力的关键特征部位上，监测点的布置要求宜符合表7.3.5的规定。地下结构曲线段监测断面的间距可适当加密。 表 7.3.5 监测点布置要求 序号监测项目监测点位置监测断面间距强烈影响区显著影响区一般及较小影响区1竖向位移地下结构底板、拱顶、侧墙、道床；地面及高架结构底层柱、桥面、桥墩3m~5m5m~10m10m~20m2水平位移地下结构底板、拱顶、侧墙；地面及高架结构桥面、结构顶部、桥墩3'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_3_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_3_6',
 'clause': '7.3.6',
 'chapter': '安全监测',
 'section': '7.3 监测点布设',
 'title': '风井、冷却塔、主变电站、车辆基地等地面建筑或设施的竖向位移监测点宜布置于结构角点处，地表竖向位移监测点宜布置于上述竖向位移监测点附近；联络通道等结构特殊区段、结',
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
 'requirements': ['风井、冷却塔、主变电站、车辆基地等地面建筑或设施的竖向位移监测点宜布置于结构角点处，地表竖向位移监测点宜布置于上述竖向位移监测点附近；联络通道等结构特殊区段、结构存在初始缺陷、使用状况恶化区段和地质条件复杂区段的监测点，宜结合现场特点布设。 '
                  '# 7.4 监测技术要求'],
 'output': OUTPUT_SCHEMA}


def clause_7_3_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.3.6 风井、冷却塔、主变电站、车辆基地等地面建筑或设施的竖向位移监测点宜布置于结构角点处，地表竖向位移监测点宜布置于上述竖向位移监测点附近；联络通道等结构特殊区段、结."""

    return _evaluate_clause(
        clause='7.3.6',
        chapter='安全监测',
        section='7.3 监测点布设',
        title='风井、冷却塔、主变电站、车辆基地等地面建筑或设施的竖向位移监测点宜布置于结构角点处，地表竖向位移监测点宜布置于上述竖向位移监测点附近；联络通道等结构特殊区段、结',
        basis='7.3.6 风井、冷却塔、主变电站、车辆基地等地面建筑或设施的竖向位移监测点宜布置于结构角点处，地表竖向位移监测点宜布置于上述竖向位移监测点附近；联络通道等结构特殊区段、结构存在初始缺陷、使用状况恶化区段和地质条件复杂区段的监测点，宜结合现场特点布设。 # 7.4 监测技术要求',
        requirements=['风井、冷却塔、主变电站、车辆基地等地面建筑或设施的竖向位移监测点宜布置于结构角点处，地表竖向位移监测点宜布置于上述竖向位移监测点附近；联络通道等结构特殊区段、结构存在初始缺陷、使用状况恶化区段和地质条件复杂区段的监测点，宜结合现场特点布设。 # 7.4 监测技术要求'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_1',
 'clause': '7.4.1',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '监测方案应依据外部作业特点及其对轨道交通结构的影响等级、轨道交通结构类型和安全评估成果编制，并符合国家及行业现行标准、规范的相关要求。',
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
 'requirements': ['监测方案应依据外部作业特点及其对轨道交通结构的影响等级、轨道交通结构类型和安全评估成果编制，并符合国家及行业现行标准、规范的相关要求。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.1 监测方案应依据外部作业特点及其对轨道交通结构的影响等级、轨道交通结构类型和安全评估成果编制，并符合国家及行业现行标准、规范的相关要求。."""

    return _evaluate_clause(
        clause='7.4.1',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='监测方案应依据外部作业特点及其对轨道交通结构的影响等级、轨道交通结构类型和安全评估成果编制，并符合国家及行业现行标准、规范的相关要求。',
        basis='7.4.1 监测方案应依据外部作业特点及其对轨道交通结构的影响等级、轨道交通结构类型和安全评估成果编制，并符合国家及行业现行标准、规范的相关要求。',
        requirements=['监测方案应依据外部作业特点及其对轨道交通结构的影响等级、轨道交通结构类型和安全评估成果编制，并符合国家及行业现行标准、规范的相关要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_2',
 'clause': '7.4.2',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '城市轨道交通结构的监测基准点应设置在远离外部作业施工影响区且变形稳定之处。',
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
 'requirements': ['城市轨道交通结构的监测基准点应设置在远离外部作业施工影响区且变形稳定之处。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.2 城市轨道交通结构的监测基准点应设置在远离外部作业施工影响区且变形稳定之处。."""

    return _evaluate_clause(
        clause='7.4.2',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='城市轨道交通结构的监测基准点应设置在远离外部作业施工影响区且变形稳定之处。',
        basis='7.4.2 城市轨道交通结构的监测基准点应设置在远离外部作业施工影响区且变形稳定之处。',
        requirements=['城市轨道交通结构的监测基准点应设置在远离外部作业施工影响区且变形稳定之处。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_3',
 'clause': '7.4.3',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '监测项目的初始值应在监测点埋设稳定后、外部作业实施前及时采集，应取至少连续测量3次的稳定值的平均值作为初始值。',
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
 'requirements': ['监测项目的初始值应在监测点埋设稳定后、外部作业实施前及时采集，应取至少连续测量3次的稳定值的平均值作为初始值。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.3 监测项目的初始值应在监测点埋设稳定后、外部作业实施前及时采集，应取至少连续测量3次的稳定值的平均值作为初始值。."""

    return _evaluate_clause(
        clause='7.4.3',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='监测项目的初始值应在监测点埋设稳定后、外部作业实施前及时采集，应取至少连续测量3次的稳定值的平均值作为初始值。',
        basis='7.4.3 监测项目的初始值应在监测点埋设稳定后、外部作业实施前及时采集，应取至少连续测量3次的稳定值的平均值作为初始值。',
        requirements=['监测项目的初始值应在监测点埋设稳定后、外部作业实施前及时采集，应取至少连续测量3次的稳定值的平均值作为初始值。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_4',
 'clause': '7.4.4',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '监测频率可按照本规程附录E的要求执行。其中基坑工程的监测频率可根据施工作业工况对轨道交通结构的影响程度进行调整。监测实施过程中，可根据变形速率合理调整监测频率，',
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
 'requirements': ['监测频率可按照本规程附录E的要求执行。其中基坑工程的监测频率可根据施工作业工况对轨道交通结构的影响程度进行调整。监测实施过程中，可根据变形速率合理调整监测频率，当测量数据达到报警值后，应加大监测频率、加强外部作业的工况巡查和轨道交通结构安全状态巡查，必要时应采用自动化监测手段进行连续监测。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.4 监测频率可按照本规程附录E的要求执行。其中基坑工程的监测频率可根据施工作业工况对轨道交通结构的影响程度进行调整。监测实施过程中，可根据变形速率合理调整监测频率，."""

    return _evaluate_clause(
        clause='7.4.4',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='监测频率可按照本规程附录E的要求执行。其中基坑工程的监测频率可根据施工作业工况对轨道交通结构的影响程度进行调整。监测实施过程中，可根据变形速率合理调整监测频率，',
        basis='7.4.4 监测频率可按照本规程附录E的要求执行。其中基坑工程的监测频率可根据施工作业工况对轨道交通结构的影响程度进行调整。监测实施过程中，可根据变形速率合理调整监测频率，当测量数据达到报警值后，应加大监测频率、加强外部作业的工况巡查和轨道交通结构安全状态巡查，必要时应采用自动化监测手段进行连续监测。',
        requirements=['监测频率可按照本规程附录E的要求执行。其中基坑工程的监测频率可根据施工作业工况对轨道交通结构的影响程度进行调整。监测实施过程中，可根据变形速率合理调整监测频率，当测量数据达到报警值后，应加大监测频率、加强外部作业的工况巡查和轨道交通结构安全状态巡查，必要时应采用自动化监测手段进行连续监测。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_5',
 'clause': '7.4.5',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '监测预警等级，应根据结构监测值的大小和变化趋势，以及相应的结构安全控制指标值进行划分。等级划分及应对管理措施应符合表7.4.5的规定。',
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
 'requirements': ['监测预警等级，应根据结构监测值的大小和变化趋势，以及相应的结构安全控制指标值进行划分。等级划分及应对管理措施应符合表7.4.5的规定。 表 7.4.5 监测预警等级划分及应对管理措施 '
                  '监测预警等级监测比值G应对管理措施-G&lt',
                  '0.6可正常进行外部作业黄色预警0.6≤G&lt',
                  '0.8监测报警,并采取加密监测点或提高监测频率等措施加强对城市轨道交通结构的监测橙色预警0.8≤G&lt',
                  '1.0应暂停外部作业,进行施工过程安全评估工作,各方共同制定相应安全保护措施,并经技术审查后,开展后续工作红色预警1.0≤G启动安全应急预案 注：1.监测比值 $G=$ '
                  '监测项目实测值/结构安全控制指标值。 2. 当同一测点每天的监测数据变化率值连续三天超过 $2\\mathrm{mm}$ 时，监测预警等级应评定为橙色。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.5 监测预警等级，应根据结构监测值的大小和变化趋势，以及相应的结构安全控制指标值进行划分。等级划分及应对管理措施应符合表7.4.5的规定。."""

    return _evaluate_clause(
        clause='7.4.5',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='监测预警等级，应根据结构监测值的大小和变化趋势，以及相应的结构安全控制指标值进行划分。等级划分及应对管理措施应符合表7.4.5的规定。',
        basis='7.4.5 监测预警等级，应根据结构监测值的大小和变化趋势，以及相应的结构安全控制指标值进行划分。等级划分及应对管理措施应符合表7.4.5的规定。 表 7.4.5 监测预警等级划分及应对管理措施 监测预警等级监测比值G应对管理措施-G&lt;0.6可正常进行外部作业黄色预警0.6≤G&lt;0.8监测报警,并采取加密监测点或提高监测频率等措施加强对城市轨道交通结构的监测橙色预警0.8≤G&lt;1.0应暂停外部作业,进行施工过程安全评估工作,各方共同制定相应安全保护措施,并经技术审查后,开展后续工作红色预警1.0≤G启动安全应急预案 注：1.监测比值 $G=$ 监测项目实测值/结构安全控制指标值。 2. 当同一测点每天的监测数据变化率值连续三天超过 $2\\mathrm{mm}$ 时，监测预警等级应评定为橙色。',
        requirements=['监测预警等级，应根据结构监测值的大小和变化趋势，以及相应的结构安全控制指标值进行划分。等级划分及应对管理措施应符合表7.4.5的规定。 表 7.4.5 监测预警等级划分及应对管理措施 监测预警等级监测比值G应对管理措施-G&lt', '0.6可正常进行外部作业黄色预警0.6≤G&lt', '0.8监测报警,并采取加密监测点或提高监测频率等措施加强对城市轨道交通结构的监测橙色预警0.8≤G&lt', '1.0应暂停外部作业,进行施工过程安全评估工作,各方共同制定相应安全保护措施,并经技术审查后,开展后续工作红色预警1.0≤G启动安全应急预案 注：1.监测比值 $G=$ 监测项目实测值/结构安全控制指标值。 2. 当同一测点每天的监测数据变化率值连续三天超过 $2\\mathrm{mm}$ 时，监测预警等级应评定为橙色。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_6',
 'clause': '7.4.6',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '当监测数据达到预警条件时，应按相应的预警状态发出预警并启动相应的预警响应。',
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
 'requirements': ['当监测数据达到预警条件时，应按相应的预警状态发出预警并启动相应的预警响应。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.6 当监测数据达到预警条件时，应按相应的预警状态发出预警并启动相应的预警响应。."""

    return _evaluate_clause(
        clause='7.4.6',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='当监测数据达到预警条件时，应按相应的预警状态发出预警并启动相应的预警响应。',
        basis='7.4.6 当监测数据达到预警条件时，应按相应的预警状态发出预警并启动相应的预警响应。',
        requirements=['当监测数据达到预警条件时，应按相应的预警状态发出预警并启动相应的预警响应。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_7',
 'clause': '7.4.7',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '城市轨道交通结构的监测周期，应贯穿于外部作业的全过程，从测定监测项目初始值开始，直至外部作业完成且受影响的轨道交通结构变形监测数据趋于稳定后结束。',
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
 'requirements': ['城市轨道交通结构的监测周期，应贯穿于外部作业的全过程，从测定监测项目初始值开始，直至外部作业完成且受影响的轨道交通结构变形监测数据趋于稳定后结束。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.7 城市轨道交通结构的监测周期，应贯穿于外部作业的全过程，从测定监测项目初始值开始，直至外部作业完成且受影响的轨道交通结构变形监测数据趋于稳定后结束。."""

    return _evaluate_clause(
        clause='7.4.7',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='城市轨道交通结构的监测周期，应贯穿于外部作业的全过程，从测定监测项目初始值开始，直至外部作业完成且受影响的轨道交通结构变形监测数据趋于稳定后结束。',
        basis='7.4.7 城市轨道交通结构的监测周期，应贯穿于外部作业的全过程，从测定监测项目初始值开始，直至外部作业完成且受影响的轨道交通结构变形监测数据趋于稳定后结束。',
        requirements=['城市轨道交通结构的监测周期，应贯穿于外部作业的全过程，从测定监测项目初始值开始，直至外部作业完成且受影响的轨道交通结构变形监测数据趋于稳定后结束。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_8',
 'clause': '7.4.8',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '城市轨道交通结构数据趋于稳定的标准为最后 $100\\mathrm{d}$ 的平均变形速率小于 $0.04\\mathrm{mm / d}$ 时，软土地区变形稳定标',
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
 'requirements': ['城市轨道交通结构数据趋于稳定的标准为最后 $100\\mathrm{d}$ 的平均变形速率小于 $0.04\\mathrm{mm / d}$ 时，软土地区变形稳定标准可放宽至小于 '
                  '$0.06\\mathrm{mm / d}$ 。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.8 城市轨道交通结构数据趋于稳定的标准为最后 $100\\mathrm{d}$ 的平均变形速率小于 $0.04\\mathrm{mm / d}$ 时，软土地区变形稳定标."""

    return _evaluate_clause(
        clause='7.4.8',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='城市轨道交通结构数据趋于稳定的标准为最后 $100\\mathrm{d}$ 的平均变形速率小于 $0.04\\mathrm{mm / d}$ 时，软土地区变形稳定标',
        basis='7.4.8 城市轨道交通结构数据趋于稳定的标准为最后 $100\\mathrm{d}$ 的平均变形速率小于 $0.04\\mathrm{mm / d}$ 时，软土地区变形稳定标准可放宽至小于 $0.06\\mathrm{mm / d}$ 。',
        requirements=['城市轨道交通结构数据趋于稳定的标准为最后 $100\\mathrm{d}$ 的平均变形速率小于 $0.04\\mathrm{mm / d}$ 时，软土地区变形稳定标准可放宽至小于 $0.06\\mathrm{mm / d}$ 。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_9_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_9',
 'clause': '7.4.9',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '应定期分析监测数据，当对变形监测成果存疑时，应进行复测并检核。',
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
 'requirements': ['应定期分析监测数据，当对变形监测成果存疑时，应进行复测并检核。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_9(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.9 应定期分析监测数据，当对变形监测成果存疑时，应进行复测并检核。."""

    return _evaluate_clause(
        clause='7.4.9',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='应定期分析监测数据，当对变形监测成果存疑时，应进行复测并检核。',
        basis='7.4.9 应定期分析监测数据，当对变形监测成果存疑时，应进行复测并检核。',
        requirements=['应定期分析监测数据，当对变形监测成果存疑时，应进行复测并检核。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_7_4_10_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_7_4_10',
 'clause': '7.4.10',
 'chapter': '安全监测',
 'section': '7.4 监测技术要求',
 'title': '进行高层建筑附加变形影响测量的，应满足下列规定：',
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
 'requirements': ['应结合外部作业施工工况及时开展，至外部建筑沉降稳定为止。'],
 'output': OUTPUT_SCHEMA}


def clause_7_4_10(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """7.4.10 进行高层建筑附加变形影响测量的，应满足下列规定：."""

    return _evaluate_clause(
        clause='7.4.10',
        chapter='安全监测',
        section='7.4 监测技术要求',
        title='进行高层建筑附加变形影响测量的，应满足下列规定：',
        basis='7.4.10 进行高层建筑附加变形影响测量的，应满足下列规定： 1 在城市轨道交通结构与新建建筑结构之间的土体内设置分层沉降观测项目，深度范围宜自地面至隧道结构底部以下 $5\\mathrm{m}$ 。 2 分层沉降观测点布设密度应结合土层设置，间距不宜大于 $5\\mathrm{m}$ ，且在隧道结构的顶部、腰部、底部对应的深度宜设置观测点。 3 应结合外部作业施工工况及时开展，至外部建筑沉降稳定为止。 4 监测频率可根据变形情况确定，但不宜低于1次/季度。 # 8 地下结构病害治理 # 8.1 一般规定',
        requirements=['应结合外部作业施工工况及时开展，至外部建筑沉降稳定为止。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_7_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_7_functions",
    "chapter": '安全监测',
    "description": "DB32/T 4351-2022 chapter 7 clause function API schema.",
    "functions": {
        "clause_7_1_1": CLAUSE_7_1_1_INPUT_SCHEMA,
        "clause_7_1_2": CLAUSE_7_1_2_INPUT_SCHEMA,
        "clause_7_1_3": CLAUSE_7_1_3_INPUT_SCHEMA,
        "clause_7_1_4": CLAUSE_7_1_4_INPUT_SCHEMA,
        "clause_7_1_5": CLAUSE_7_1_5_INPUT_SCHEMA,
        "clause_7_1_6": CLAUSE_7_1_6_INPUT_SCHEMA,
        "clause_7_2_1": CLAUSE_7_2_1_INPUT_SCHEMA,
        "clause_7_2_2": CLAUSE_7_2_2_INPUT_SCHEMA,
        "clause_7_2_3": CLAUSE_7_2_3_INPUT_SCHEMA,
        "clause_7_2_4": CLAUSE_7_2_4_INPUT_SCHEMA,
        "clause_7_2_5": CLAUSE_7_2_5_INPUT_SCHEMA,
        "clause_7_2_6": CLAUSE_7_2_6_INPUT_SCHEMA,
        "clause_7_2_7": CLAUSE_7_2_7_INPUT_SCHEMA,
        "clause_7_2_8": CLAUSE_7_2_8_INPUT_SCHEMA,
        "clause_7_2_9": CLAUSE_7_2_9_INPUT_SCHEMA,
        "clause_7_3_1": CLAUSE_7_3_1_INPUT_SCHEMA,
        "clause_7_3_2": CLAUSE_7_3_2_INPUT_SCHEMA,
        "clause_7_3_3": CLAUSE_7_3_3_INPUT_SCHEMA,
        "clause_7_3_4": CLAUSE_7_3_4_INPUT_SCHEMA,
        "clause_7_3_5": CLAUSE_7_3_5_INPUT_SCHEMA,
        "clause_7_3_6": CLAUSE_7_3_6_INPUT_SCHEMA,
        "clause_7_4_1": CLAUSE_7_4_1_INPUT_SCHEMA,
        "clause_7_4_2": CLAUSE_7_4_2_INPUT_SCHEMA,
        "clause_7_4_3": CLAUSE_7_4_3_INPUT_SCHEMA,
        "clause_7_4_4": CLAUSE_7_4_4_INPUT_SCHEMA,
        "clause_7_4_5": CLAUSE_7_4_5_INPUT_SCHEMA,
        "clause_7_4_6": CLAUSE_7_4_6_INPUT_SCHEMA,
        "clause_7_4_7": CLAUSE_7_4_7_INPUT_SCHEMA,
        "clause_7_4_8": CLAUSE_7_4_8_INPUT_SCHEMA,
        "clause_7_4_9": CLAUSE_7_4_9_INPUT_SCHEMA,
        "clause_7_4_10": CLAUSE_7_4_10_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_7_1_1(confirmed_items=['在城市轨道交通控制保护区内从事外部作业时，应对受其影响的轨道交通结构进行安全监测，监测工作不得影响轨道交通的正常运营。'], strict=False)
    print(first.to_dict())
