"""Functions for Chapter 4 of DB32/T 4351-2022.

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

CLAUSE_4_1_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_1_1',
 'clause': '4.1.1',
 'chapter': '既有结构保护',
 'section': '4.1 一般规定',
 'title': '在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。',
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
 'requirements': ['在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。'],
 'output': OUTPUT_SCHEMA}


def clause_4_1_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.1.1 在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。."""

    return _evaluate_clause(
        clause='4.1.1',
        chapter='既有结构保护',
        section='4.1 一般规定',
        title='在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。',
        basis='4.1.1 在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。',
        requirements=['在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_1_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_1_2',
 'clause': '4.1.2',
 'chapter': '既有结构保护',
 'section': '4.1 一般规定',
 'title': '在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述',
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
 'requirements': ['在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述规定执行。'],
 'output': OUTPUT_SCHEMA}


def clause_4_1_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.1.2 在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述."""

    return _evaluate_clause(
        clause='4.1.2',
        chapter='既有结构保护',
        section='4.1 一般规定',
        title='在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述',
        basis='4.1.2 在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述规定执行。',
        requirements=['在城市轨道交通控制保护区内从事重大影响外部作业时，应对既有结构进行安全评估和安全监测，在结构安全保护方案的基础上制定应急预案。外部作业影响等级为二级时，宜按上述规定执行。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_1_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_1_3',
 'clause': '4.1.3',
 'chapter': '既有结构保护',
 'section': '4.1 一般规定',
 'title': '当外部作业发生重大设计变更或施工变更时，应重新编制结构安全保护方案，并进行可行性论证。',
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
 'requirements': ['当外部作业发生重大设计变更或施工变更时，应重新编制结构安全保护方案，并进行可行性论证。'],
 'output': OUTPUT_SCHEMA}


def clause_4_1_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.1.3 当外部作业发生重大设计变更或施工变更时，应重新编制结构安全保护方案，并进行可行性论证。."""

    return _evaluate_clause(
        clause='4.1.3',
        chapter='既有结构保护',
        section='4.1 一般规定',
        title='当外部作业发生重大设计变更或施工变更时，应重新编制结构安全保护方案，并进行可行性论证。',
        basis='4.1.3 当外部作业发生重大设计变更或施工变更时，应重新编制结构安全保护方案，并进行可行性论证。',
        requirements=['当外部作业发生重大设计变更或施工变更时，应重新编制结构安全保护方案，并进行可行性论证。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_1_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_1_4',
 'clause': '4.1.4',
 'chapter': '既有结构保护',
 'section': '4.1 一般规定',
 'title': '外部作业实施时，应结合现场巡查和监测数据，动态调整结构安全保护方案与措施。',
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
 'requirements': ['外部作业实施时，应结合现场巡查和监测数据，动态调整结构安全保护方案与措施。 # 4.2 现状调查和现场巡查'],
 'output': OUTPUT_SCHEMA}


def clause_4_1_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.1.4 外部作业实施时，应结合现场巡查和监测数据，动态调整结构安全保护方案与措施。."""

    return _evaluate_clause(
        clause='4.1.4',
        chapter='既有结构保护',
        section='4.1 一般规定',
        title='外部作业实施时，应结合现场巡查和监测数据，动态调整结构安全保护方案与措施。',
        basis='4.1.4 外部作业实施时，应结合现场巡查和监测数据，动态调整结构安全保护方案与措施。 # 4.2 现状调查和现场巡查',
        requirements=['外部作业实施时，应结合现场巡查和监测数据，动态调整结构安全保护方案与措施。 # 4.2 现状调查和现场巡查'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_1',
 'clause': '4.2.1',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '城市轨道交通结构现状调查包括工前调查、过程调查及工后确认。现状调查应准确、全面反映结构的安全现状。',
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
 'requirements': ['城市轨道交通结构现状调查包括工前调查、过程调查及工后确认。现状调查应准确、全面反映结构的安全现状。'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.1 城市轨道交通结构现状调查包括工前调查、过程调查及工后确认。现状调查应准确、全面反映结构的安全现状。."""

    return _evaluate_clause(
        clause='4.2.1',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='城市轨道交通结构现状调查包括工前调查、过程调查及工后确认。现状调查应准确、全面反映结构的安全现状。',
        basis='4.2.1 城市轨道交通结构现状调查包括工前调查、过程调查及工后确认。现状调查应准确、全面反映结构的安全现状。',
        requirements=['城市轨道交通结构现状调查包括工前调查、过程调查及工后确认。现状调查应准确、全面反映结构的安全现状。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_2',
 'clause': '4.2.2',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '城市轨道交通结构的调查范围应根据外部作业的类别及其影响等级综合确定，并宜符合表4.2.2的规定：',
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
 'requirements': ['城市轨道交通结构的调查范围应根据外部作业的类别及其影响等级综合确定，并宜符合表4.2.2的规定： 表 4.2.2 现状调查范围 '
                  '外部作业类别影响等级特级一级二级三级四级基坑工程L+6hL+(4~6)hL+4hL+2hL隧道工程L+6DL+(4~6)DL+4DL+2DL管线工程L+20mL+10mL+5mL-道路工程L+30mL+20mL+10mL- '
                  '注：1. $L$ 表示外部作业的平面投影范围， $h$ 表示基坑深度， $D$ 表示隧道'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.2 城市轨道交通结构的调查范围应根据外部作业的类别及其影响等级综合确定，并宜符合表4.2.2的规定：."""

    return _evaluate_clause(
        clause='4.2.2',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='城市轨道交通结构的调查范围应根据外部作业的类别及其影响等级综合确定，并宜符合表4.2.2的规定：',
        basis='4.2.2 城市轨道交通结构的调查范围应根据外部作业的类别及其影响等级综合确定，并宜符合表4.2.2的规定： 表 4.2.2 现状调查范围 外部作业类别影响等级特级一级二级三级四级基坑工程L+6hL+(4~6)hL+4hL+2hL隧道工程L+6DL+(4~6)DL+4DL+2DL管线工程L+20mL+10mL+5mL-道路工程L+30mL+20mL+10mL- 注：1. $L$ 表示外部作业的平面投影范围， $h$ 表示基坑深度， $D$ 表示隧道外径或宽度。 2. 其他外部作业，如降水、桩基、地基加固等工程，应结合影响范围、接近程度、地质条件、施工工艺、地区工程经验等综合确定其调查范围。',
        requirements=['城市轨道交通结构的调查范围应根据外部作业的类别及其影响等级综合确定，并宜符合表4.2.2的规定： 表 4.2.2 现状调查范围 外部作业类别影响等级特级一级二级三级四级基坑工程L+6hL+(4~6)hL+4hL+2hL隧道工程L+6DL+(4~6)DL+4DL+2DL管线工程L+20mL+10mL+5mL-道路工程L+30mL+20mL+10mL- 注：1. $L$ 表示外部作业的平面投影范围， $h$ 表示基坑深度， $D$ 表示隧道'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_3',
 'clause': '4.2.3',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '工前调查应在安全评估之前进行，调查应包含但不限于以下内容：',
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
 'requirements': ['地质条件和外部作业场地周边环境条件。',
                  '勘察、设计、施工、竣工、大修和专项维修、前期外部作业影响扰动记录及监测数据等资料。',
                  '既有结构的变形及病害情况，重点是地下结构的渗漏水、道床脱空、不均匀沉降、管片裂损、管片接缝张开与错台等。'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.3 工前调查应在安全评估之前进行，调查应包含但不限于以下内容：."""

    return _evaluate_clause(
        clause='4.2.3',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='工前调查应在安全评估之前进行，调查应包含但不限于以下内容：',
        basis='# 4.2.3 工前调查应在安全评估之前进行，调查应包含但不限于以下内容： 1 地质条件和外部作业场地周边环境条件。 2 勘察、设计、施工、竣工、大修和专项维修、前期外部作业影响扰动记录及监测数据等资料。 3 既有结构的变形及病害情况，重点是地下结构的渗漏水、道床脱空、不均匀沉降、管片裂损、管片接缝张开与错台等。 4 重大影响外部作业调查范围内的结构断面测量，其中盾构法隧道宜进行逐环测量，明挖及矿山法隧道断面测量间距不宜大于 $5\\mathrm{m}$ 。',
        requirements=['地质条件和外部作业场地周边环境条件。', '勘察、设计、施工、竣工、大修和专项维修、前期外部作业影响扰动记录及监测数据等资料。', '既有结构的变形及病害情况，重点是地下结构的渗漏水、道床脱空、不均匀沉降、管片裂损、管片接缝张开与错台等。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_4',
 'clause': '4.2.4',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '施工过程中出现以下情况时，宜开展过程调查工作：',
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
 'requirements': ['既有结构原有病害出现较快发展或新增病害较多。'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.4 施工过程中出现以下情况时，宜开展过程调查工作：."""

    return _evaluate_clause(
        clause='4.2.4',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='施工过程中出现以下情况时，宜开展过程调查工作：',
        basis='# 4.2.4 施工过程中出现以下情况时，宜开展过程调查工作： 1 既有结构监测数据的变化量、变形速率均超过安全控制指标的 $60\\%$ 或变化量与变形速率之一超过安全控制指标的 $80\\%$ 。 2 既有结构原有病害出现较快发展或新增病害较多。',
        requirements=['既有结构原有病害出现较快发展或新增病害较多。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_5',
 'clause': '4.2.5',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '工后确认应在外部作业完成且既有结构变形稳定之后开展。确认范围与内容应与工前调查一致，当外部作业对既有结构造成较大影响时，应适当扩大工后确认的范围与内容。',
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
 'requirements': ['工后确认应在外部作业完成且既有结构变形稳定之后开展。确认范围与内容应与工前调查一致，当外部作业对既有结构造成较大影响时，应适当扩大工后确认的范围与内容。'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.5 工后确认应在外部作业完成且既有结构变形稳定之后开展。确认范围与内容应与工前调查一致，当外部作业对既有结构造成较大影响时，应适当扩大工后确认的范围与内容。."""

    return _evaluate_clause(
        clause='4.2.5',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='工后确认应在外部作业完成且既有结构变形稳定之后开展。确认范围与内容应与工前调查一致，当外部作业对既有结构造成较大影响时，应适当扩大工后确认的范围与内容。',
        basis='# 4.2.5 工后确认应在外部作业完成且既有结构变形稳定之后开展。确认范围与内容应与工前调查一致，当外部作业对既有结构造成较大影响时，应适当扩大工后确认的范围与内容。',
        requirements=['工后确认应在外部作业完成且既有结构变形稳定之后开展。确认范围与内容应与工前调查一致，当外部作业对既有结构造成较大影响时，应适当扩大工后确认的范围与内容。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_6',
 'clause': '4.2.6',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '工后确认结果应与工前调查结果进行对比，结合病害及变形的发展情况，综合评估既有结构的安全性、耐久性及其对运营安全的影响。',
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
 'requirements': ['工后确认结果应与工前调查结果进行对比，结合病害及变形的发展情况，综合评估既有结构的安全性、耐久性及其对运营安全的影响。'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.6 工后确认结果应与工前调查结果进行对比，结合病害及变形的发展情况，综合评估既有结构的安全性、耐久性及其对运营安全的影响。."""

    return _evaluate_clause(
        clause='4.2.6',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='工后确认结果应与工前调查结果进行对比，结合病害及变形的发展情况，综合评估既有结构的安全性、耐久性及其对运营安全的影响。',
        basis='4.2.6 工后确认结果应与工前调查结果进行对比，结合病害及变形的发展情况，综合评估既有结构的安全性、耐久性及其对运营安全的影响。',
        requirements=['工后确认结果应与工前调查结果进行对比，结合病害及变形的发展情况，综合评估既有结构的安全性、耐久性及其对运营安全的影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_7',
 'clause': '4.2.7',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '外部作业现场巡查应采取日常巡查和重点巡查相结合的方式，对重大影响外部作业，应进行重点巡查。',
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
 'requirements': ['外部作业现场巡查应采取日常巡查和重点巡查相结合的方式，对重大影响外部作业，应进行重点巡查。'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.7 外部作业现场巡查应采取日常巡查和重点巡查相结合的方式，对重大影响外部作业，应进行重点巡查。."""

    return _evaluate_clause(
        clause='4.2.7',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='外部作业现场巡查应采取日常巡查和重点巡查相结合的方式，对重大影响外部作业，应进行重点巡查。',
        basis='4.2.7 外部作业现场巡查应采取日常巡查和重点巡查相结合的方式，对重大影响外部作业，应进行重点巡查。',
        requirements=['外部作业现场巡查应采取日常巡查和重点巡查相结合的方式，对重大影响外部作业，应进行重点巡查。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_2_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_2_8',
 'clause': '4.2.8',
 'chapter': '既有结构保护',
 'section': '4.2 现状调查和现场巡查',
 'title': '当现场巡查发现既有结构出现异常时，应结合监测数据等资料，对结构进行安全状态分析，并采取有效措施降低不利影响。',
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
 'requirements': ['当现场巡查发现既有结构出现异常时，应结合监测数据等资料，对结构进行安全状态分析，并采取有效措施降低不利影响。 # 4.3 安全评估'],
 'output': OUTPUT_SCHEMA}


def clause_4_2_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.2.8 当现场巡查发现既有结构出现异常时，应结合监测数据等资料，对结构进行安全状态分析，并采取有效措施降低不利影响。."""

    return _evaluate_clause(
        clause='4.2.8',
        chapter='既有结构保护',
        section='4.2 现状调查和现场巡查',
        title='当现场巡查发现既有结构出现异常时，应结合监测数据等资料，对结构进行安全状态分析，并采取有效措施降低不利影响。',
        basis='4.2.8 当现场巡查发现既有结构出现异常时，应结合监测数据等资料，对结构进行安全状态分析，并采取有效措施降低不利影响。 # 4.3 安全评估',
        requirements=['当现场巡查发现既有结构出现异常时，应结合监测数据等资料，对结构进行安全状态分析，并采取有效措施降低不利影响。 # 4.3 安全评估'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_3_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_3_1',
 'clause': '4.3.1',
 'chapter': '既有结构保护',
 'section': '4.3 安全评估',
 'title': '安全评估宜贯穿于外部作业的设计、实施等各阶段，包括城市轨道交通结构的现状评估、外部作业影响预评估、外部作业施工过程评估和外部作业影响后评估，安全评估的流程如图4',
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
 'requirements': ['安全评估宜贯穿于外部作业的设计、实施等各阶段，包括城市轨道交通结构的现状评估、外部作业影响预评估、外部作业施工过程评估和外部作业影响后评估，安全评估的流程如图4.3.1所示。 图4.3.1 '
                  '安全评估流程'],
 'output': OUTPUT_SCHEMA}


def clause_4_3_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.3.1 安全评估宜贯穿于外部作业的设计、实施等各阶段，包括城市轨道交通结构的现状评估、外部作业影响预评估、外部作业施工过程评估和外部作业影响后评估，安全评估的流程如图4."""

    return _evaluate_clause(
        clause='4.3.1',
        chapter='既有结构保护',
        section='4.3 安全评估',
        title='安全评估宜贯穿于外部作业的设计、实施等各阶段，包括城市轨道交通结构的现状评估、外部作业影响预评估、外部作业施工过程评估和外部作业影响后评估，安全评估的流程如图4',
        basis='4.3.1 安全评估宜贯穿于外部作业的设计、实施等各阶段，包括城市轨道交通结构的现状评估、外部作业影响预评估、外部作业施工过程评估和外部作业影响后评估，安全评估的流程如图4.3.1所示。 图4.3.1 安全评估流程',
        requirements=['安全评估宜贯穿于外部作业的设计、实施等各阶段，包括城市轨道交通结构的现状评估、外部作业影响预评估、外部作业施工过程评估和外部作业影响后评估，安全评估的流程如图4.3.1所示。 图4.3.1 安全评估流程'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_3_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_3_2',
 'clause': '4.3.2',
 'chapter': '既有结构保护',
 'section': '4.3 安全评估',
 'title': '城市轨道交通结构的现状评估应在外部作业实施前，通过现状调查、检测、测量和计算分析等手段，评估当前既有结构的安全状态及剩余抗变形能力、承载能力，并确定相应的结',
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
 'requirements': ['城市轨道交通结构的现状评估应在外部作业实施前，通过现状调查、检测、测量和计算分析等手段，评估当前既有结构的安全状态及剩余抗变形能力、承载能力，并确定相应的结 构安全控制指标值。'],
 'output': OUTPUT_SCHEMA}


def clause_4_3_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.3.2 城市轨道交通结构的现状评估应在外部作业实施前，通过现状调查、检测、测量和计算分析等手段，评估当前既有结构的安全状态及剩余抗变形能力、承载能力，并确定相应的结."""

    return _evaluate_clause(
        clause='4.3.2',
        chapter='既有结构保护',
        section='4.3 安全评估',
        title='城市轨道交通结构的现状评估应在外部作业实施前，通过现状调查、检测、测量和计算分析等手段，评估当前既有结构的安全状态及剩余抗变形能力、承载能力，并确定相应的结',
        basis='4.3.2 城市轨道交通结构的现状评估应在外部作业实施前，通过现状调查、检测、测量和计算分析等手段，评估当前既有结构的安全状态及剩余抗变形能力、承载能力，并确定相应的结 构安全控制指标值。',
        requirements=['城市轨道交通结构的现状评估应在外部作业实施前，通过现状调查、检测、测量和计算分析等手段，评估当前既有结构的安全状态及剩余抗变形能力、承载能力，并确定相应的结 构安全控制指标值。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_3_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_3_3',
 'clause': '4.3.3',
 'chapter': '既有结构保护',
 'section': '4.3 安全评估',
 'title': '外部作业影响预评估应在外部作业实施前，采用理论分析、数值模拟和工程类比等方法，预测外部作业对城市轨道交通结构的影响程度，评估外部作业方案和既有结构保护方案的可行',
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
 'requirements': ['外部作业影响预评估应在外部作业实施前，采用理论分析、数值模拟和工程类比等方法，预测外部作业对城市轨道交通结构的影响程度，评估外部作业方案和既有结构保护方案的可行性。'],
 'output': OUTPUT_SCHEMA}


def clause_4_3_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.3.3 外部作业影响预评估应在外部作业实施前，采用理论分析、数值模拟和工程类比等方法，预测外部作业对城市轨道交通结构的影响程度，评估外部作业方案和既有结构保护方案的可行."""

    return _evaluate_clause(
        clause='4.3.3',
        chapter='既有结构保护',
        section='4.3 安全评估',
        title='外部作业影响预评估应在外部作业实施前，采用理论分析、数值模拟和工程类比等方法，预测外部作业对城市轨道交通结构的影响程度，评估外部作业方案和既有结构保护方案的可行',
        basis='4.3.3 外部作业影响预评估应在外部作业实施前，采用理论分析、数值模拟和工程类比等方法，预测外部作业对城市轨道交通结构的影响程度，评估外部作业方案和既有结构保护方案的可行性。',
        requirements=['外部作业影响预评估应在外部作业实施前，采用理论分析、数值模拟和工程类比等方法，预测外部作业对城市轨道交通结构的影响程度，评估外部作业方案和既有结构保护方案的可行性。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_3_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_3_4',
 'clause': '4.3.4',
 'chapter': '既有结构保护',
 'section': '4.3 安全评估',
 'title': '外部作业施工过程评估应根据城市轨道交通结构的监测数据、过程调查和外部作业预评估成果，及时评估既有结构当前的安全状态。',
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
 'requirements': ['外部作业施工过程评估应根据城市轨道交通结构的监测数据、过程调查和外部作业预评估成果，及时评估既有结构当前的安全状态。'],
 'output': OUTPUT_SCHEMA}


def clause_4_3_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.3.4 外部作业施工过程评估应根据城市轨道交通结构的监测数据、过程调查和外部作业预评估成果，及时评估既有结构当前的安全状态。."""

    return _evaluate_clause(
        clause='4.3.4',
        chapter='既有结构保护',
        section='4.3 安全评估',
        title='外部作业施工过程评估应根据城市轨道交通结构的监测数据、过程调查和外部作业预评估成果，及时评估既有结构当前的安全状态。',
        basis='4.3.4 外部作业施工过程评估应根据城市轨道交通结构的监测数据、过程调查和外部作业预评估成果，及时评估既有结构当前的安全状态。',
        requirements=['外部作业施工过程评估应根据城市轨道交通结构的监测数据、过程调查和外部作业预评估成果，及时评估既有结构当前的安全状态。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_3_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_3_5',
 'clause': '4.3.5',
 'chapter': '既有结构保护',
 'section': '4.3 安全评估',
 'title': '外部作业影响后评估应在外部作业完成后进行，根据外部作业对城市轨道交通结构造成的影响程度评估结构的安全状态；若结构变形较大或产生的病害较严重，则应根据轨道交通结构',
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
 'requirements': ['外部作业影响后评估应在外部作业完成后进行，根据外部作业对城市轨道交通结构造成的影响程度评估结构的安全状态；若结构变形较大或产生的病害较严重，则应根据轨道交通结构安全和运营安全要求，提出相应的修复、加固等治理措施。'],
 'output': OUTPUT_SCHEMA}


def clause_4_3_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.3.5 外部作业影响后评估应在外部作业完成后进行，根据外部作业对城市轨道交通结构造成的影响程度评估结构的安全状态；若结构变形较大或产生的病害较严重，则应根据轨道交通结构."""

    return _evaluate_clause(
        clause='4.3.5',
        chapter='既有结构保护',
        section='4.3 安全评估',
        title='外部作业影响后评估应在外部作业完成后进行，根据外部作业对城市轨道交通结构造成的影响程度评估结构的安全状态；若结构变形较大或产生的病害较严重，则应根据轨道交通结构',
        basis='4.3.5 外部作业影响后评估应在外部作业完成后进行，根据外部作业对城市轨道交通结构造成的影响程度评估结构的安全状态；若结构变形较大或产生的病害较严重，则应根据轨道交通结构安全和运营安全要求，提出相应的修复、加固等治理措施。',
        requirements=['外部作业影响后评估应在外部作业完成后进行，根据外部作业对城市轨道交通结构造成的影响程度评估结构的安全状态；若结构变形较大或产生的病害较严重，则应根据轨道交通结构安全和运营安全要求，提出相应的修复、加固等治理措施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_3_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_3_6',
 'clause': '4.3.6',
 'chapter': '既有结构保护',
 'section': '4.3 安全评估',
 'title': '安全评估应形成专项评估报告，内容包含对城市轨道交通结构的安全影响分析、结论及建议等，并应符合附录D的技术要求。',
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
 'requirements': ['安全评估应形成专项评估报告，内容包含对城市轨道交通结构的安全影响分析、结论及建议等，并应符合附录D的技术要求。 # 4.4 地下结构保护'],
 'output': OUTPUT_SCHEMA}


def clause_4_3_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.3.6 安全评估应形成专项评估报告，内容包含对城市轨道交通结构的安全影响分析、结论及建议等，并应符合附录D的技术要求。."""

    return _evaluate_clause(
        clause='4.3.6',
        chapter='既有结构保护',
        section='4.3 安全评估',
        title='安全评估应形成专项评估报告，内容包含对城市轨道交通结构的安全影响分析、结论及建议等，并应符合附录D的技术要求。',
        basis='4.3.6 安全评估应形成专项评估报告，内容包含对城市轨道交通结构的安全影响分析、结论及建议等，并应符合附录D的技术要求。 # 4.4 地下结构保护',
        requirements=['安全评估应形成专项评估报告，内容包含对城市轨道交通结构的安全影响分析、结论及建议等，并应符合附录D的技术要求。 # 4.4 地下结构保护'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_1',
 'clause': '4.4.1',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '城市轨道交通地下结构上方区域不应作为材料堆场，不宜设置基坑出土口或运输车道。外部作业的重型设施和设备应与既有结构保持一定的安全距离。',
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
 'requirements': ['城市轨道交通地下结构上方区域不应作为材料堆场，不宜设置基坑出土口或运输车道。外部作业的重型设施和设备应与既有结构保持一定的安全距离。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.1 城市轨道交通地下结构上方区域不应作为材料堆场，不宜设置基坑出土口或运输车道。外部作业的重型设施和设备应与既有结构保持一定的安全距离。."""

    return _evaluate_clause(
        clause='4.4.1',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='城市轨道交通地下结构上方区域不应作为材料堆场，不宜设置基坑出土口或运输车道。外部作业的重型设施和设备应与既有结构保持一定的安全距离。',
        basis='4.4.1 城市轨道交通地下结构上方区域不应作为材料堆场，不宜设置基坑出土口或运输车道。外部作业的重型设施和设备应与既有结构保持一定的安全距离。',
        requirements=['城市轨道交通地下结构上方区域不应作为材料堆场，不宜设置基坑出土口或运输车道。外部作业的重型设施和设备应与既有结构保持一定的安全距离。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_2',
 'clause': '4.4.2',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '在城市轨道交通控制保护区内进行加载或卸载作业时，应验算其对地下结构安全的影响，并应满足相应结构安全控制指标的要求。',
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
 'requirements': ['在城市轨道交通控制保护区内进行加载或卸载作业时，应验算其对地下结构安全的影响，并应满足相应结构安全控制指标的要求。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.2 在城市轨道交通控制保护区内进行加载或卸载作业时，应验算其对地下结构安全的影响，并应满足相应结构安全控制指标的要求。."""

    return _evaluate_clause(
        clause='4.4.2',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='在城市轨道交通控制保护区内进行加载或卸载作业时，应验算其对地下结构安全的影响，并应满足相应结构安全控制指标的要求。',
        basis='4.4.2 在城市轨道交通控制保护区内进行加载或卸载作业时，应验算其对地下结构安全的影响，并应满足相应结构安全控制指标的要求。',
        requirements=['在城市轨道交通控制保护区内进行加载或卸载作业时，应验算其对地下结构安全的影响，并应满足相应结构安全控制指标的要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_3',
 'clause': '4.4.3',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '在城市轨道交通控制保护区内进行工程勘探、拉锚、降水等钻孔作业时，应严格控制其与既有地下结构的净距，并制定安全可靠的作业方案。',
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
 'requirements': ['在城市轨道交通控制保护区内进行工程勘探、拉锚、降水等钻孔作业时，应严格控制其与既有地下结构的净距，并制定安全可靠的作业方案。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.3 在城市轨道交通控制保护区内进行工程勘探、拉锚、降水等钻孔作业时，应严格控制其与既有地下结构的净距，并制定安全可靠的作业方案。."""

    return _evaluate_clause(
        clause='4.4.3',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='在城市轨道交通控制保护区内进行工程勘探、拉锚、降水等钻孔作业时，应严格控制其与既有地下结构的净距，并制定安全可靠的作业方案。',
        basis='4.4.3 在城市轨道交通控制保护区内进行工程勘探、拉锚、降水等钻孔作业时，应严格控制其与既有地下结构的净距，并制定安全可靠的作业方案。',
        requirements=['在城市轨道交通控制保护区内进行工程勘探、拉锚、降水等钻孔作业时，应严格控制其与既有地下结构的净距，并制定安全可靠的作业方案。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_4',
 'clause': '4.4.4',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '在城市轨道交通控制保护区内新建建筑物时，应验算其',
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
 'requirements': ['在城市轨道交通控制保护区内新建建筑物时，应验算其 '
                  '建成后在地层中产生的附加荷载对既有地下结构的影响。对于新建高层建筑，可采取增大建筑退界、减少结构荷载、增大桩基刚度或采用端承桩等措施，降低外部作业完成后地层的后续沉降对既有地下结构的影响。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.4 在城市轨道交通控制保护区内新建建筑物时，应验算其."""

    return _evaluate_clause(
        clause='4.4.4',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='在城市轨道交通控制保护区内新建建筑物时，应验算其',
        basis='4.4.4 在城市轨道交通控制保护区内新建建筑物时，应验算其 建成后在地层中产生的附加荷载对既有地下结构的影响。对于新建高层建筑，可采取增大建筑退界、减少结构荷载、增大桩基刚度或采用端承桩等措施，降低外部作业完成后地层的后续沉降对既有地下结构的影响。',
        requirements=['在城市轨道交通控制保护区内新建建筑物时，应验算其 建成后在地层中产生的附加荷载对既有地下结构的影响。对于新建高层建筑，可采取增大建筑退界、减少结构荷载、增大桩基刚度或采用端承桩等措施，降低外部作业完成后地层的后续沉降对既有地下结构的影响。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_5',
 'clause': '4.4.5',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '在城市轨道交通结构上方进行原有建筑拆除时，应采取逐层拆除辅以监测等有效措施，避免既有地下结构上方荷载的急剧变化。',
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
 'requirements': ['在城市轨道交通结构上方进行原有建筑拆除时，应采取逐层拆除辅以监测等有效措施，避免既有地下结构上方荷载的急剧变化。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.5 在城市轨道交通结构上方进行原有建筑拆除时，应采取逐层拆除辅以监测等有效措施，避免既有地下结构上方荷载的急剧变化。."""

    return _evaluate_clause(
        clause='4.4.5',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='在城市轨道交通结构上方进行原有建筑拆除时，应采取逐层拆除辅以监测等有效措施，避免既有地下结构上方荷载的急剧变化。',
        basis='4.4.5 在城市轨道交通结构上方进行原有建筑拆除时，应采取逐层拆除辅以监测等有效措施，避免既有地下结构上方荷载的急剧变化。',
        requirements=['在城市轨道交通结构上方进行原有建筑拆除时，应采取逐层拆除辅以监测等有效措施，避免既有地下结构上方荷载的急剧变化。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_6',
 'clause': '4.4.6',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '在城市轨道交通车站等明挖结构上方进行道路、管线等外部作业时，应与既有地下结构的防水保护层保持合理的安全距离。当外部作业需部分凿除结构压顶梁或冠梁时，不得影响既有',
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
 'requirements': ['在城市轨道交通车站等明挖结构上方进行道路、管线等外部作业时，应与既有地下结构的防水保护层保持合理的安全距离。当外部作业需部分凿除结构压顶梁或冠梁时，不得影响既有结构本体安全和抗浮安全，并应满足防渗漏要求。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.6 在城市轨道交通车站等明挖结构上方进行道路、管线等外部作业时，应与既有地下结构的防水保护层保持合理的安全距离。当外部作业需部分凿除结构压顶梁或冠梁时，不得影响既有."""

    return _evaluate_clause(
        clause='4.4.6',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='在城市轨道交通车站等明挖结构上方进行道路、管线等外部作业时，应与既有地下结构的防水保护层保持合理的安全距离。当外部作业需部分凿除结构压顶梁或冠梁时，不得影响既有',
        basis='4.4.6 在城市轨道交通车站等明挖结构上方进行道路、管线等外部作业时，应与既有地下结构的防水保护层保持合理的安全距离。当外部作业需部分凿除结构压顶梁或冠梁时，不得影响既有结构本体安全和抗浮安全，并应满足防渗漏要求。',
        requirements=['在城市轨道交通车站等明挖结构上方进行道路、管线等外部作业时，应与既有地下结构的防水保护层保持合理的安全距离。当外部作业需部分凿除结构压顶梁或冠梁时，不得影响既有结构本体安全和抗浮安全，并应满足防渗漏要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_7',
 'clause': '4.4.7',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '在城市轨道交通地下结构周边进行注浆、旋喷等有附加压力的外部作业时，宜通过工程类比或相似地层中的压力控制试验，合理确定压力控制参数，使作用于既有结构侧壁上的附加荷',
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
 'requirements': ['在城市轨道交通地下结构周边进行注浆、旋喷等有附加压力的外部作业时，宜通过工程类比或相似地层中的压力控制试验，合理确定压力控制参数，使作用于既有结构侧壁上的附加荷载不大于 '
                  '$20\\mathrm{kPa}$ 。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.7 在城市轨道交通地下结构周边进行注浆、旋喷等有附加压力的外部作业时，宜通过工程类比或相似地层中的压力控制试验，合理确定压力控制参数，使作用于既有结构侧壁上的附加荷."""

    return _evaluate_clause(
        clause='4.4.7',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='在城市轨道交通地下结构周边进行注浆、旋喷等有附加压力的外部作业时，宜通过工程类比或相似地层中的压力控制试验，合理确定压力控制参数，使作用于既有结构侧壁上的附加荷',
        basis='4.4.7 在城市轨道交通地下结构周边进行注浆、旋喷等有附加压力的外部作业时，宜通过工程类比或相似地层中的压力控制试验，合理确定压力控制参数，使作用于既有结构侧壁上的附加荷载不大于 $20\\mathrm{kPa}$ 。',
        requirements=['在城市轨道交通地下结构周边进行注浆、旋喷等有附加压力的外部作业时，宜通过工程类比或相似地层中的压力控制试验，合理确定压力控制参数，使作用于既有结构侧壁上的附加荷载不大于 $20\\mathrm{kPa}$ 。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_8',
 'clause': '4.4.8',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '过江（河、湖）段城市轨道交通控制保护区内不应进行采砂、抛锚或拖锚等水下作业，水下清淤疏浚作业应保证城市轨道交通结构上方覆土厚度不小于设计要求。',
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
 'requirements': ['过江（河、湖）段城市轨道交通控制保护区内不应进行采砂、抛锚或拖锚等水下作业，水下清淤疏浚作业应保证城市轨道交通结构上方覆土厚度不小于设计要求。'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.8 过江（河、湖）段城市轨道交通控制保护区内不应进行采砂、抛锚或拖锚等水下作业，水下清淤疏浚作业应保证城市轨道交通结构上方覆土厚度不小于设计要求。."""

    return _evaluate_clause(
        clause='4.4.8',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='过江（河、湖）段城市轨道交通控制保护区内不应进行采砂、抛锚或拖锚等水下作业，水下清淤疏浚作业应保证城市轨道交通结构上方覆土厚度不小于设计要求。',
        basis='4.4.8 过江（河、湖）段城市轨道交通控制保护区内不应进行采砂、抛锚或拖锚等水下作业，水下清淤疏浚作业应保证城市轨道交通结构上方覆土厚度不小于设计要求。',
        requirements=['过江（河、湖）段城市轨道交通控制保护区内不应进行采砂、抛锚或拖锚等水下作业，水下清淤疏浚作业应保证城市轨道交通结构上方覆土厚度不小于设计要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_4_9_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_4_9',
 'clause': '4.4.9',
 'chapter': '既有结构保护',
 'section': '4.4 地下结构保护',
 'title': '临近城市轨道交通地下车站、敞口段的外部作业应采取有效的防淹、排涝措施，避免施工期间外部水源进入轨道交通地下空间内。',
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
 'requirements': ['临近城市轨道交通地下车站、敞口段的外部作业应采取有效的防淹、排涝措施，避免施工期间外部水源进入轨道交通地下空间内。 # 4.5 地面和高架结构保护'],
 'output': OUTPUT_SCHEMA}


def clause_4_4_9(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.4.9 临近城市轨道交通地下车站、敞口段的外部作业应采取有效的防淹、排涝措施，避免施工期间外部水源进入轨道交通地下空间内。."""

    return _evaluate_clause(
        clause='4.4.9',
        chapter='既有结构保护',
        section='4.4 地下结构保护',
        title='临近城市轨道交通地下车站、敞口段的外部作业应采取有效的防淹、排涝措施，避免施工期间外部水源进入轨道交通地下空间内。',
        basis='4.4.9 临近城市轨道交通地下车站、敞口段的外部作业应采取有效的防淹、排涝措施，避免施工期间外部水源进入轨道交通地下空间内。 # 4.5 地面和高架结构保护',
        requirements=['临近城市轨道交通地下车站、敞口段的外部作业应采取有效的防淹、排涝措施，避免施工期间外部水源进入轨道交通地下空间内。 # 4.5 地面和高架结构保护'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_1',
 'clause': '4.5.1',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '外部作业禁止施工侵限、车辆碰撞、设备侧翻、物体坠入，并应防止火灾、水淹等危及城市轨道交通结构和设备设施安全的事件。',
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
 'requirements': ['外部作业禁止施工侵限、车辆碰撞、设备侧翻、物体坠入，并应防止火灾、水淹等危及城市轨道交通结构和设备设施安全的事件。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.1 外部作业禁止施工侵限、车辆碰撞、设备侧翻、物体坠入，并应防止火灾、水淹等危及城市轨道交通结构和设备设施安全的事件。."""

    return _evaluate_clause(
        clause='4.5.1',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='外部作业禁止施工侵限、车辆碰撞、设备侧翻、物体坠入，并应防止火灾、水淹等危及城市轨道交通结构和设备设施安全的事件。',
        basis='4.5.1 外部作业禁止施工侵限、车辆碰撞、设备侧翻、物体坠入，并应防止火灾、水淹等危及城市轨道交通结构和设备设施安全的事件。',
        requirements=['外部作业禁止施工侵限、车辆碰撞、设备侧翻、物体坠入，并应防止火灾、水淹等危及城市轨道交通结构和设备设施安全的事件。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_2',
 'clause': '4.5.2',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '上跨城市轨道交通地面或高架结构的外部作业，与轨道及接触网等的净空应满足行车安全和运营维保的要求，并应针对轨道交通结构和行车安全设置防护措施，严禁物体坠入轨行区。',
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
 'requirements': ['上跨城市轨道交通地面或高架结构的外部作业，与轨道及接触网等的净空应满足行车安全和运营维保的要求，并应针对轨道交通结构和行车安全设置防护措施，严禁物体坠入轨行区。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.2 上跨城市轨道交通地面或高架结构的外部作业，与轨道及接触网等的净空应满足行车安全和运营维保的要求，并应针对轨道交通结构和行车安全设置防护措施，严禁物体坠入轨行区。."""

    return _evaluate_clause(
        clause='4.5.2',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='上跨城市轨道交通地面或高架结构的外部作业，与轨道及接触网等的净空应满足行车安全和运营维保的要求，并应针对轨道交通结构和行车安全设置防护措施，严禁物体坠入轨行区。',
        basis='4.5.2 上跨城市轨道交通地面或高架结构的外部作业，与轨道及接触网等的净空应满足行车安全和运营维保的要求，并应针对轨道交通结构和行车安全设置防护措施，严禁物体坠入轨行区。',
        requirements=['上跨城市轨道交通地面或高架结构的外部作业，与轨道及接触网等的净空应满足行车安全和运营维保的要求，并应针对轨道交通结构和行车安全设置防护措施，严禁物体坠入轨行区。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_3',
 'clause': '4.5.3',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '与城市轨道交通地面或高架结构交叉的市政道路应设置限高标志和防护、防撞设施。',
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
 'requirements': ['与城市轨道交通地面或高架结构交叉的市政道路应设置限高标志和防护、防撞设施。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.3 与城市轨道交通地面或高架结构交叉的市政道路应设置限高标志和防护、防撞设施。."""

    return _evaluate_clause(
        clause='4.5.3',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='与城市轨道交通地面或高架结构交叉的市政道路应设置限高标志和防护、防撞设施。',
        basis='4.5.3 与城市轨道交通地面或高架结构交叉的市政道路应设置限高标志和防护、防撞设施。',
        requirements=['与城市轨道交通地面或高架结构交叉的市政道路应设置限高标志和防护、防撞设施。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_4',
 'clause': '4.5.4',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '与城市轨道交通地面或高架结构并行的桥梁等交通设施，应保持足够的安全距离或设置通长的防撞墙。',
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
 'requirements': ['与城市轨道交通地面或高架结构并行的桥梁等交通设施，应保持足够的安全距离或设置通长的防撞墙。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.4 与城市轨道交通地面或高架结构并行的桥梁等交通设施，应保持足够的安全距离或设置通长的防撞墙。."""

    return _evaluate_clause(
        clause='4.5.4',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='与城市轨道交通地面或高架结构并行的桥梁等交通设施，应保持足够的安全距离或设置通长的防撞墙。',
        basis='4.5.4 与城市轨道交通地面或高架结构并行的桥梁等交通设施，应保持足够的安全距离或设置通长的防撞墙。',
        requirements=['与城市轨道交通地面或高架结构并行的桥梁等交通设施，应保持足够的安全距离或设置通长的防撞墙。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_5',
 'clause': '4.5.5',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '当城市轨道交通结构邻近高边坡、高挡墙、高压铁塔等高大建（构）筑物时，外部作业应保证高大建（构）筑物及其基础的安全。',
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
 'requirements': ['当城市轨道交通结构邻近高边坡、高挡墙、高压铁塔等高大建（构）筑物时，外部作业应保证高大建（构）筑物及其基础的安全。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.5 当城市轨道交通结构邻近高边坡、高挡墙、高压铁塔等高大建（构）筑物时，外部作业应保证高大建（构）筑物及其基础的安全。."""

    return _evaluate_clause(
        clause='4.5.5',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='当城市轨道交通结构邻近高边坡、高挡墙、高压铁塔等高大建（构）筑物时，外部作业应保证高大建（构）筑物及其基础的安全。',
        basis='4.5.5 当城市轨道交通结构邻近高边坡、高挡墙、高压铁塔等高大建（构）筑物时，外部作业应保证高大建（构）筑物及其基础的安全。',
        requirements=['当城市轨道交通结构邻近高边坡、高挡墙、高压铁塔等高大建（构）筑物时，外部作业应保证高大建（构）筑物及其基础的安全。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_6',
 'clause': '4.5.6',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '城市轨道交通地面或高架结构上方进行跨线架空作业时，应满足本规程3.3.1条和现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～75',
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
 'requirements': ['城市轨道交通地面或高架结构上方进行跨线架空作业时，应满足本规程3.3.1条和现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》GB50545的有关规定。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.6 城市轨道交通地面或高架结构上方进行跨线架空作业时，应满足本规程3.3.1条和现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～75."""

    return _evaluate_clause(
        clause='4.5.6',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='城市轨道交通地面或高架结构上方进行跨线架空作业时，应满足本规程3.3.1条和现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～75',
        basis='4.5.6 城市轨道交通地面或高架结构上方进行跨线架空作业时，应满足本规程3.3.1条和现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》GB50545的有关规定。',
        requirements=['城市轨道交通地面或高架结构上方进行跨线架空作业时，应满足本规程3.3.1条和现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》GB50545的有关规定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_7',
 'clause': '4.5.7',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '在水域段临近城市轨道交通高架结构进行外部作业时，应采取有效措施避免撞击水中桥墩和桥面结构。',
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
 'requirements': ['在水域段临近城市轨道交通高架结构进行外部作业时，应采取有效措施避免撞击水中桥墩和桥面结构。'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.7 在水域段临近城市轨道交通高架结构进行外部作业时，应采取有效措施避免撞击水中桥墩和桥面结构。."""

    return _evaluate_clause(
        clause='4.5.7',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='在水域段临近城市轨道交通高架结构进行外部作业时，应采取有效措施避免撞击水中桥墩和桥面结构。',
        basis='4.5.7 在水域段临近城市轨道交通高架结构进行外部作业时，应采取有效措施避免撞击水中桥墩和桥面结构。',
        requirements=['在水域段临近城市轨道交通高架结构进行外部作业时，应采取有效措施避免撞击水中桥墩和桥面结构。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_4_5_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_4_5_8',
 'clause': '4.5.8',
 'chapter': '既有结构保护',
 'section': '4.5 地面和高架结构保护',
 'title': '外部作业实施完成后，还应考虑建（构）筑物使用阶段对城市轨道交通运营可能产生的影响，并采取对应的安全防护措施。',
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
 'requirements': ['外部作业实施完成后，还应考虑建（构）筑物使用阶段对城市轨道交通运营可能产生的影响，并采取对应的安全防护措施。 # 5 外部作业控制 # 5.1 一般规定'],
 'output': OUTPUT_SCHEMA}


def clause_4_5_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """4.5.8 外部作业实施完成后，还应考虑建（构）筑物使用阶段对城市轨道交通运营可能产生的影响，并采取对应的安全防护措施。."""

    return _evaluate_clause(
        clause='4.5.8',
        chapter='既有结构保护',
        section='4.5 地面和高架结构保护',
        title='外部作业实施完成后，还应考虑建（构）筑物使用阶段对城市轨道交通运营可能产生的影响，并采取对应的安全防护措施。',
        basis='4.5.8 外部作业实施完成后，还应考虑建（构）筑物使用阶段对城市轨道交通运营可能产生的影响，并采取对应的安全防护措施。 # 5 外部作业控制 # 5.1 一般规定',
        requirements=['外部作业实施完成后，还应考虑建（构）筑物使用阶段对城市轨道交通运营可能产生的影响，并采取对应的安全防护措施。 # 5 外部作业控制 # 5.1 一般规定'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_4_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_4_functions",
    "chapter": '既有结构保护',
    "description": "DB32/T 4351-2022 chapter 4 clause function API schema.",
    "functions": {
        "clause_4_1_1": CLAUSE_4_1_1_INPUT_SCHEMA,
        "clause_4_1_2": CLAUSE_4_1_2_INPUT_SCHEMA,
        "clause_4_1_3": CLAUSE_4_1_3_INPUT_SCHEMA,
        "clause_4_1_4": CLAUSE_4_1_4_INPUT_SCHEMA,
        "clause_4_2_1": CLAUSE_4_2_1_INPUT_SCHEMA,
        "clause_4_2_2": CLAUSE_4_2_2_INPUT_SCHEMA,
        "clause_4_2_3": CLAUSE_4_2_3_INPUT_SCHEMA,
        "clause_4_2_4": CLAUSE_4_2_4_INPUT_SCHEMA,
        "clause_4_2_5": CLAUSE_4_2_5_INPUT_SCHEMA,
        "clause_4_2_6": CLAUSE_4_2_6_INPUT_SCHEMA,
        "clause_4_2_7": CLAUSE_4_2_7_INPUT_SCHEMA,
        "clause_4_2_8": CLAUSE_4_2_8_INPUT_SCHEMA,
        "clause_4_3_1": CLAUSE_4_3_1_INPUT_SCHEMA,
        "clause_4_3_2": CLAUSE_4_3_2_INPUT_SCHEMA,
        "clause_4_3_3": CLAUSE_4_3_3_INPUT_SCHEMA,
        "clause_4_3_4": CLAUSE_4_3_4_INPUT_SCHEMA,
        "clause_4_3_5": CLAUSE_4_3_5_INPUT_SCHEMA,
        "clause_4_3_6": CLAUSE_4_3_6_INPUT_SCHEMA,
        "clause_4_4_1": CLAUSE_4_4_1_INPUT_SCHEMA,
        "clause_4_4_2": CLAUSE_4_4_2_INPUT_SCHEMA,
        "clause_4_4_3": CLAUSE_4_4_3_INPUT_SCHEMA,
        "clause_4_4_4": CLAUSE_4_4_4_INPUT_SCHEMA,
        "clause_4_4_5": CLAUSE_4_4_5_INPUT_SCHEMA,
        "clause_4_4_6": CLAUSE_4_4_6_INPUT_SCHEMA,
        "clause_4_4_7": CLAUSE_4_4_7_INPUT_SCHEMA,
        "clause_4_4_8": CLAUSE_4_4_8_INPUT_SCHEMA,
        "clause_4_4_9": CLAUSE_4_4_9_INPUT_SCHEMA,
        "clause_4_5_1": CLAUSE_4_5_1_INPUT_SCHEMA,
        "clause_4_5_2": CLAUSE_4_5_2_INPUT_SCHEMA,
        "clause_4_5_3": CLAUSE_4_5_3_INPUT_SCHEMA,
        "clause_4_5_4": CLAUSE_4_5_4_INPUT_SCHEMA,
        "clause_4_5_5": CLAUSE_4_5_5_INPUT_SCHEMA,
        "clause_4_5_6": CLAUSE_4_5_6_INPUT_SCHEMA,
        "clause_4_5_7": CLAUSE_4_5_7_INPUT_SCHEMA,
        "clause_4_5_8": CLAUSE_4_5_8_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_4_1_1(confirmed_items=['在城市轨道交通控制保护区内从事外部作业时，应事先开展现状调查、地质条件及环境调查，并制定结构安全保护方案。'], strict=False)
    print(first.to_dict())
