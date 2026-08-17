"""Functions for Chapter 3 of DB32/T 4351-2022.

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

CLAUSE_3_1_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_1',
 'clause': '3.1.1',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。',
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
 'requirements': ['城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.1 城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。."""

    return _evaluate_clause(
        clause='3.1.1',
        chapter='基本规定',
        section='3.1 一般规定',
        title='城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。',
        basis='3.1.1 城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。',
        requirements=['城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_2',
 'clause': '3.1.2',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '城市轨道交通结构安全保护工作应利用数字化技术手段搭建信息化管理平台。信息化管理平台应实现巡查、项目管理、安全监测及应急处置等各类数据的互联互通与共享。',
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
 'requirements': ['城市轨道交通结构安全保护工作应利用数字化技术手段搭建信息化管理平台。信息化管理平台应实现巡查、项目管理、安全监测及应急处置等各类数据的互联互通与共享。'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.2 城市轨道交通结构安全保护工作应利用数字化技术手段搭建信息化管理平台。信息化管理平台应实现巡查、项目管理、安全监测及应急处置等各类数据的互联互通与共享。."""

    return _evaluate_clause(
        clause='3.1.2',
        chapter='基本规定',
        section='3.1 一般规定',
        title='城市轨道交通结构安全保护工作应利用数字化技术手段搭建信息化管理平台。信息化管理平台应实现巡查、项目管理、安全监测及应急处置等各类数据的互联互通与共享。',
        basis='3.1.2 城市轨道交通结构安全保护工作应利用数字化技术手段搭建信息化管理平台。信息化管理平台应实现巡查、项目管理、安全监测及应急处置等各类数据的互联互通与共享。',
        requirements=['城市轨道交通结构安全保护工作应利用数字化技术手段搭建信息化管理平台。信息化管理平台应实现巡查、项目管理、安全监测及应急处置等各类数据的互联互通与共享。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_3',
 'clause': '3.1.3',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '在城市轨道交通周边进行外部作业时，应制定安全可靠的作业方案和保护措施，外部作业不得影响城市轨道交通结构的承载能力、正常使用、耐久性和其他特殊功能。',
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
 'requirements': ['在城市轨道交通周边进行外部作业时，应制定安全可靠的作业方案和保护措施，外部作业不得影响城市轨道交通结构的承载能力、正常使用、耐久性和其他特殊功能。'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.3 在城市轨道交通周边进行外部作业时，应制定安全可靠的作业方案和保护措施，外部作业不得影响城市轨道交通结构的承载能力、正常使用、耐久性和其他特殊功能。."""

    return _evaluate_clause(
        clause='3.1.3',
        chapter='基本规定',
        section='3.1 一般规定',
        title='在城市轨道交通周边进行外部作业时，应制定安全可靠的作业方案和保护措施，外部作业不得影响城市轨道交通结构的承载能力、正常使用、耐久性和其他特殊功能。',
        basis='3.1.3 在城市轨道交通周边进行外部作业时，应制定安全可靠的作业方案和保护措施，外部作业不得影响城市轨道交通结构的承载能力、正常使用、耐久性和其他特殊功能。',
        requirements=['在城市轨道交通周边进行外部作业时，应制定安全可靠的作业方案和保护措施，外部作业不得影响城市轨道交通结构的承载能力、正常使用、耐久性和其他特殊功能。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_4',
 'clause': '3.1.4',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '城市轨道交通沿线应设置控制保护区，设置范围应符合下列规定：',
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
 'requirements': ['城市轨道交通沿线应设置控制保护区，设置范围应符合下列规定： 1 地下车站与隧道结构外边线外侧不小于 $50\\mathrm{m}$ ，其中，过江（河、湖）段隧道结构外边线外侧不小于 '
                  '$100\\mathrm{m}$ 。 2 地面和高架车站、路基和桥梁结构外边线外侧不小于 $30\\mathrm{m}$ 。 3 '
                  '附属建（构）筑物（含出入口、换乘通道、通风道、冷却塔和变电站等）结构外边线及车辆基地用地范围外侧不小于 $10\\mathrm{m}$ '],
 'output': OUTPUT_SCHEMA}


def clause_3_1_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.4 城市轨道交通沿线应设置控制保护区，设置范围应符合下列规定：."""

    return _evaluate_clause(
        clause='3.1.4',
        chapter='基本规定',
        section='3.1 一般规定',
        title='城市轨道交通沿线应设置控制保护区，设置范围应符合下列规定：',
        basis='3.1.4 城市轨道交通沿线应设置控制保护区，设置范围应符合下列规定： 1 地下车站与隧道结构外边线外侧不小于 $50\\mathrm{m}$ ，其中，过江（河、湖）段隧道结构外边线外侧不小于 $100\\mathrm{m}$ 。 2 地面和高架车站、路基和桥梁结构外边线外侧不小于 $30\\mathrm{m}$ 。 3 附属建（构）筑物（含出入口、换乘通道、通风道、冷却塔和变电站等）结构外边线及车辆基地用地范围外侧不小于 $10\\mathrm{m}$ 。',
        requirements=['城市轨道交通沿线应设置控制保护区，设置范围应符合下列规定： 1 地下车站与隧道结构外边线外侧不小于 $50\\mathrm{m}$ ，其中，过江（河、湖）段隧道结构外边线外侧不小于 $100\\mathrm{m}$ 。 2 地面和高架车站、路基和桥梁结构外边线外侧不小于 $30\\mathrm{m}$ 。 3 附属建（构）筑物（含出入口、换乘通道、通风道、冷却塔和变电站等）结构外边线及车辆基地用地范围外侧不小于 $10\\mathrm{m}$ '],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_5',
 'clause': '3.1.5',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '在城市轨道交通控制保护区范围内应设置特别保护区，设置范围应符合下列规定：',
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
 'requirements': ['在城市轨道交通控制保护区范围内应设置特别保护区，设置范围应符合下列规定： 1 地下车站与隧道结构外边线外侧不小于 $5\\mathrm{m}$ ，其中，过江（河、湖）段隧道结构外边线不小于 '
                  '$50\\mathrm{m}$ 。 2 地面和高架车站、路基和桥梁结构外边线外侧不小于 $3 \\mathrm{~m}$ 。 3. '
                  '附属建（构）筑物（含出入口、换乘通道、通风道、冷却塔和变电站等）结构外边线及车辆基地用地范围外侧不小于 $5\\mathrm{'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.5 在城市轨道交通控制保护区范围内应设置特别保护区，设置范围应符合下列规定：."""

    return _evaluate_clause(
        clause='3.1.5',
        chapter='基本规定',
        section='3.1 一般规定',
        title='在城市轨道交通控制保护区范围内应设置特别保护区，设置范围应符合下列规定：',
        basis='3.1.5 在城市轨道交通控制保护区范围内应设置特别保护区，设置范围应符合下列规定： 1 地下车站与隧道结构外边线外侧不小于 $5\\mathrm{m}$ ，其中，过江（河、湖）段隧道结构外边线不小于 $50\\mathrm{m}$ 。 2 地面和高架车站、路基和桥梁结构外边线外侧不小于 $3 \\mathrm{~m}$ 。 3. 附属建（构）筑物（含出入口、换乘通道、通风道、冷却塔和变电站等）结构外边线及车辆基地用地范围外侧不小于 $5\\mathrm{m}$ 。',
        requirements=['在城市轨道交通控制保护区范围内应设置特别保护区，设置范围应符合下列规定： 1 地下车站与隧道结构外边线外侧不小于 $5\\mathrm{m}$ ，其中，过江（河、湖）段隧道结构外边线不小于 $50\\mathrm{m}$ 。 2 地面和高架车站、路基和桥梁结构外边线外侧不小于 $3 \\mathrm{~m}$ 。 3. 附属建（构）筑物（含出入口、换乘通道、通风道、冷却塔和变电站等）结构外边线及车辆基地用地范围外侧不小于 $5\\mathrm{'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_6',
 'clause': '3.1.6',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '遇特殊工程地质和水文地质、特殊的外部作业或既有结构存在较大结构病害时，城市轨道交通控制保护区和特别保护区范围可适当扩大。',
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
 'requirements': ['遇特殊工程地质和水文地质、特殊的外部作业或既有结构存在较大结构病害时，城市轨道交通控制保护区和特别保护区范围可适当扩大。'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.6 遇特殊工程地质和水文地质、特殊的外部作业或既有结构存在较大结构病害时，城市轨道交通控制保护区和特别保护区范围可适当扩大。."""

    return _evaluate_clause(
        clause='3.1.6',
        chapter='基本规定',
        section='3.1 一般规定',
        title='遇特殊工程地质和水文地质、特殊的外部作业或既有结构存在较大结构病害时，城市轨道交通控制保护区和特别保护区范围可适当扩大。',
        basis='3.1.6 遇特殊工程地质和水文地质、特殊的外部作业或既有结构存在较大结构病害时，城市轨道交通控制保护区和特别保护区范围可适当扩大。',
        requirements=['遇特殊工程地质和水文地质、特殊的外部作业或既有结构存在较大结构病害时，城市轨道交通控制保护区和特别保护区范围可适当扩大。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_7_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_7',
 'clause': '3.1.7',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '城市轨道交通线网中相邻线路分期建设时，先建工程应充分考虑后建工程的建设影响及需要，为后建工程预留实施条件。',
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
 'requirements': ['城市轨道交通线网中相邻线路分期建设时，先建工程应充分考虑后建工程的建设影响及需要，为后建工程预留实施条件。 '
                  '注：1.本表适用于围岩级别为IV、V的情况；围岩级别为I～Ⅲ的情况，表中的影响等级可降低一级，四级以下仍定为四级；软土地区，表中的影响等级应提高一级，特级时不再提高。'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_7(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.7 城市轨道交通线网中相邻线路分期建设时，先建工程应充分考虑后建工程的建设影响及需要，为后建工程预留实施条件。."""

    return _evaluate_clause(
        clause='3.1.7',
        chapter='基本规定',
        section='3.1 一般规定',
        title='城市轨道交通线网中相邻线路分期建设时，先建工程应充分考虑后建工程的建设影响及需要，为后建工程预留实施条件。',
        basis='3.1.7 城市轨道交通线网中相邻线路分期建设时，先建工程应充分考虑后建工程的建设影响及需要，为后建工程预留实施条件。 注：1.本表适用于围岩级别为IV、V的情况；围岩级别为I～Ⅲ的情况，表中的影响等级可降低一级，四级以下仍定为四级；软土地区，表中的影响等级应提高一级，特级时不再提高。',
        requirements=['城市轨道交通线网中相邻线路分期建设时，先建工程应充分考虑后建工程的建设影响及需要，为后建工程预留实施条件。 注：1.本表适用于围岩级别为IV、V的情况；围岩级别为I～Ⅲ的情况，表中的影响等级可降低一级，四级以下仍定为四级；软土地区，表中的影响等级应提高一级，特级时不再提高。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_1_8_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_1_8',
 'clause': '3.1.8',
 'chapter': '基本规定',
 'section': '3.1 一般规定',
 'title': '城市轨道交通结构的安全控制应包括：外部作业影响等级、外部作业净距控制值、结构安全控制指标。',
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
 'requirements': ['城市轨道交通结构的安全控制应包括：外部作业影响等级、外部作业净距控制值、结构安全控制指标。 # 3.2 外部作业影响等级'],
 'output': OUTPUT_SCHEMA}


def clause_3_1_8(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.1.8 城市轨道交通结构的安全控制应包括：外部作业影响等级、外部作业净距控制值、结构安全控制指标。."""

    return _evaluate_clause(
        clause='3.1.8',
        chapter='基本规定',
        section='3.1 一般规定',
        title='城市轨道交通结构的安全控制应包括：外部作业影响等级、外部作业净距控制值、结构安全控制指标。',
        basis='3.1.8 城市轨道交通结构的安全控制应包括：外部作业影响等级、外部作业净距控制值、结构安全控制指标。 # 3.2 外部作业影响等级',
        requirements=['城市轨道交通结构的安全控制应包括：外部作业影响等级、外部作业净距控制值、结构安全控制指标。 # 3.2 外部作业影响等级'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_2_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_2_1',
 'clause': '3.2.1',
 'chapter': '基本规定',
 'section': '3.2 外部作业影响等级',
 'title': '外部作业影响等级应综合考虑其作业特点、与城市轨道交通结构的空间关系、轨道交通结构类型及现状、工程地质与水文地质条件等后确定。',
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
 'requirements': ['外部作业影响等级应综合考虑其作业特点、与城市轨道交通结构的空间关系、轨道交通结构类型及现状、工程地质与水文地质条件等后确定。'],
 'output': OUTPUT_SCHEMA}


def clause_3_2_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.2.1 外部作业影响等级应综合考虑其作业特点、与城市轨道交通结构的空间关系、轨道交通结构类型及现状、工程地质与水文地质条件等后确定。."""

    return _evaluate_clause(
        clause='3.2.1',
        chapter='基本规定',
        section='3.2 外部作业影响等级',
        title='外部作业影响等级应综合考虑其作业特点、与城市轨道交通结构的空间关系、轨道交通结构类型及现状、工程地质与水文地质条件等后确定。',
        basis='3.2.1 外部作业影响等级应综合考虑其作业特点、与城市轨道交通结构的空间关系、轨道交通结构类型及现状、工程地质与水文地质条件等后确定。',
        requirements=['外部作业影响等级应综合考虑其作业特点、与城市轨道交通结构的空间关系、轨道交通结构类型及现状、工程地质与水文地质条件等后确定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_2_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_2_2',
 'clause': '3.2.2',
 'chapter': '基本规定',
 'section': '3.2 外部作业影响等级',
 'title': '外部作业为基坑工程、隧道工程（矿山法、盾构法或顶管法工程）等时，其影响等级应按表3.2.2进行划分，其中接近程度和外部作业工程影响分区宜按本规程附录A确定。',
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
 'requirements': ['外部作业为基坑工程、隧道工程（矿山法、盾构法或顶管法工程）等时，其影响等级应按表3.2.2进行划分，其中接近程度和外部作业工程影响分区宜按本规程附录A确定。 表 3.2.2 外部作业影响等级的划分 '
                  '外部作业的工程影响分区接近程度非常接近接近较接近不接近强烈影响区(A)特级特级一级二级显著影响区(B)特级一级二级三级一般影响区(C)一级二级三级四级较小影响区(D)二级三级四级四级 2. '
                  '围岩级别应按现行标准《城市轨道交通岩土工程勘察规范》'],
 'output': OUTPUT_SCHEMA}


def clause_3_2_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.2.2 外部作业为基坑工程、隧道工程（矿山法、盾构法或顶管法工程）等时，其影响等级应按表3.2.2进行划分，其中接近程度和外部作业工程影响分区宜按本规程附录A确定。."""

    return _evaluate_clause(
        clause='3.2.2',
        chapter='基本规定',
        section='3.2 外部作业影响等级',
        title='外部作业为基坑工程、隧道工程（矿山法、盾构法或顶管法工程）等时，其影响等级应按表3.2.2进行划分，其中接近程度和外部作业工程影响分区宜按本规程附录A确定。',
        basis='3.2.2 外部作业为基坑工程、隧道工程（矿山法、盾构法或顶管法工程）等时，其影响等级应按表3.2.2进行划分，其中接近程度和外部作业工程影响分区宜按本规程附录A确定。 表 3.2.2 外部作业影响等级的划分 外部作业的工程影响分区接近程度非常接近接近较接近不接近强烈影响区(A)特级特级一级二级显著影响区(B)特级一级二级三级一般影响区(C)一级二级三级四级较小影响区(D)二级三级四级四级 2. 围岩级别应按现行标准《城市轨道交通岩土工程勘察规范》GB50307中的有关规定确定。',
        requirements=['外部作业为基坑工程、隧道工程（矿山法、盾构法或顶管法工程）等时，其影响等级应按表3.2.2进行划分，其中接近程度和外部作业工程影响分区宜按本规程附录A确定。 表 3.2.2 外部作业影响等级的划分 外部作业的工程影响分区接近程度非常接近接近较接近不接近强烈影响区(A)特级特级一级二级显著影响区(B)特级一级二级三级一般影响区(C)一级二级三级四级较小影响区(D)二级三级四级四级 2. 围岩级别应按现行标准《城市轨道交通岩土工程勘察规范》'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_2_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_2_3',
 'clause': '3.2.3',
 'chapter': '基本规定',
 'section': '3.2 外部作业影响等级',
 'title': '外部作业为其他工程（道路及地下管线工程等）时，其影响等级宜根据城市轨道交通的结构类型、外部作业与轨道交通结构的空间关系，参照附录B确定。采用明挖法的管线工程可参',
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
 'requirements': ['外部作业为其他工程（道路及地下管线工程等）时，其影响等级宜根据城市轨道交通的结构类型、外部作业与轨道交通结构的空间关系，参照附录B确定。采用明挖法的管线工程可参照基坑工程进行分级。'],
 'output': OUTPUT_SCHEMA}


def clause_3_2_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.2.3 外部作业为其他工程（道路及地下管线工程等）时，其影响等级宜根据城市轨道交通的结构类型、外部作业与轨道交通结构的空间关系，参照附录B确定。采用明挖法的管线工程可参."""

    return _evaluate_clause(
        clause='3.2.3',
        chapter='基本规定',
        section='3.2 外部作业影响等级',
        title='外部作业为其他工程（道路及地下管线工程等）时，其影响等级宜根据城市轨道交通的结构类型、外部作业与轨道交通结构的空间关系，参照附录B确定。采用明挖法的管线工程可参',
        basis='3.2.3 外部作业为其他工程（道路及地下管线工程等）时，其影响等级宜根据城市轨道交通的结构类型、外部作业与轨道交通结构的空间关系，参照附录B确定。采用明挖法的管线工程可参照基坑工程进行分级。',
        requirements=['外部作业为其他工程（道路及地下管线工程等）时，其影响等级宜根据城市轨道交通的结构类型、外部作业与轨道交通结构的空间关系，参照附录B确定。采用明挖法的管线工程可参照基坑工程进行分级。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_2_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_2_4',
 'clause': '3.2.4',
 'chapter': '基本规定',
 'section': '3.2 外部作业影响等级',
 'title': '当外部作业影响范围内存在多种类型的城市轨道交通结构时，可根据结构类型的不同，分别确定影响等级，并取其较高等级作为工程影响等级。',
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
 'requirements': ['当外部作业影响范围内存在多种类型的城市轨道交通结构时，可根据结构类型的不同，分别确定影响等级，并取其较高等级作为工程影响等级。'],
 'output': OUTPUT_SCHEMA}


def clause_3_2_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.2.4 当外部作业影响范围内存在多种类型的城市轨道交通结构时，可根据结构类型的不同，分别确定影响等级，并取其较高等级作为工程影响等级。."""

    return _evaluate_clause(
        clause='3.2.4',
        chapter='基本规定',
        section='3.2 外部作业影响等级',
        title='当外部作业影响范围内存在多种类型的城市轨道交通结构时，可根据结构类型的不同，分别确定影响等级，并取其较高等级作为工程影响等级。',
        basis='3.2.4 当外部作业影响范围内存在多种类型的城市轨道交通结构时，可根据结构类型的不同，分别确定影响等级，并取其较高等级作为工程影响等级。',
        requirements=['当外部作业影响范围内存在多种类型的城市轨道交通结构时，可根据结构类型的不同，分别确定影响等级，并取其较高等级作为工程影响等级。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_2_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_2_5',
 'clause': '3.2.5',
 'chapter': '基本规定',
 'section': '3.2 外部作业影响等级',
 'title': '特殊情况下外部作业影响等级按下列原则调整：',
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
 'requirements': ['当城市轨道交通结构处于复杂的工程地质和水文地质条件或存在地质灾害的情况时，外部作业影响等级应提高一级。',
                  '对于涉及抽降承压水的外部作业工程，其影响等级应提高一级。',
                  '联络通道等结构特殊区段、结构病害严重或结构变形较大时，外部作业影响等级可提高一级。'],
 'output': OUTPUT_SCHEMA}


def clause_3_2_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.2.5 特殊情况下外部作业影响等级按下列原则调整：."""

    return _evaluate_clause(
        clause='3.2.5',
        chapter='基本规定',
        section='3.2 外部作业影响等级',
        title='特殊情况下外部作业影响等级按下列原则调整：',
        basis='3.2.5 特殊情况下外部作业影响等级按下列原则调整： 1 当城市轨道交通结构处于复杂的工程地质和水文地质条件或存在地质灾害的情况时，外部作业影响等级应提高一级。 2 对于涉及抽降承压水的外部作业工程，其影响等级应提高一级。 3 联络通道等结构特殊区段、结构病害严重或结构变形较大时，外部作业影响等级可提高一级。 4 当基坑深度超过 $5\\mathrm{m}$ ，若临近城市轨道交通结构侧边长超 $100\\mathrm{m}$ 或开挖面积超 $10000\\mathrm{m}^2$ ，其影响等级可提高一级。',
        requirements=['当城市轨道交通结构处于复杂的工程地质和水文地质条件或存在地质灾害的情况时，外部作业影响等级应提高一级。', '对于涉及抽降承压水的外部作业工程，其影响等级应提高一级。', '联络通道等结构特殊区段、结构病害严重或结构变形较大时，外部作业影响等级可提高一级。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_2_6_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_2_6',
 'clause': '3.2.6',
 'chapter': '基本规定',
 'section': '3.2 外部作业影响等级',
 'title': '重大影响外部作业指对城市轨道交通结构安全有重大影响的项目，主要包括：',
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
 'requirements': ['影响等级划分为特级、一级的外部作业。',
                  '影响等级为二级的外部作业，但轨道交通结构周边土体以淤泥、淤泥质土或其他高压缩性土为主或轨道交通结构处于断裂破碎带、岩溶、土洞、松散岩土体等不良地质体或特殊性岩土发育区域。',
                  '对城市轨道交通结构影响较大的地下水作业，特别是抽降承压水作业。'],
 'output': OUTPUT_SCHEMA}


def clause_3_2_6(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.2.6 重大影响外部作业指对城市轨道交通结构安全有重大影响的项目，主要包括：."""

    return _evaluate_clause(
        clause='3.2.6',
        chapter='基本规定',
        section='3.2 外部作业影响等级',
        title='重大影响外部作业指对城市轨道交通结构安全有重大影响的项目，主要包括：',
        basis='3.2.6 重大影响外部作业指对城市轨道交通结构安全有重大影响的项目，主要包括： 1 影响等级划分为特级、一级的外部作业。 2 影响等级为二级的外部作业，但轨道交通结构周边土体以淤泥、淤泥质土或其他高压缩性土为主或轨道交通结构处于断裂破碎带、岩溶、土洞、松散岩土体等不良地质体或特殊性岩土发育区域。 3 对城市轨道交通结构影响较大的地下水作业，特别是抽降承压水作业。 4 穿越轨道交通地下结构的作业，不含尺寸及埋深较小的明挖小型管沟、明渠及牵引拖拉管等交叉作业。 # 3.3 外部作业净距控制值',
        requirements=['影响等级划分为特级、一级的外部作业。', '影响等级为二级的外部作业，但轨道交通结构周边土体以淤泥、淤泥质土或其他高压缩性土为主或轨道交通结构处于断裂破碎带、岩溶、土洞、松散岩土体等不良地质体或特殊性岩土发育区域。', '对城市轨道交通结构影响较大的地下水作业，特别是抽降承压水作业。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_3_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_3_1',
 'clause': '3.3.1',
 'chapter': '基本规定',
 'section': '3.3 外部作业净距控制值',
 'title': '外部作业净距控制值宜符合表3.3.1的规定。',
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
 'requirements': ['外部作业净距控制值宜符合表3.3.1的规定。 表 3.3.1 外部作业净距控制值 单位：m '
                  '外部作业轨道交通结构类型地下结构地面结构高架结构装配式现浇围护桩、地下连续墙*≥7.0≥5.0≥5.0≥5.0工程桩*非挤土桩≥5.0≥3.0≥3.0≥3.0挤土桩≥30.0≥20.0≥6.0≥6.0锚杆、锚索、土钉(末端)*≥10.0≥6.0≥6.0≥6.0上方基坑#≥4.0---穿越隧道#≥2.0---钻探孔*≥6.0≥3.0≥3.0≥3.0'],
 'output': OUTPUT_SCHEMA}


def clause_3_3_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.3.1 外部作业净距控制值宜符合表3.3.1的规定。."""

    return _evaluate_clause(
        clause='3.3.1',
        chapter='基本规定',
        section='3.3 外部作业净距控制值',
        title='外部作业净距控制值宜符合表3.3.1的规定。',
        basis='# 3.3.1 外部作业净距控制值宜符合表3.3.1的规定。 表 3.3.1 外部作业净距控制值 单位：m 外部作业轨道交通结构类型地下结构地面结构高架结构装配式现浇围护桩、地下连续墙*≥7.0≥5.0≥5.0≥5.0工程桩*非挤土桩≥5.0≥3.0≥3.0≥3.0挤土桩≥30.0≥20.0≥6.0≥6.0锚杆、锚索、土钉(末端)*≥10.0≥6.0≥6.0≥6.0上方基坑#≥4.0---穿越隧道#≥2.0---钻探孔*≥6.0≥3.0≥3.0≥3.0起重、吊装设备(站位及吊物)-≥6.0≥6.0搭建棚架及宣传标志-≥6.0≥6.0存放易燃物料-≥6.0≥6.0 （续表） 外部作业轨道交通结构类型地下结构地面结构高架结构装配式现浇浅孔爆破*≥15.0≥15.0≥15.0深孔爆破*≥50.0≥50.0≥50.0 注：1. *、#分别指外部作业与城市轨道交通结构外边线之间的水平投影净距、竖向净距；装配式地下结构指盾构法或顶管法隧道以及其他拼装地下结构。 2. 灌注桩采用冲孔、振动工艺时，按挤土桩考虑；围护桩、地下连续墙不含接口改造作业。 3. 上方基坑作业的竖向净距不宜小于 $1.0D$ ，且不小于 $4.0\\mathrm{m}$ ；下穿隧道作业的竖向净距不宜小于 $1.0D$ ，且不小于 $2.0\\mathrm{m}$ ； $D$ 为新建隧道及既有结构外径或宽度的最大值。 4.当地基土以软弱土为主时，表中的净距控制值宜适当提高，并从严控制。 5. 对不满足净距控制值的，须经专题专项论证确定。',
        requirements=['外部作业净距控制值宜符合表3.3.1的规定。 表 3.3.1 外部作业净距控制值 单位：m 外部作业轨道交通结构类型地下结构地面结构高架结构装配式现浇围护桩、地下连续墙*≥7.0≥5.0≥5.0≥5.0工程桩*非挤土桩≥5.0≥3.0≥3.0≥3.0挤土桩≥30.0≥20.0≥6.0≥6.0锚杆、锚索、土钉(末端)*≥10.0≥6.0≥6.0≥6.0上方基坑#≥4.0---穿越隧道#≥2.0---钻探孔*≥6.0≥3.0≥3.0≥3.0'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_3_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_3_2',
 'clause': '3.3.2',
 'chapter': '基本规定',
 'section': '3.3 外部作业净距控制值',
 'title': '油气、燃气、天然气等易燃易爆物的净距控制值应按现行国家标准《石油天然气工程设计防火规范》GB50183和《输气管道工程设计规范》GB50251的要求，综合考虑其',
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
 'requirements': ['油气、燃气、天然气等易燃易爆物的净距控制值应按现行国家标准《石油天然气工程设计防火规范》GB50183和《输气管道工程设计规范》GB50251的要求，综合考虑其防火、防爆的安全保护要求后确定。'],
 'output': OUTPUT_SCHEMA}


def clause_3_3_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.3.2 油气、燃气、天然气等易燃易爆物的净距控制值应按现行国家标准《石油天然气工程设计防火规范》GB50183和《输气管道工程设计规范》GB50251的要求，综合考虑其."""

    return _evaluate_clause(
        clause='3.3.2',
        chapter='基本规定',
        section='3.3 外部作业净距控制值',
        title='油气、燃气、天然气等易燃易爆物的净距控制值应按现行国家标准《石油天然气工程设计防火规范》GB50183和《输气管道工程设计规范》GB50251的要求，综合考虑其',
        basis='3.3.2 油气、燃气、天然气等易燃易爆物的净距控制值应按现行国家标准《石油天然气工程设计防火规范》GB50183和《输气管道工程设计规范》GB50251的要求，综合考虑其防火、防爆的安全保护要求后确定。',
        requirements=['油气、燃气、天然气等易燃易爆物的净距控制值应按现行国家标准《石油天然气工程设计防火规范》GB50183和《输气管道工程设计规范》GB50251的要求，综合考虑其防火、防爆的安全保护要求后确定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_3_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_3_3',
 'clause': '3.3.3',
 'chapter': '基本规定',
 'section': '3.3 外部作业净距控制值',
 'title': '汽车加油加气站的净距控制值应按现行国家标准《汽车加油加气站设计与施工规范》GB50156的要求确定。',
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
 'requirements': ['汽车加油加气站的净距控制值应按现行国家标准《汽车加油加气站设计与施工规范》GB50156的要求确定。'],
 'output': OUTPUT_SCHEMA}


def clause_3_3_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.3.3 汽车加油加气站的净距控制值应按现行国家标准《汽车加油加气站设计与施工规范》GB50156的要求确定。."""

    return _evaluate_clause(
        clause='3.3.3',
        chapter='基本规定',
        section='3.3 外部作业净距控制值',
        title='汽车加油加气站的净距控制值应按现行国家标准《汽车加油加气站设计与施工规范》GB50156的要求确定。',
        basis='3.3.3 汽车加油加气站的净距控制值应按现行国家标准《汽车加油加气站设计与施工规范》GB50156的要求确定。',
        requirements=['汽车加油加气站的净距控制值应按现行国家标准《汽车加油加气站设计与施工规范》GB50156的要求确定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_3_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_3_4',
 'clause': '3.3.4',
 'chapter': '基本规定',
 'section': '3.3 外部作业净距控制值',
 'title': '外部作业与越江（河、湖）城市轨道交通地下结构、跨江桥梁的净距控制值应根据实际情况进行确定，并不宜小于表3.3.1中相应数值的3倍。',
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
 'requirements': ['外部作业与越江（河、湖）城市轨道交通地下结构、跨江桥梁的净距控制值应根据实际情况进行确定，并不宜小于表3.3.1中相应数值的3倍。'],
 'output': OUTPUT_SCHEMA}


def clause_3_3_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.3.4 外部作业与越江（河、湖）城市轨道交通地下结构、跨江桥梁的净距控制值应根据实际情况进行确定，并不宜小于表3.3.1中相应数值的3倍。."""

    return _evaluate_clause(
        clause='3.3.4',
        chapter='基本规定',
        section='3.3 外部作业净距控制值',
        title='外部作业与越江（河、湖）城市轨道交通地下结构、跨江桥梁的净距控制值应根据实际情况进行确定，并不宜小于表3.3.1中相应数值的3倍。',
        basis='3.3.4 外部作业与越江（河、湖）城市轨道交通地下结构、跨江桥梁的净距控制值应根据实际情况进行确定，并不宜小于表3.3.1中相应数值的3倍。',
        requirements=['外部作业与越江（河、湖）城市轨道交通地下结构、跨江桥梁的净距控制值应根据实际情况进行确定，并不宜小于表3.3.1中相应数值的3倍。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_3_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_3_5',
 'clause': '3.3.5',
 'chapter': '基本规定',
 'section': '3.3 外部作业净距控制值',
 'title': '高压电力管线、架空电力线等设施的净距控制值应按现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》G',
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
 'requirements': ['高压电力管线、架空电力线等设施的净距控制值应按现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》GB50545及《城市工程管线综合规划规范》GB50289等的要求确定。 '
                  '# 3.4 结构安全控制指标'],
 'output': OUTPUT_SCHEMA}


def clause_3_3_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.3.5 高压电力管线、架空电力线等设施的净距控制值应按现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》G."""

    return _evaluate_clause(
        clause='3.3.5',
        chapter='基本规定',
        section='3.3 外部作业净距控制值',
        title='高压电力管线、架空电力线等设施的净距控制值应按现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》G',
        basis='3.3.5 高压电力管线、架空电力线等设施的净距控制值应按现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》GB50545及《城市工程管线综合规划规范》GB50289等的要求确定。 # 3.4 结构安全控制指标',
        requirements=['高压电力管线、架空电力线等设施的净距控制值应按现行国家标准《66kV及以下架空电力线路设计规范》GB50061、《110kV～750kV架空输电线路设计规范》GB50545及《城市工程管线综合规划规范》GB50289等的要求确定。 # 3.4 结构安全控制指标'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_4_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_4_1',
 'clause': '3.4.1',
 'chapter': '基本规定',
 'section': '3.4 结构安全控制指标',
 'title': '结构安全控制指标包括：位移、差异沉降、相对收敛、变形曲率半径、变形相对曲率、变形速率、结构裂缝、管片接缝张开量与管片错台、附加荷载、振动速度等。',
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
 'requirements': ['结构安全控制指标包括：位移、差异沉降、相对收敛、变形曲率半径、变形相对曲率、变形速率、结构裂缝、管片接缝张开量与管片错台、附加荷载、振动速度等。'],
 'output': OUTPUT_SCHEMA}


def clause_3_4_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.4.1 结构安全控制指标包括：位移、差异沉降、相对收敛、变形曲率半径、变形相对曲率、变形速率、结构裂缝、管片接缝张开量与管片错台、附加荷载、振动速度等。."""

    return _evaluate_clause(
        clause='3.4.1',
        chapter='基本规定',
        section='3.4 结构安全控制指标',
        title='结构安全控制指标包括：位移、差异沉降、相对收敛、变形曲率半径、变形相对曲率、变形速率、结构裂缝、管片接缝张开量与管片错台、附加荷载、振动速度等。',
        basis='3.4.1 结构安全控制指标包括：位移、差异沉降、相对收敛、变形曲率半径、变形相对曲率、变形速率、结构裂缝、管片接缝张开量与管片错台、附加荷载、振动速度等。',
        requirements=['结构安全控制指标包括：位移、差异沉降、相对收敛、变形曲率半径、变形相对曲率、变形速率、结构裂缝、管片接缝张开量与管片错台、附加荷载、振动速度等。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_4_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_4_2',
 'clause': '3.4.2',
 'chapter': '基本规定',
 'section': '3.4 结构安全控制指标',
 'title': '结构安全控制指标值的选择应遵循可操作性原则，并结合轨道交通结构的特点、安全现状、结构保护及运营安全要求、外部作业对既有结构的影响特征等合理选用。当存在时空相近的',
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
 'requirements': ['结构安全控制指标值的选择应遵循可操作性原则，并结合轨道交通结构的特点、安全现状、结构保护及运营安全要求、外部作业对既有结构的影响特征等合理选用。当存在时空相近的多项外部作业时，应综合考虑叠加效应，合理分配结构安全控制指标。'],
 'output': OUTPUT_SCHEMA}


def clause_3_4_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.4.2 结构安全控制指标值的选择应遵循可操作性原则，并结合轨道交通结构的特点、安全现状、结构保护及运营安全要求、外部作业对既有结构的影响特征等合理选用。当存在时空相近的."""

    return _evaluate_clause(
        clause='3.4.2',
        chapter='基本规定',
        section='3.4 结构安全控制指标',
        title='结构安全控制指标值的选择应遵循可操作性原则，并结合轨道交通结构的特点、安全现状、结构保护及运营安全要求、外部作业对既有结构的影响特征等合理选用。当存在时空相近的',
        basis='3.4.2 结构安全控制指标值的选择应遵循可操作性原则，并结合轨道交通结构的特点、安全现状、结构保护及运营安全要求、外部作业对既有结构的影响特征等合理选用。当存在时空相近的多项外部作业时，应综合考虑叠加效应，合理分配结构安全控制指标。',
        requirements=['结构安全控制指标值的选择应遵循可操作性原则，并结合轨道交通结构的特点、安全现状、结构保护及运营安全要求、外部作业对既有结构的影响特征等合理选用。当存在时空相近的多项外部作业时，应综合考虑叠加效应，合理分配结构安全控制指标。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_4_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_4_3',
 'clause': '3.4.3',
 'chapter': '基本规定',
 'section': '3.4 结构安全控制指标',
 'title': '外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。',
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
 'requirements': ['外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。'],
 'output': OUTPUT_SCHEMA}


def clause_3_4_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.4.3 外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。."""

    return _evaluate_clause(
        clause='3.4.3',
        chapter='基本规定',
        section='3.4 结构安全控制指标',
        title='外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。',
        basis='3.4.3 外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。',
        requirements=['外部作业引起的城市轨道交通结构附加变形不得超过安全控制指标的控制值，附加荷载及累计变形不得超过安全控制指标的安全限值，道床与轨道结构变位不得影响列车运营安全。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_4_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_4_4',
 'clause': '3.4.4',
 'chapter': '基本规定',
 'section': '3.4 结构安全控制指标',
 'title': '既有结构变形或病害较严重、存在维修或加固情况的，结构安全控制指标值应根据现状评估结果动态调整，并从严控制。',
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
 'requirements': ['既有结构变形或病害较严重、存在维修或加固情况的，结构安全控制指标值应根据现状评估结果动态调整，并从严控制。'],
 'output': OUTPUT_SCHEMA}


def clause_3_4_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.4.4 既有结构变形或病害较严重、存在维修或加固情况的，结构安全控制指标值应根据现状评估结果动态调整，并从严控制。."""

    return _evaluate_clause(
        clause='3.4.4',
        chapter='基本规定',
        section='3.4 结构安全控制指标',
        title='既有结构变形或病害较严重、存在维修或加固情况的，结构安全控制指标值应根据现状评估结果动态调整，并从严控制。',
        basis='3.4.4 既有结构变形或病害较严重、存在维修或加固情况的，结构安全控制指标值应根据现状评估结果动态调整，并从严控制。',
        requirements=['既有结构变形或病害较严重、存在维修或加固情况的，结构安全控制指标值应根据现状评估结果动态调整，并从严控制。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_3_4_5_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_3_4_5',
 'clause': '3.4.5',
 'chapter': '基本规定',
 'section': '3.4 结构安全控制指标',
 'title': '结构安全控制指标值宜符合本规程附录C的规定。',
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
 'requirements': ['结构安全控制指标值宜符合本规程附录C的规定。 # 4 既有结构保护 # 4.1 一般规定'],
 'output': OUTPUT_SCHEMA}


def clause_3_4_5(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """3.4.5 结构安全控制指标值宜符合本规程附录C的规定。."""

    return _evaluate_clause(
        clause='3.4.5',
        chapter='基本规定',
        section='3.4 结构安全控制指标',
        title='结构安全控制指标值宜符合本规程附录C的规定。',
        basis='3.4.5 结构安全控制指标值宜符合本规程附录C的规定。 # 4 既有结构保护 # 4.1 一般规定',
        requirements=['结构安全控制指标值宜符合本规程附录C的规定。 # 4 既有结构保护 # 4.1 一般规定'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_3_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_3_functions",
    "chapter": '基本规定',
    "description": "DB32/T 4351-2022 chapter 3 clause function API schema.",
    "functions": {
        "clause_3_1_1": CLAUSE_3_1_1_INPUT_SCHEMA,
        "clause_3_1_2": CLAUSE_3_1_2_INPUT_SCHEMA,
        "clause_3_1_3": CLAUSE_3_1_3_INPUT_SCHEMA,
        "clause_3_1_4": CLAUSE_3_1_4_INPUT_SCHEMA,
        "clause_3_1_5": CLAUSE_3_1_5_INPUT_SCHEMA,
        "clause_3_1_6": CLAUSE_3_1_6_INPUT_SCHEMA,
        "clause_3_1_7": CLAUSE_3_1_7_INPUT_SCHEMA,
        "clause_3_1_8": CLAUSE_3_1_8_INPUT_SCHEMA,
        "clause_3_2_1": CLAUSE_3_2_1_INPUT_SCHEMA,
        "clause_3_2_2": CLAUSE_3_2_2_INPUT_SCHEMA,
        "clause_3_2_3": CLAUSE_3_2_3_INPUT_SCHEMA,
        "clause_3_2_4": CLAUSE_3_2_4_INPUT_SCHEMA,
        "clause_3_2_5": CLAUSE_3_2_5_INPUT_SCHEMA,
        "clause_3_2_6": CLAUSE_3_2_6_INPUT_SCHEMA,
        "clause_3_3_1": CLAUSE_3_3_1_INPUT_SCHEMA,
        "clause_3_3_2": CLAUSE_3_3_2_INPUT_SCHEMA,
        "clause_3_3_3": CLAUSE_3_3_3_INPUT_SCHEMA,
        "clause_3_3_4": CLAUSE_3_3_4_INPUT_SCHEMA,
        "clause_3_3_5": CLAUSE_3_3_5_INPUT_SCHEMA,
        "clause_3_4_1": CLAUSE_3_4_1_INPUT_SCHEMA,
        "clause_3_4_2": CLAUSE_3_4_2_INPUT_SCHEMA,
        "clause_3_4_3": CLAUSE_3_4_3_INPUT_SCHEMA,
        "clause_3_4_4": CLAUSE_3_4_4_INPUT_SCHEMA,
        "clause_3_4_5": CLAUSE_3_4_5_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_3_1_1(confirmed_items=['城市轨道交通结构安全保护工作包含既有结构保护、外部作业控制、接口改造、安全监测及结构病害治理等内容。'], strict=False)
    print(first.to_dict())
