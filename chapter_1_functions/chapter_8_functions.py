"""Functions for Chapter 8 of DB32/T 4351-2022.

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

CLAUSE_8_1_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_1_1',
 'clause': '8.1.1',
 'chapter': '地下结构病害治理',
 'section': '8.1 一般规定',
 'title': '外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。',
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
 'requirements': ['外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。'],
 'output': OUTPUT_SCHEMA}


def clause_8_1_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.1.1 外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。."""

    return _evaluate_clause(
        clause='8.1.1',
        chapter='地下结构病害治理',
        section='8.1 一般规定',
        title='外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。',
        basis='8.1.1 外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。',
        requirements=['外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_1_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_1_2',
 'clause': '8.1.2',
 'chapter': '地下结构病害治理',
 'section': '8.1 一般规定',
 'title': '城市轨道交通地下结构病害治理应根据结构类型、病害类型和病害等级确定。',
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
 'requirements': ['城市轨道交通地下结构病害治理应根据结构类型、病害类型和病害等级确定。'],
 'output': OUTPUT_SCHEMA}


def clause_8_1_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.1.2 城市轨道交通地下结构病害治理应根据结构类型、病害类型和病害等级确定。."""

    return _evaluate_clause(
        clause='8.1.2',
        chapter='地下结构病害治理',
        section='8.1 一般规定',
        title='城市轨道交通地下结构病害治理应根据结构类型、病害类型和病害等级确定。',
        basis='8.1.2 城市轨道交通地下结构病害治理应根据结构类型、病害类型和病害等级确定。',
        requirements=['城市轨道交通地下结构病害治理应根据结构类型、病害类型和病害等级确定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_1_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_1_3',
 'clause': '8.1.3',
 'chapter': '地下结构病害治理',
 'section': '8.1 一般规定',
 'title': '重大影响外部作业应按照“外控内治、动态平衡”的原则对城市轨道交通地下结构进行预加固、过程加固或后加固。',
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
 'requirements': ['重大影响外部作业应按照“外控内治、动态平衡”的原则对城市轨道交通地下结构进行预加固、过程加固或后加固。'],
 'output': OUTPUT_SCHEMA}


def clause_8_1_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.1.3 重大影响外部作业应按照“外控内治、动态平衡”的原则对城市轨道交通地下结构进行预加固、过程加固或后加固。."""

    return _evaluate_clause(
        clause='8.1.3',
        chapter='地下结构病害治理',
        section='8.1 一般规定',
        title='重大影响外部作业应按照“外控内治、动态平衡”的原则对城市轨道交通地下结构进行预加固、过程加固或后加固。',
        basis='8.1.3 重大影响外部作业应按照“外控内治、动态平衡”的原则对城市轨道交通地下结构进行预加固、过程加固或后加固。',
        requirements=['重大影响外部作业应按照“外控内治、动态平衡”的原则对城市轨道交通地下结构进行预加固、过程加固或后加固。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_1_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_1_4',
 'clause': '8.1.4',
 'chapter': '地下结构病害治理',
 'section': '8.1 一般规定',
 'title': '城市轨道交通地下结构病害治理完成后，应对治理后的结构进行监测、检测与后评估。',
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
 'requirements': ['城市轨道交通地下结构病害治理完成后，应对治理后的结构进行监测、检测与后评估。 # 8.2 安全状态与病害分级'],
 'output': OUTPUT_SCHEMA}


def clause_8_1_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.1.4 城市轨道交通地下结构病害治理完成后，应对治理后的结构进行监测、检测与后评估。."""

    return _evaluate_clause(
        clause='8.1.4',
        chapter='地下结构病害治理',
        section='8.1 一般规定',
        title='城市轨道交通地下结构病害治理完成后，应对治理后的结构进行监测、检测与后评估。',
        basis='8.1.4 城市轨道交通地下结构病害治理完成后，应对治理后的结构进行监测、检测与后评估。 # 8.2 安全状态与病害分级',
        requirements=['城市轨道交通地下结构病害治理完成后，应对治理后的结构进行监测、检测与后评估。 # 8.2 安全状态与病害分级'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_2_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_2_1',
 'clause': '8.2.1',
 'chapter': '地下结构病害治理',
 'section': '8.2 安全状态与病害分级',
 'title': '城市轨道交通地下结构类型主要有盾构法、明挖法和矿山法等，结构安全状态分级应符合表8.2.1的规定。',
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
 'requirements': ['城市轨道交通地下结构类型主要有盾构法、明挖法和矿山法等，结构安全状态分级应符合表8.2.1的规定。 表 8.2.1 城市轨道交通地下结构安全状态分级 '
                  '分级分级定义维护措施1级性能完好日常检查2级性能退化，趋于稳定，不影响运营安全保证结构耐久性的维护3级性能劣化，发展较慢，将来影响运营安全重点监护、对应修复4级性能恶化，发展较快，影响但不危及安全修复或加固5级性能严重恶化，发展迅速，危及安全加固或更换'],
 'output': OUTPUT_SCHEMA}


def clause_8_2_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.2.1 城市轨道交通地下结构类型主要有盾构法、明挖法和矿山法等，结构安全状态分级应符合表8.2.1的规定。."""

    return _evaluate_clause(
        clause='8.2.1',
        chapter='地下结构病害治理',
        section='8.2 安全状态与病害分级',
        title='城市轨道交通地下结构类型主要有盾构法、明挖法和矿山法等，结构安全状态分级应符合表8.2.1的规定。',
        basis='8.2.1 城市轨道交通地下结构类型主要有盾构法、明挖法和矿山法等，结构安全状态分级应符合表8.2.1的规定。 表 8.2.1 城市轨道交通地下结构安全状态分级 分级分级定义维护措施1级性能完好日常检查2级性能退化，趋于稳定，不影响运营安全保证结构耐久性的维护3级性能劣化，发展较慢，将来影响运营安全重点监护、对应修复4级性能恶化，发展较快，影响但不危及安全修复或加固5级性能严重恶化，发展迅速，危及安全加固或更换',
        requirements=['城市轨道交通地下结构类型主要有盾构法、明挖法和矿山法等，结构安全状态分级应符合表8.2.1的规定。 表 8.2.1 城市轨道交通地下结构安全状态分级 分级分级定义维护措施1级性能完好日常检查2级性能退化，趋于稳定，不影响运营安全保证结构耐久性的维护3级性能劣化，发展较慢，将来影响运营安全重点监护、对应修复4级性能恶化，发展较快，影响但不危及安全修复或加固5级性能严重恶化，发展迅速，危及安全加固或更换'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_2_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_2_2',
 'clause': '8.2.2',
 'chapter': '地下结构病害治理',
 'section': '8.2 安全状态与病害分级',
 'title': '城市轨道交通地下结构病害导致既有设施设备侵入建筑限界的，应将结构安全状态评定为5级。当结构安全状态达到4级及以上时，应进行病害治理专项论证。',
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
 'requirements': ['城市轨道交通地下结构病害导致既有设施设备侵入建筑限界的，应将结构安全状态评定为5级。当结构安全状态达到4级及以上时，应进行病害治理专项论证。'],
 'output': OUTPUT_SCHEMA}


def clause_8_2_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.2.2 城市轨道交通地下结构病害导致既有设施设备侵入建筑限界的，应将结构安全状态评定为5级。当结构安全状态达到4级及以上时，应进行病害治理专项论证。."""

    return _evaluate_clause(
        clause='8.2.2',
        chapter='地下结构病害治理',
        section='8.2 安全状态与病害分级',
        title='城市轨道交通地下结构病害导致既有设施设备侵入建筑限界的，应将结构安全状态评定为5级。当结构安全状态达到4级及以上时，应进行病害治理专项论证。',
        basis='8.2.2 城市轨道交通地下结构病害导致既有设施设备侵入建筑限界的，应将结构安全状态评定为5级。当结构安全状态达到4级及以上时，应进行病害治理专项论证。',
        requirements=['城市轨道交通地下结构病害导致既有设施设备侵入建筑限界的，应将结构安全状态评定为5级。当结构安全状态达到4级及以上时，应进行病害治理专项论证。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_2_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_2_3',
 'clause': '8.2.3',
 'chapter': '地下结构病害治理',
 'section': '8.2 安全状态与病害分级',
 'title': '盾构法结构病害主要包括渗漏水、管片裂缝与破损、管片接缝错台、收敛变形及纵向不均匀沉降等，各类型病害分级标准可按表8.2.3-1～8.2.3-6划分。',
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
 'requirements': ['盾构法结构病害主要包括渗漏水、管片裂缝与破损、管片接缝错台、收敛变形及纵向不均匀沉降等，各类型病害分级标准可按表8.2.3-1～8.2.3-6划分。 表 8.2.3-1 盾构法结构渗漏水病害分级标准 '
                  '分级分级标准1级无',
                  '表面有少量湿渍,无肉眼可见漏水源2级有渗水,无滴漏3级有滴水,无漏泥,滴水频率小于60滴/min,位于侧面,不影响行车安全4级隧底涌流、道床下沉,影响正常运行',
                  '拱部滴漏,边墙淌水,影响正常运行5级涌水',
                  '拱部线漏、涌流或直接传至接触网,危及行车安全 注：1. “,”表示均需满足,“',
                  '”表示任意满足,不均匀沉降、收敛变形严重区段可酌情提高等级。 2. 本表适用于接触网位于拱顶的常规盾构隧道，接触网位于隧道侧面可参照执行。 表 8.2.3-2 盾构法结构管片裂缝病害分级标准 '
                  '分级分级标准1级W&lt',
                  '0.2mm2级0.2mm≤W&lt',
                  '0.5mm3级0.5mm≤W&lt',
                  '1.0mm4级1.0mm≤W&lt',
                  '2.0mm5级W≥2.0mm 注： $W$ 表示裂缝宽度。 表 8.2.3-3 盾构法结构管片破损病害分级标准 分级分级标准1级保护层无剥落,无掉角掉块现象,无可见裂缝2级压溃面积很小',
                  'D≤50mm3级压溃面积小于1㎡',
                  '5mm&lt',
                  'S≤30mm'],
 'output': OUTPUT_SCHEMA}


def clause_8_2_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.2.3 盾构法结构病害主要包括渗漏水、管片裂缝与破损、管片接缝错台、收敛变形及纵向不均匀沉降等，各类型病害分级标准可按表8.2.3-1～8.2.3-6划分。."""

    return _evaluate_clause(
        clause='8.2.3',
        chapter='地下结构病害治理',
        section='8.2 安全状态与病害分级',
        title='盾构法结构病害主要包括渗漏水、管片裂缝与破损、管片接缝错台、收敛变形及纵向不均匀沉降等，各类型病害分级标准可按表8.2.3-1～8.2.3-6划分。',
        basis='8.2.3 盾构法结构病害主要包括渗漏水、管片裂缝与破损、管片接缝错台、收敛变形及纵向不均匀沉降等，各类型病害分级标准可按表8.2.3-1～8.2.3-6划分。 表 8.2.3-1 盾构法结构渗漏水病害分级标准 分级分级标准1级无;表面有少量湿渍,无肉眼可见漏水源2级有渗水,无滴漏3级有滴水,无漏泥,滴水频率小于60滴/min,位于侧面,不影响行车安全4级隧底涌流、道床下沉,影响正常运行;拱部滴漏,边墙淌水,影响正常运行5级涌水;漏泥漏砂;拱部线漏、涌流或直接传至接触网,危及行车安全 注：1. “,”表示均需满足,“;”表示任意满足,不均匀沉降、收敛变形严重区段可酌情提高等级。 2. 本表适用于接触网位于拱顶的常规盾构隧道，接触网位于隧道侧面可参照执行。 表 8.2.3-2 盾构法结构管片裂缝病害分级标准 分级分级标准1级W&lt;0.2mm2级0.2mm≤W&lt;0.5mm3级0.5mm≤W&lt;1.0mm4级1.0mm≤W&lt;2.0mm5级W≥2.0mm 注： $W$ 表示裂缝宽度。 表 8.2.3-3 盾构法结构管片破损病害分级标准 分级分级标准1级保护层无剥落,无掉角掉块现象,无可见裂缝2级压溃面积很小;S≤5mm;D≤50mm3级压溃面积小于1㎡;5mm&lt;S≤30mm;50mm&lt;D≤75mm4级压溃面积1㎡~3㎡;30mm&lt;S≤衬砌厚度的1/4;75mm&lt;D≤150mm;可能掉块5级压溃面积大于3㎡;S&gt;衬砌厚度的1/4;D&gt;150mm;剥落面积超过该构件表面积的1/3 注：1. “,”表示均需满足,“;”表示任意满足。 2. $S$ 表示剥落深度， $D$ 表示剥落区直径。 表 8.2.3-4 盾构法结构管片接缝错台病害分级标准 分级分级标准1级纵缝错台≤5mm；环缝错台≤6mm2级5mm&lt;纵缝错台≤8mm；6mm&lt;环缝错台≤12mm3级8mm&lt;纵缝错台≤10mm；12mm&lt;环缝错台≤15mm4级10mm&lt;纵缝错台≤12mm；15mm&lt;环缝错台≤18mm5级纵缝错台&gt;12mm；环缝错台&gt;18mm 注：“；”表示任意满足。 表 8.2.3-5 盾构法结构收敛变形病害分级标准 分级分级标准常用管片(单位: mm)错缝拼装管片通缝拼装管片1 级\\( c&lt;24.8 \\)\\( c&lt;4 \\text{‰}D \\)\\( c&lt;5 \\text{‰}D \\)2 级24.8≤c&lt;37.2\\( 4 \\text{‰}D≤c&lt;6 \\text{‰}D \\)\\( 5 \\text{‰}D≤c&lt;8 \\text{‰}D \\)3 级37.2≤c&lt;55.8\\( 6 \\text{‰}D≤c&lt;9 \\text{‰}D \\)\\( 8 \\text{‰}D≤c&lt;12 \\text{‰}D \\)4 级55.8≤c&lt;74.4\\( 9 \\text{‰}D≤c&lt;12 \\text{‰}D \\)\\( 12 \\text{‰}D≤c&lt;16 \\text{‰}D \\)5 级\\( c≥74.4 \\)\\( c≥12 \\text{‰}D \\)\\( c≥16 \\text{‰}D \\) 注：1. $c$ 为隧道收敛变形量， $D$ 为隧道直径。 2. 本表量化的分级标准依据江苏省内常用的外径 $6.2\\mathrm{m}$ 盾构法隧道结构拟定，其他直径盾构法结构可根据管片拼装方式参考制定。 表 8.2.3-6 盾构法结构纵向不均匀沉降病害分级标准 分级分级标准1级ρ≥15000m2级8000m&lt;ρ&lt;15000m3级1200m&lt;ρ≤8000m4级300m&lt;ρ≤1200m5级ρ≤300m 注：1. $\\rho$ 为盾构法结构纵向变形曲率半径。 2. 本表适用于外径 $6.2\\mathrm{m}$ 盾构法隧道，其他尺寸可参考制定。',
        requirements=['盾构法结构病害主要包括渗漏水、管片裂缝与破损、管片接缝错台、收敛变形及纵向不均匀沉降等，各类型病害分级标准可按表8.2.3-1～8.2.3-6划分。 表 8.2.3-1 盾构法结构渗漏水病害分级标准 分级分级标准1级无', '表面有少量湿渍,无肉眼可见漏水源2级有渗水,无滴漏3级有滴水,无漏泥,滴水频率小于60滴/min,位于侧面,不影响行车安全4级隧底涌流、道床下沉,影响正常运行', '拱部滴漏,边墙淌水,影响正常运行5级涌水', '拱部线漏、涌流或直接传至接触网,危及行车安全 注：1. “,”表示均需满足,“', '”表示任意满足,不均匀沉降、收敛变形严重区段可酌情提高等级。 2. 本表适用于接触网位于拱顶的常规盾构隧道，接触网位于隧道侧面可参照执行。 表 8.2.3-2 盾构法结构管片裂缝病害分级标准 分级分级标准1级W&lt', '0.2mm2级0.2mm≤W&lt', '0.5mm3级0.5mm≤W&lt', '1.0mm4级1.0mm≤W&lt', '2.0mm5级W≥2.0mm 注： $W$ 表示裂缝宽度。 表 8.2.3-3 盾构法结构管片破损病害分级标准 分级分级标准1级保护层无剥落,无掉角掉块现象,无可见裂缝2级压溃面积很小', 'D≤50mm3级压溃面积小于1㎡', '5mm&lt', 'S≤30mm'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_2_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_2_4',
 'clause': '8.2.4',
 'chapter': '地下结构病害治理',
 'section': '8.2 安全状态与病害分级',
 'title': '明挖法或矿山法结构病害主要包括渗漏水、结构裂缝、结构破损、接缝（施工缝、变形缝）错台与纵向不均匀沉降等，其中渗漏水病害和结构破损病害分级分别按表8.2.3-1、',
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
 'requirements': ['明挖法或矿山法结构病害主要包括渗漏水、结构裂缝、结构破损、接缝（施工缝、变形缝）错台与纵向不均匀沉降等，其中渗漏水病害和结构破损病害分级分别按表8.2.3-1、表8.2.3-3划分，其余病害分级可按表 '
                  '$8.2.4 - 1\\sim 8.2.4 - 3$ 划分。 表 8.2.4-1 明挖法或矿山法结构裂缝病害分级标准 等级分级标准1级无肉眼可见裂缝；W&lt',
                  '0.3mm2级L≤5m，0.3mm≤W&lt',
                  '3mm3级L≤5m，3mm≤W&lt',
                  '5mm；裂缝多于三条，且存在交叉；裂缝发展不快4级10m≥L&gt',
                  '5m，W≥5mm；裂缝呈网状分布，在外力作用下可能掉块；裂缝出现渗漏，但不影响行车安全5级L&gt',
                  '10m，W≥5mm，且裂缝继续发展；拱部开裂呈块状，有掉块风险；裂缝出现漏泥、漏砂现象，影响行车安全 注：1. “,”表示均需满足,“',
                  '”表示任意满足；衬砌裂纹沿纵向或斜向时,应提高一级。 2. $L$ 表示裂缝长度， $W$ 表示裂缝宽度。 表 8.2.4-2 明挖法或矿山法结构接缝错台病害分级标准 等级分级标准1级明挖法 '
                  'b≤10mm, 矿山法 b≤20mm',
                  '接缝无渗漏水2级明挖法 10mm&lt',
                  'b≤20mm,矿山法 20mm&lt',
                  'b≤30mm',
                  '接缝出现湿渍3级明挖法 20mm&lt',
                  'b≤30mm,矿山法 30mm&lt'],
 'output': OUTPUT_SCHEMA}


def clause_8_2_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.2.4 明挖法或矿山法结构病害主要包括渗漏水、结构裂缝、结构破损、接缝（施工缝、变形缝）错台与纵向不均匀沉降等，其中渗漏水病害和结构破损病害分级分别按表8.2.3-1、."""

    return _evaluate_clause(
        clause='8.2.4',
        chapter='地下结构病害治理',
        section='8.2 安全状态与病害分级',
        title='明挖法或矿山法结构病害主要包括渗漏水、结构裂缝、结构破损、接缝（施工缝、变形缝）错台与纵向不均匀沉降等，其中渗漏水病害和结构破损病害分级分别按表8.2.3-1、',
        basis='8.2.4 明挖法或矿山法结构病害主要包括渗漏水、结构裂缝、结构破损、接缝（施工缝、变形缝）错台与纵向不均匀沉降等，其中渗漏水病害和结构破损病害分级分别按表8.2.3-1、表8.2.3-3划分，其余病害分级可按表 $8.2.4 - 1\\sim 8.2.4 - 3$ 划分。 表 8.2.4-1 明挖法或矿山法结构裂缝病害分级标准 等级分级标准1级无肉眼可见裂缝；W&lt;0.3mm2级L≤5m，0.3mm≤W&lt;3mm3级L≤5m，3mm≤W&lt;5mm；裂缝多于三条，且存在交叉；裂缝发展不快4级10m≥L&gt;5m，W≥5mm；裂缝呈网状分布，在外力作用下可能掉块；裂缝出现渗漏，但不影响行车安全5级L&gt;10m，W≥5mm，且裂缝继续发展；拱部开裂呈块状，有掉块风险；裂缝出现漏泥、漏砂现象，影响行车安全 注：1. “,”表示均需满足,“;”表示任意满足；衬砌裂纹沿纵向或斜向时,应提高一级。 2. $L$ 表示裂缝长度， $W$ 表示裂缝宽度。 表 8.2.4-2 明挖法或矿山法结构接缝错台病害分级标准 等级分级标准1级明挖法 b≤10mm, 矿山法 b≤20mm; 接缝无渗漏水2级明挖法 10mm&lt;b≤20mm,矿山法 20mm&lt;b≤30mm; 接缝出现湿渍3级明挖法 20mm&lt;b≤30mm,矿山法 30mm&lt;b≤40mm; 接缝浸渗、滴漏4级明挖法 30mm&lt;b≤40mm,矿山法 40mm&lt;b≤50mm; 接缝线漏5级明挖法 b&gt;40m,矿山法 b&gt;50mm;接缝涌流或漏泥、漏砂 注：“，”表示均需满足，“；”表示任意满足； $b$ 表示接缝（施工缝、变形缝）错台量。 表 8.2.4-3 明挖法或矿山法结构纵向不均匀沉降病害分级标准 等级分级标准1级隧道的相对变曲≤1/2 5002级1/2 500&lt;隧道的相对变曲≤2 0003级1/2 000&lt;隧道的相对变曲≤1/1 5004级1/1 500&lt;隧道的相对变曲≤1/5005级隧道的相对变曲&gt;1/500 # 8.3 病害治理要求',
        requirements=['明挖法或矿山法结构病害主要包括渗漏水、结构裂缝、结构破损、接缝（施工缝、变形缝）错台与纵向不均匀沉降等，其中渗漏水病害和结构破损病害分级分别按表8.2.3-1、表8.2.3-3划分，其余病害分级可按表 $8.2.4 - 1\\sim 8.2.4 - 3$ 划分。 表 8.2.4-1 明挖法或矿山法结构裂缝病害分级标准 等级分级标准1级无肉眼可见裂缝；W&lt', '0.3mm2级L≤5m，0.3mm≤W&lt', '3mm3级L≤5m，3mm≤W&lt', '5mm；裂缝多于三条，且存在交叉；裂缝发展不快4级10m≥L&gt', '5m，W≥5mm；裂缝呈网状分布，在外力作用下可能掉块；裂缝出现渗漏，但不影响行车安全5级L&gt', '10m，W≥5mm，且裂缝继续发展；拱部开裂呈块状，有掉块风险；裂缝出现漏泥、漏砂现象，影响行车安全 注：1. “,”表示均需满足,“', '”表示任意满足；衬砌裂纹沿纵向或斜向时,应提高一级。 2. $L$ 表示裂缝长度， $W$ 表示裂缝宽度。 表 8.2.4-2 明挖法或矿山法结构接缝错台病害分级标准 等级分级标准1级明挖法 b≤10mm, 矿山法 b≤20mm', '接缝无渗漏水2级明挖法 10mm&lt', 'b≤20mm,矿山法 20mm&lt', 'b≤30mm', '接缝出现湿渍3级明挖法 20mm&lt', 'b≤30mm,矿山法 30mm&lt'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_3_1_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_3_1',
 'clause': '8.3.1',
 'chapter': '地下结构病害治理',
 'section': '8.3 病害治理要求',
 'title': '轨道交通地下结构病害应分类分级治理，对第 $2\\sim 3$ 级病害进行维护与修复，对 $4\\sim 5$ 级病害进行重点治理，不同分级的病害采取不同的治理措施',
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
 'requirements': ['轨道交通地下结构病害应分类分级治理，对第 $2\\sim 3$ 级病害进行维护与修复，对 $4\\sim 5$ '
                  '级病害进行重点治理，不同分级的病害采取不同的治理措施，分类分级治理措施宜按本规程附录F执行。'],
 'output': OUTPUT_SCHEMA}


def clause_8_3_1(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.3.1 轨道交通地下结构病害应分类分级治理，对第 $2\\sim 3$ 级病害进行维护与修复，对 $4\\sim 5$ 级病害进行重点治理，不同分级的病害采取不同的治理措施."""

    return _evaluate_clause(
        clause='8.3.1',
        chapter='地下结构病害治理',
        section='8.3 病害治理要求',
        title='轨道交通地下结构病害应分类分级治理，对第 $2\\sim 3$ 级病害进行维护与修复，对 $4\\sim 5$ 级病害进行重点治理，不同分级的病害采取不同的治理措施',
        basis='8.3.1 轨道交通地下结构病害应分类分级治理，对第 $2\\sim 3$ 级病害进行维护与修复，对 $4\\sim 5$ 级病害进行重点治理，不同分级的病害采取不同的治理措施，分类分级治理措施宜按本规程附录F执行。',
        requirements=['轨道交通地下结构病害应分类分级治理，对第 $2\\sim 3$ 级病害进行维护与修复，对 $4\\sim 5$ 级病害进行重点治理，不同分级的病害采取不同的治理措施，分类分级治理措施宜按本规程附录F执行。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_3_2_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_3_2',
 'clause': '8.3.2',
 'chapter': '地下结构病害治理',
 'section': '8.3 病害治理要求',
 'title': '轨道交通地下结构病害治理方案应根据既有结构的病害类别与分级、建筑与设备限界、工程地质条件、场地条件、外部作业影响程度等因素综合确定。',
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
 'requirements': ['轨道交通地下结构病害治理方案应根据既有结构的病害类别与分级、建筑与设备限界、工程地质条件、场地条件、外部作业影响程度等因素综合确定。'],
 'output': OUTPUT_SCHEMA}


def clause_8_3_2(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.3.2 轨道交通地下结构病害治理方案应根据既有结构的病害类别与分级、建筑与设备限界、工程地质条件、场地条件、外部作业影响程度等因素综合确定。."""

    return _evaluate_clause(
        clause='8.3.2',
        chapter='地下结构病害治理',
        section='8.3 病害治理要求',
        title='轨道交通地下结构病害治理方案应根据既有结构的病害类别与分级、建筑与设备限界、工程地质条件、场地条件、外部作业影响程度等因素综合确定。',
        basis='8.3.2 轨道交通地下结构病害治理方案应根据既有结构的病害类别与分级、建筑与设备限界、工程地质条件、场地条件、外部作业影响程度等因素综合确定。',
        requirements=['轨道交通地下结构病害治理方案应根据既有结构的病害类别与分级、建筑与设备限界、工程地质条件、场地条件、外部作业影响程度等因素综合确定。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_3_3_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_3_3',
 'clause': '8.3.3',
 'chapter': '地下结构病害治理',
 'section': '8.3 病害治理要求',
 'title': '治理后的城市轨道交通地下结构的承载能力、正常使用功能及耐久性等应满足设计使用年限内的安全运营要求。',
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
 'requirements': ['治理后的城市轨道交通地下结构的承载能力、正常使用功能及耐久性等应满足设计使用年限内的安全运营要求。'],
 'output': OUTPUT_SCHEMA}


def clause_8_3_3(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.3.3 治理后的城市轨道交通地下结构的承载能力、正常使用功能及耐久性等应满足设计使用年限内的安全运营要求。."""

    return _evaluate_clause(
        clause='8.3.3',
        chapter='地下结构病害治理',
        section='8.3 病害治理要求',
        title='治理后的城市轨道交通地下结构的承载能力、正常使用功能及耐久性等应满足设计使用年限内的安全运营要求。',
        basis='8.3.3 治理后的城市轨道交通地下结构的承载能力、正常使用功能及耐久性等应满足设计使用年限内的安全运营要求。',
        requirements=['治理后的城市轨道交通地下结构的承载能力、正常使用功能及耐久性等应满足设计使用年限内的安全运营要求。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CLAUSE_8_3_4_INPUT_SCHEMA: dict[str, Any] = {'function': 'clause_8_3_4',
 'clause': '8.3.4',
 'chapter': '地下结构病害治理',
 'section': '8.3 病害治理要求',
 'title': '对于严重影响结构安全和运营安全的不均匀沉降，须对结构下方软弱土层进行加固，并根据线路平顺性及限界调整要求，采用微扰动注浆方式对既有地下结构进行适量抬升，治理后既',
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
 'requirements': ['对于严重影响结构安全和运营安全的不均匀沉降，须对结构下方软弱土层进行加固，并根据线路平顺性及限界调整要求，采用微扰动注浆方式对既有地下结构进行适量抬升，治理后既有结构的承载能力、正常使用功能及耐久性等不应低于原技术标准。'],
 'output': OUTPUT_SCHEMA}


def clause_8_3_4(
    applicable: bool = True,
    confirmed_items: Iterable[str] | None = None,
    measured_values: Mapping[str, Any] | None = None,
    notes: Iterable[str] | None = None,
    strict: bool = True,
) -> ClauseResult:
    """8.3.4 对于严重影响结构安全和运营安全的不均匀沉降，须对结构下方软弱土层进行加固，并根据线路平顺性及限界调整要求，采用微扰动注浆方式对既有地下结构进行适量抬升，治理后既."""

    return _evaluate_clause(
        clause='8.3.4',
        chapter='地下结构病害治理',
        section='8.3 病害治理要求',
        title='对于严重影响结构安全和运营安全的不均匀沉降，须对结构下方软弱土层进行加固，并根据线路平顺性及限界调整要求，采用微扰动注浆方式对既有地下结构进行适量抬升，治理后既',
        basis='8.3.4 对于严重影响结构安全和运营安全的不均匀沉降，须对结构下方软弱土层进行加固，并根据线路平顺性及限界调整要求，采用微扰动注浆方式对既有地下结构进行适量抬升，治理后既有结构的承载能力、正常使用功能及耐久性等不应低于原技术标准。',
        requirements=['对于严重影响结构安全和运营安全的不均匀沉降，须对结构下方软弱土层进行加固，并根据线路平顺性及限界调整要求，采用微扰动注浆方式对既有地下结构进行适量抬升，治理后既有结构的承载能力、正常使用功能及耐久性等不应低于原技术标准。'],
        applicable=applicable,
        confirmed_items=confirmed_items,
        measured_values=measured_values,
        notes=notes,
        strict=strict,
    )

CHAPTER_8_API_SCHEMA: dict[str, Any] = {
    "module": "chapter_8_functions",
    "chapter": '地下结构病害治理',
    "description": "DB32/T 4351-2022 chapter 8 clause function API schema.",
    "functions": {
        "clause_8_1_1": CLAUSE_8_1_1_INPUT_SCHEMA,
        "clause_8_1_2": CLAUSE_8_1_2_INPUT_SCHEMA,
        "clause_8_1_3": CLAUSE_8_1_3_INPUT_SCHEMA,
        "clause_8_1_4": CLAUSE_8_1_4_INPUT_SCHEMA,
        "clause_8_2_1": CLAUSE_8_2_1_INPUT_SCHEMA,
        "clause_8_2_2": CLAUSE_8_2_2_INPUT_SCHEMA,
        "clause_8_2_3": CLAUSE_8_2_3_INPUT_SCHEMA,
        "clause_8_2_4": CLAUSE_8_2_4_INPUT_SCHEMA,
        "clause_8_3_1": CLAUSE_8_3_1_INPUT_SCHEMA,
        "clause_8_3_2": CLAUSE_8_3_2_INPUT_SCHEMA,
        "clause_8_3_3": CLAUSE_8_3_3_INPUT_SCHEMA,
        "clause_8_3_4": CLAUSE_8_3_4_INPUT_SCHEMA
    },
}


if __name__ == "__main__":
    first = clause_8_1_1(confirmed_items=['外部作业会引起城市轨道交通地下结构出现较大变形，产生结构渗漏水、开裂及破损、错台等病害。'], strict=False)
    print(first.to_dict())
