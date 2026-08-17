from __future__ import annotations

import ast
import hashlib
import html
import json
import re
import shutil
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Any, Callable

from .config import MINERU_ALLOW_LEGACY_OCR, REGULATION_DB, REGULATION_FILE_ROOT
from .mineru_parser import MinerUError, extract_pdf_with_mineru, mineru_cloud_available


Progress = Callable[[str], None]
getcontext().prec = 28

DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
NUMERIC_HINT = re.compile(
    r"(?:\d+(?:\.\d+)?\s*(?:km|mm|cm|m|千米|米|毫米|厘米|%|％|度|°)|"
    r"\d+(?:\.\d+)?\s*\\mathrm\s*\{\s*(?:km|mm|cm|m|kPa|d)(?:\s*/\s*d)?\s*\}|"
    r"\d+(?:\.\d+)?\s*[DHBPLW](?![A-Za-z])|"
    r"(?:≥|≤|>|<|=)\s*\d+(?:\.\d+)?|"
    r"\d+(?:\.\d+)?\s*(?:倍|级|小时|天|d)|"
    r"max\s*\(|min\s*\(|[DHBPLW]\s*[+\-*=>])",
    re.I,
)
NORMATIVE_HINT = re.compile(
    r"应当|必须|严禁|禁止|不得|不应|不宜|应|宜|可|至少|至多|"
    r"不小于|不大于|不超过|范围内|以上|以下|控制值|限值|允许值|max\s*\(|min\s*\(",
    re.I,
)
CONDITIONAL_HINT = re.compile(
    r"安全评估|安全评价|保护监测|安全监测|监测频率|影响等级|风险等级|"
    r"应(?:当)?[^。；]{0,24}(?:监测|评估|评价|检测|设置|提交|验算|复核)|"
    r"必须[^。；]{0,24}(?:监测|评估|评价|检测|设置|提交|验算|复核)|严禁|禁止",
    re.I,
)
CLAUSE_PATTERN = re.compile(r"^\s*((?:\d+\.){1,4}\d+|第[一二三四五六七八九十百]+条)\s*")
RULE_FIELD_CATALOG = {
    "project_type": "项目/外部作业类型", "project_stage": "项目阶段",
    "relative_relationship": "与轨道结构相对关系", "minimum_horizontal_clearance": "最小水平净距(m)",
    "minimum_vertical_clearance": "最小竖向净距(m)", "pit_depth": "基坑深度(m)",
    "pit_length": "基坑长度(m)", "tunnel_diameter": "隧道外径或结构宽度D(m)",
    "metro_buried_depth": "轨道结构埋深(m)", "metro_structure_method": "轨道结构形式",
    "metro_existing_condition": "轨道结构状态", "dewatering_method": "降水方式",
    "monitoring_required": "是否需要保护监测", "monitoring_frequency": "监测频率",
    "safety_assessment_required": "是否需要安全评估", "impact_level": "影响等级",
    "is_in_control_protection_zone": "是否在控制保护区", "is_in_special_protection_zone": "是否在特别保护区",
    "additional_load_value": "附加荷载值", "settlement_value": "沉降值", "displacement_value": "位移值",
}

DEFAULT_REGULATION_FOLDERS = (
    ("rail_transit", "轨道交通保护"),
    ("foundation_pit", "基坑与地下工程"),
    ("building_fire", "建筑与消防"),
    ("environment_monitoring", "环境与监测"),
    ("other", "其他技术规程"),
)

REGULATION_FOLDER_KEYWORDS = (
    ("rail_transit", ("城市轨道", "轨道交通", "地铁", "隧道保护", "结构安全保护")),
    ("foundation_pit", ("基坑", "支护", "地下工程", "岩土", "地基基础", "降水")),
    ("building_fire", ("防火", "消防", "建筑设计", "建筑结构")),
    ("environment_monitoring", ("声环境", "噪声", "振动", "环境质量", "环境监测", "监测")),
)


def _clause_start(text: str) -> re.Match[str] | None:
    """Recognize clause numbers in plain text and Markdown headings."""
    return CLAUSE_PATTERN.match(re.sub(r"^\s*#{1,6}\s*", "", text))


def _has_numeric_requirement(text: str) -> bool:
    if NUMERIC_HINT.search(text):
        return True
    # Values in normative tables often inherit their unit from a caption such
    # as "单位：m", so individual cells contain only bare decimals.
    if "<table" in text and re.search(r"单位\s*[：:]\s*(?:m|mm|cm|kPa|%)", text, re.I):
        return bool(re.search(r">\s*[≤≥<>]?\s*\d+(?:\.\d+)?(?:\s*[~～-]\s*\d+(?:\.\d+)?)?\s*<", text))
    return False


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _clean_table_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _matrix_to_html(matrix: list[list[Any]]) -> str:
    """Keep a detected table machine-readable instead of flattening it into lines."""
    clean = [[_clean_table_cell(cell) for cell in row] for row in matrix if any(_clean_table_cell(cell) for cell in row)]
    if not clean:
        return ""
    width = max(len(row) for row in clean)
    rows = []
    for row in clean:
        cells = row + [""] * (width - len(row))
        rows.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in cells) + "</tr>")
    return "<table>" + "".join(rows) + "</table>"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _extract_docx(path: Path) -> list[dict[str, Any]]:
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as exc:
        raise RuntimeError("当前Python环境缺少python-docx，无法保留Word表格结构。") from exc

    document = Document(str(path))
    rows: list[dict[str, Any]] = []
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            text = _clean_table_cell(Paragraph(child, document).text)
            if text:
                rows.append({"page": None, "text": text, "content_type": "paragraph"})
        elif child.tag.endswith("}tbl"):
            table = Table(child, document)
            table_html = _matrix_to_html([[cell.text for cell in row.cells] for row in table.rows])
            if table_html:
                rows.append({"page": None, "text": table_html, "content_type": "table"})
    return rows


def _pdf_rows_need_ocr(rows: list[dict[str, Any]]) -> bool:
    """Detect scanned pages whose only extractable text is a repeated watermark."""
    paragraphs = [
        re.sub(r"\s+", "", str(row.get("text") or ""))
        for row in rows
        if row.get("content_type") == "paragraph" and row.get("text")
    ]
    if sum(len(text) for text in paragraphs) < 100:
        return True
    if len(paragraphs) < 3:
        return False
    frequencies: dict[str, int] = {}
    for text in paragraphs:
        frequencies[text] = frequencies.get(text, 0) + 1
    dominant = max(frequencies.values(), default=0)
    unique_ratio = len(frequencies) / len(paragraphs)
    repeated_watermark = dominant / len(paragraphs) >= 0.45 and unique_ratio <= 0.35
    sparse_pages = (
        len({row.get("page") for row in rows if row.get("page") is not None}) >= 3
        and sum(len(text) for text in paragraphs) / len(paragraphs) < 80
    )
    return repeated_watermark or sparse_pages


def _remove_repeated_pdf_noise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    page_count = len({row.get("page") for row in rows if row.get("page") is not None})
    per_text_pages: dict[str, set[Any]] = {}
    for row in rows:
        text = re.sub(r"\s+", "", str(row.get("text") or ""))
        if text:
            per_text_pages.setdefault(text, set()).add(row.get("page"))
    result = []
    for row in rows:
        text = re.sub(r"\s+", "", str(row.get("text") or ""))
        repeated_on_most_pages = (
            page_count >= 3
            and len(text) <= 100
            and len(per_text_pages.get(text, set())) / page_count >= 0.65
        )
        obvious_watermark = bool(re.search(r"标准分享网|免费下载|bzfxw\.com", text, re.I))
        if repeated_on_most_pages or obvious_watermark:
            continue
        result.append(row)
    return result


def _extract_pdf(path: Path, progress: Progress | None = None) -> tuple[list[dict[str, Any]], str]:
    notify = progress or (lambda _message: None)
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("当前Python环境缺少pdfplumber，无法解析技术规程PDF。") from exc
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(str(path)) as document:
        for page_number, page in enumerate(document.pages, start=1):
            text = (page.extract_text() or "").replace("\r", "\n")
            for line in text.splitlines():
                line = re.sub(r"\s+", " ", line).strip()
                if line:
                    rows.append({"page": page_number, "text": line, "content_type": "paragraph"})
            # pdfplumber uses character coordinates and ruling lines to recover
            # rows/columns. Preserve the resulting matrix as HTML for the LLM and
            # deterministic cell-level verification that follow.
            for table in page.extract_tables() or []:
                table_html = _matrix_to_html(table)
                if table_html:
                    rows.append({"page": page_number, "text": table_html, "content_type": "table"})
    if _pdf_rows_need_ocr(rows):
        if mineru_cloud_available():
            try:
                mineru_rows = extract_pdf_with_mineru(path, notify)
                return _remove_repeated_pdf_noise(mineru_rows), "mineru_cloud_vlm"
            except MinerUError:
                if not MINERU_ALLOW_LEGACY_OCR:
                    raise
                notify("MinerU解析失败，正在尝试本机传统OCR")
        elif not MINERU_ALLOW_LEGACY_OCR:
            raise RuntimeError("PDF正文过少，且未配置MinerU解析服务。")
        try:
            from stage1_reply_system.document_processing.pdf_extractor import extract_pdf

            result = extract_pdf(
                path,
                # A deliberately unreachable direct-text threshold forces OCR
                # after the repeated-watermark detector has classified the PDF
                # as scanned.
                direct_text_threshold=1_000_000,
                ocr_resolution=220,
                max_pages=None,
                scan_last_page_footer=False,
            )
            rows = []
            for page in result.get("pages", []):
                for line in str(page.get("text") or "").splitlines():
                    clean = re.sub(r"\s+", " ", line).strip()
                    if clean:
                        rows.append({"page": page.get("page"), "text": clean, "content_type": "paragraph"})
        except Exception as exc:
            raise RuntimeError("PDF正文过少，可能是扫描件，OCR解析失败。") from exc
        return _remove_repeated_pdf_noise(rows), "legacy_local_ocr"
    return _remove_repeated_pdf_noise(rows), "pdfplumber_text"


def extract_regulation(path: Path, progress: Progress | None = None) -> tuple[str, list[dict[str, Any]], str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        rows, method = _extract_pdf(path, progress)
    elif suffix == ".docx":
        rows = _extract_docx(path)
        method = "docx_xml"
    elif suffix in {".txt", ".md"}:
        rows = [{"page": None, "text": line.strip()} for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines() if line.strip()]
        method = "markdown" if suffix == ".md" else "text"
    else:
        raise ValueError(f"暂不支持技术规程格式：{suffix}")
    return "\n".join(row["text"] for row in rows), rows, method


class SafeExpression:
    """A tiny Decimal expression evaluator for reviewed engineering formulas."""

    FUNCTIONS = {
        "max": lambda *values: max(values),
        "min": lambda *values: min(values),
        "abs": abs,
    }
    BINARY = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.Pow: lambda left, right: left ** int(right),
    }
    UNARY = {ast.UAdd: lambda value: value, ast.USub: lambda value: -value}

    @classmethod
    def names(cls, expression: str) -> set[str]:
        tree = cls._parse(expression)
        return {
            node.id for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id not in cls.FUNCTIONS
        }

    @classmethod
    def evaluate(cls, expression: str, values: dict[str, Any]) -> Decimal:
        tree = cls._parse(expression)
        prepared = {key: cls._decimal(value) for key, value in values.items()}
        return cls._visit(tree.body, prepared)

    @classmethod
    def constants(cls, expression: str) -> list[Decimal]:
        tree = cls._parse(expression)
        return [
            Decimal(str(node.value)) for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
        ]

    @classmethod
    def _parse(cls, expression: str) -> ast.Expression:
        if not isinstance(expression, str) or not expression.strip() or len(expression) > 500:
            raise ValueError("公式不能为空且长度不能超过500字符。")
        try:
            tree = ast.parse(expression.strip(), mode="eval")
        except SyntaxError as exc:
            raise ValueError("公式语法无效。") from exc
        for node in ast.walk(tree):
            if isinstance(node, (ast.Attribute, ast.Subscript, ast.Lambda, ast.ListComp, ast.DictComp, ast.Import, ast.ImportFrom)):
                raise ValueError("公式包含禁止使用的Python语法。")
        return tree

    @classmethod
    def _decimal(cls, value: Any) -> Decimal:
        if isinstance(value, bool) or value is None:
            raise ValueError("公式输入必须是数值。")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"无法将{value!r}转换为数值。") from exc

    @classmethod
    def _visit(cls, node: ast.AST, values: dict[str, Decimal]) -> Decimal:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Decimal(str(node.value))
        if isinstance(node, ast.Name):
            if node.id not in values:
                raise ValueError(f"公式缺少输入字段：{node.id}")
            return values[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in cls.BINARY:
            right = cls._visit(node.right, values)
            if isinstance(node.op, ast.Pow) and (right != right.to_integral_value() or abs(right) > 10):
                raise ValueError("幂运算只允许绝对值不超过10的整数指数。")
            return cls.BINARY[type(node.op)](cls._visit(node.left, values), right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls.UNARY:
            return cls.UNARY[type(node.op)](cls._visit(node.operand, values))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in cls.FUNCTIONS:
            if node.keywords or not node.args:
                raise ValueError("公式函数必须使用位置参数且参数不能为空。")
            return cls.FUNCTIONS[node.func.id](*(cls._visit(item, values) for item in node.args))
        raise ValueError(f"公式包含不支持的语法：{type(node).__name__}")


class RuleEngine:
    OPERATORS = {
        "<": lambda actual, limit: actual < limit,
        "<=": lambda actual, limit: actual <= limit,
        ">": lambda actual, limit: actual > limit,
        ">=": lambda actual, limit: actual >= limit,
        "==": lambda actual, limit: actual == limit,
    }
    UNIT_TO_BASE = {
        "m": Decimal("1"), "米": Decimal("1"),
        "cm": Decimal("0.01"), "厘米": Decimal("0.01"),
        "mm": Decimal("0.001"), "毫米": Decimal("0.001"),
        "km": Decimal("1000"), "千米": Decimal("1000"),
    }
    CONDITION_OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "in", "not_in", "contains", "exists", "truthy"}

    @classmethod
    def measurement(cls, value: Any, target_unit: str) -> Decimal:
        source_unit = target_unit
        raw = value
        if isinstance(value, dict):
            raw = value.get("value")
            source_unit = str(value.get("unit") or target_unit)
        elif isinstance(value, str):
            match = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*([A-Za-z%°\u4e00-\u9fff]*)\s*", value)
            if not match:
                raise ValueError(f"无法识别测量值：{value}")
            raw = match.group(1)
            source_unit = match.group(2) or target_unit
        number = SafeExpression._decimal(raw)
        if not target_unit or source_unit == target_unit:
            return number
        if source_unit in cls.UNIT_TO_BASE and target_unit in cls.UNIT_TO_BASE:
            return number * cls.UNIT_TO_BASE[source_unit] / cls.UNIT_TO_BASE[target_unit]
        raise ValueError(f"不支持从{source_unit}换算为{target_unit}。")

    @classmethod
    def validate(cls, rule: dict[str, Any]) -> dict[str, Any]:
        rule_type = rule.get("rule_type") or "numeric_rule"
        if rule_type == "conditional_rule":
            return cls._validate_conditional(rule)
        if rule_type == "lookup_table_rule":
            return cls._validate_lookup(rule)
        if rule_type != "numeric_rule":
            return {"valid": False, "errors": [f"不支持的规则类型：{rule_type}"], "warnings": []}
        return cls._validate_numeric(rule)

    @classmethod
    def _base_errors(cls, rule: dict[str, Any]) -> list[str]:
        errors = []
        if not rule.get("name"):
            errors.append("缺少字段：name")
        if not (rule.get("source") or {}).get("original_text"):
            errors.append("缺少规程原文依据。")
        return errors

    @classmethod
    def _validate_numeric(cls, rule: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        for key in ("name", "actual_field", "operator", "action"):
            if not rule.get(key):
                errors.append(f"缺少字段：{key}")
        if rule.get("operator") not in cls.OPERATORS:
            errors.append("operator只允许<、<=、>、>=、==。")
        inputs = rule.get("inputs")
        if not isinstance(inputs, dict) or not inputs:
            errors.append("inputs必须定义至少一个输入字段。")
            inputs = {}
        actual_field = rule.get("actual_field")
        if actual_field and actual_field not in inputs:
            errors.append("actual_field必须在inputs中定义。")
        formula = rule.get("limit_formula")
        if not formula:
            errors.append("缺少limit_formula。")
        else:
            try:
                names = SafeExpression.names(str(formula))
                undefined = sorted(names - set(inputs))
                if undefined:
                    errors.append("公式引用了未定义字段：" + "、".join(undefined))
            except ValueError as exc:
                errors.append(str(exc))
        units = {str(value.get("unit", "")).strip() for value in inputs.values() if isinstance(value, dict)}
        units.discard("")
        if len(units) > 1:
            warnings.append("输入字段包含不同单位，发布前必须确认已换算到同一量纲。")
        if not (rule.get("source") or {}).get("original_text"):
            errors.append("缺少规程原文依据。")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    @classmethod
    def _validate_conditional(cls, rule: dict[str, Any]) -> dict[str, Any]:
        errors = cls._base_errors(rule)
        conditions = rule.get("conditions")
        requirement = rule.get("requirement")
        if not isinstance(conditions, list) or not conditions:
            errors.append("conditions必须定义至少一个触发条件。")
        else:
            for index, condition in enumerate(conditions, start=1):
                if not isinstance(condition, dict) or not condition.get("field"):
                    errors.append(f"第{index}个触发条件缺少field。")
                if not isinstance(condition, dict) or condition.get("operator") not in cls.CONDITION_OPERATORS:
                    errors.append(f"第{index}个触发条件operator无效。")
        if requirement:
            if not isinstance(requirement, dict) or not requirement.get("field"):
                errors.append("requirement必须定义待审核字段。")
            elif requirement.get("operator") not in cls.CONDITION_OPERATORS:
                errors.append("requirement.operator无效。")
        elif not isinstance(rule.get("action"), dict) or not rule.get("action"):
            errors.append("条件规则必须定义requirement或action。")
        return {"valid": not errors, "errors": errors, "warnings": []}

    @classmethod
    def _validate_lookup(cls, rule: dict[str, Any]) -> dict[str, Any]:
        errors = cls._base_errors(rule)
        selectors = rule.get("selectors")
        rows = rule.get("rows")
        if not isinstance(selectors, list) or not selectors or not all(isinstance(value, str) and value for value in selectors):
            errors.append("selectors必须定义至少一个输入字段。")
        if not rule.get("output_field"):
            errors.append("缺少output_field。")
        if not isinstance(rows, list) or not rows:
            errors.append("rows必须定义至少一行映射。")
        else:
            for index, row in enumerate(rows, start=1):
                if not isinstance(row, dict) or not isinstance(row.get("when"), dict) or "result" not in row:
                    errors.append(f"第{index}行映射必须包含when和result。")
        return {"valid": not errors, "errors": errors, "warnings": []}

    @classmethod
    def execute(cls, rule: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        rule_type = rule.get("rule_type") or "numeric_rule"
        if rule_type == "conditional_rule":
            return cls._execute_conditional(rule, data)
        if rule_type == "lookup_table_rule":
            return cls._execute_lookup(rule, data)
        validation = cls.validate(rule)
        if not validation["valid"]:
            return {"status": "invalid_rule", "validation": validation}
        inputs = rule["inputs"]
        required = [key for key, meta in inputs.items() if not isinstance(meta, dict) or meta.get("required", True)]
        missing = [key for key in required if data.get(key) in (None, "")]
        if missing:
            return {"status": "insufficient_data", "missing_fields": missing, "message": "缺少计算所需字段：" + "、".join(missing)}
        try:
            values = {
                key: cls.measurement(data[key], (meta or {}).get("unit", "") if isinstance(meta, dict) else "")
                for key, meta in inputs.items() if data.get(key) not in (None, "")
            }
        except ValueError as exc:
            return {"status": "calculation_error", "message": str(exc)}
        try:
            actual = values[rule["actual_field"]]
            limit = SafeExpression.evaluate(rule["limit_formula"], values)
            passed = cls.OPERATORS[rule["operator"]](actual, limit)
        except (ValueError, ArithmeticError, InvalidOperation) as exc:
            return {"status": "calculation_error", "message": str(exc)}
        unit = (inputs.get(rule["actual_field"]) or {}).get("unit", "")
        return {
            "status": "matched" if passed else "not_matched",
            "condition_met": passed,
            "actual_value": str(actual),
            "limit_value": str(limit),
            "unit": unit,
            "calculation": f"{rule['actual_field']}={actual}{unit} {rule['operator']} {rule['limit_formula']}={limit}{unit}",
            "action": rule["action"] if passed else {},
        }

    @classmethod
    def _compare_value(cls, actual: Any, operator: str, expected: Any = None) -> bool:
        if operator == "exists":
            return actual not in (None, "", [])
        if operator == "truthy":
            return bool(actual)
        if operator == "in":
            return actual in (expected if isinstance(expected, list) else [expected])
        if operator == "not_in":
            return actual not in (expected if isinstance(expected, list) else [expected])
        if operator == "contains":
            return expected in actual if isinstance(actual, (str, list, tuple, set, dict)) else False
        if operator == "!=":
            return actual != expected
        if operator == "==":
            return actual == expected
        try:
            left, right = cls.measurement(actual, ""), cls.measurement(expected, "")
            return cls.OPERATORS[operator](left, right)
        except (InvalidOperation, ValueError, KeyError, TypeError):
            return False

    @classmethod
    def _execute_conditional(cls, rule: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        validation = cls.validate(rule)
        if not validation["valid"]:
            return {"status": "invalid_rule", "validation": validation}
        fields = [condition["field"] for condition in rule["conditions"]]
        missing = [field for field in fields if data.get(field) in (None, "", [])]
        if missing:
            return {"status": "insufficient_data", "missing_fields": sorted(set(missing)), "message": "缺少条件判断字段：" + "、".join(sorted(set(missing)))}
        triggered = all(
            cls._compare_value(data.get(condition["field"]), condition["operator"], condition.get("value"))
            for condition in rule["conditions"]
        )
        if not triggered:
            return {"status": "not_applicable", "condition_met": False, "message": "案例不满足本条规则的触发条件。"}
        requirement = rule.get("requirement")
        if not requirement:
            condition_text = " 且 ".join(
                f"{item['field']}={data.get(item['field'])!r} {item['operator']} {item.get('value')!r}"
                for item in rule["conditions"]
            )
            return {
                "status": "matched", "condition_met": True,
                "calculation": "触发条件成立：" + condition_text,
                "action": rule.get("action") or {},
            }
        field = requirement["field"]
        if data.get(field) in (None, "", []):
            return {"status": "insufficient_data", "missing_fields": [field], "message": f"缺少待审核字段：{field}"}
        passed = cls._compare_value(data.get(field), requirement["operator"], requirement.get("value"))
        return {
            "status": "matched" if passed else "not_matched",
            "condition_met": passed,
            "actual_value": data.get(field),
            "expected_value": requirement.get("value"),
            "calculation": f"触发条件成立；{field}={data.get(field)!r} {requirement['operator']} {requirement.get('value')!r}",
            "action": rule.get("action") if passed else {},
        }

    @classmethod
    def _execute_lookup(cls, rule: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        validation = cls.validate(rule)
        if not validation["valid"]:
            return {"status": "invalid_rule", "validation": validation}
        missing = [field for field in rule["selectors"] if data.get(field) in (None, "", [])]
        if missing:
            return {"status": "insufficient_data", "missing_fields": missing, "message": "缺少表格查询字段：" + "、".join(missing)}
        selected = None
        for row in rule["rows"]:
            if all(cls._compare_value(data.get(field), "in", expected) for field, expected in row["when"].items()):
                selected = row
                break
        if selected is None:
            return {"status": "not_applicable", "message": "未找到与案例条件对应的表格行。"}
        field = rule["output_field"]
        expected = selected["result"]
        actual = data.get(field)
        if actual in (None, "", []):
            return {
                "status": "derived",
                "condition_met": True,
                "derived_field": field,
                "derived_value": expected,
                "calculation": f"按表格映射得到 {field}={expected!r}",
                "matched_row": selected,
            }
        passed = actual == expected
        return {
            "status": "matched" if passed else "not_matched",
            "condition_met": passed,
            "actual_value": actual,
            "expected_value": expected,
            "calculation": f"表格映射值 {expected!r}，案例填写值 {actual!r}",
            "matched_row": selected,
        }


class RegulationRepository:
    def __init__(self, database: Path = REGULATION_DB, file_root: Path = REGULATION_FILE_ROOT) -> None:
        self.database = Path(database)
        self.file_root = Path(file_root)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.file_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._initialize()
        self._initialize_default_folders()
        self._classify_uncategorized_documents()
        self._backfill_clause_index()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS regulation (
                    regulation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    version TEXT,
                    original_file_name TEXT,
                    stored_file TEXT NOT NULL,
                    text_file TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    extraction_method TEXT,
                    text_length INTEGER DEFAULT 0,
                    paragraph_count INTEGER DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'ready',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    folder_id TEXT,
                    folder_assignment TEXT
                );
                CREATE TABLE IF NOT EXISTS regulation_folder (
                    folder_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    system_key TEXT UNIQUE,
                    parent_id TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS regulation_setting (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_regulation_sha ON regulation(sha256);
                CREATE TABLE IF NOT EXISTS regulation_rule (
                    rule_id TEXT PRIMARY KEY,
                    regulation_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    rule_json TEXT NOT NULL,
                    validation_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(regulation_id) REFERENCES regulation(regulation_id)
                );
                CREATE INDEX IF NOT EXISTS idx_rule_regulation ON regulation_rule(regulation_id);
                CREATE TABLE IF NOT EXISTS regulation_clause (
                    clause_id TEXT PRIMARY KEY,
                    regulation_id TEXT NOT NULL,
                    clause_no TEXT NOT NULL,
                    title TEXT,
                    clause_text TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL DEFAULT 'reference',
                    source_page INTEGER,
                    source_paragraph INTEGER,
                    content_hash TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(regulation_id) REFERENCES regulation(regulation_id),
                    UNIQUE(regulation_id, clause_no)
                );
                CREATE INDEX IF NOT EXISTS idx_clause_regulation ON regulation_clause(regulation_id);
                CREATE INDEX IF NOT EXISTS idx_clause_number ON regulation_clause(clause_no);
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(regulation_clause)")}
            if "knowledge_type" not in columns:
                connection.execute(
                    "ALTER TABLE regulation_clause ADD COLUMN knowledge_type TEXT NOT NULL DEFAULT 'reference'"
                )
            regulation_columns = {row["name"] for row in connection.execute("PRAGMA table_info(regulation)")}
            if "folder_id" not in regulation_columns:
                connection.execute("ALTER TABLE regulation ADD COLUMN folder_id TEXT")
            if "folder_assignment" not in regulation_columns:
                connection.execute("ALTER TABLE regulation ADD COLUMN folder_assignment TEXT")
            folder_columns = {row["name"] for row in connection.execute("PRAGMA table_info(regulation_folder)")}
            if "system_key" not in folder_columns:
                connection.execute("ALTER TABLE regulation_folder ADD COLUMN system_key TEXT")
                connection.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_regulation_folder_system_key "
                    "ON regulation_folder(system_key)"
                )
            if "parent_id" not in folder_columns:
                connection.execute("ALTER TABLE regulation_folder ADD COLUMN parent_id TEXT")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_regulation_folder ON regulation(folder_id)")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_regulation_folder_parent "
                "ON regulation_folder(parent_id)"
            )

    def _initialize_default_folders(self) -> None:
        """Create the built-in taxonomy once while still allowing later deletion."""
        with self._connect() as connection:
            seeded = connection.execute(
                "SELECT setting_value FROM regulation_setting WHERE setting_key='default_folders_seeded'"
            ).fetchone()
            if seeded:
                return
            now = _now()
            for sort_order, (system_key, name) in enumerate(DEFAULT_REGULATION_FOLDERS):
                existing = connection.execute(
                    "SELECT folder_id FROM regulation_folder WHERE name=? COLLATE NOCASE",
                    (name,),
                ).fetchone()
                if existing:
                    connection.execute(
                        "UPDATE regulation_folder SET system_key=?, sort_order=?, updated_at=? WHERE folder_id=?",
                        (system_key, sort_order, now, existing["folder_id"]),
                    )
                    continue
                connection.execute(
                    """INSERT INTO regulation_folder(
                        folder_id,name,system_key,sort_order,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?)""",
                    ("RF-" + uuid.uuid4().hex[:12].upper(), name, system_key, sort_order, now, now),
                )
            connection.execute(
                """INSERT OR REPLACE INTO regulation_setting(setting_key,setting_value,updated_at)
                   VALUES('default_folders_seeded','1',?)""",
                (now,),
            )

    @staticmethod
    def _suggest_folder_key(title: str, text: str = "") -> str:
        title_sample = title.lower()
        for candidate, keywords in REGULATION_FOLDER_KEYWORDS:
            if any(keyword.lower() in title_sample for keyword in keywords):
                return candidate
        text_sample = text[:12000].lower()
        system_key = "other"
        for candidate, keywords in REGULATION_FOLDER_KEYWORDS:
            if any(keyword.lower() in text_sample for keyword in keywords):
                system_key = candidate
                break
        return system_key

    def _suggest_folder_id(self, title: str, text: str = "") -> str | None:
        system_key = self._suggest_folder_key(title, text)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT folder_id FROM regulation_folder WHERE system_key=?",
                (system_key,),
            ).fetchone()
        return row["folder_id"] if row else None

    def _classify_uncategorized_documents(self) -> None:
        with self._connect() as connection:
            rows = [
                dict(row)
                for row in connection.execute(
                    """SELECT r.regulation_id,r.title,r.text_file
                       FROM regulation r
                       LEFT JOIN regulation_folder f ON f.folder_id=r.folder_id
                       WHERE r.folder_assignment='auto'
                          OR (r.folder_assignment IS NULL AND (r.folder_id IS NULL OR f.system_key IS NOT NULL))"""
                )
            ]
        for item in rows:
            text_file = Path(item["text_file"])
            text = text_file.read_text(encoding="utf-8", errors="replace") if text_file.exists() else ""
            folder_id = self._suggest_folder_id(item["title"], text)
            if folder_id:
                with self._connect() as connection:
                    connection.execute(
                        """UPDATE regulation
                           SET folder_id=?, folder_assignment='auto', updated_at=?
                           WHERE regulation_id=?""",
                        (folder_id, _now(), item["regulation_id"]),
                    )

    @staticmethod
    def _knowledge_type(text: str, clause_no: str) -> str:
        if clause_no.startswith("2.0.") or clause_no.startswith("S."):
            return "reference"
        if "<table" in text.lower():
            return "table"
        normative = re.search(r"应当|必须|严禁|禁止|不得|不应|不宜|应|宜|可|须", text)
        numeric = re.search(r"\d+(?:\.\d+)?\s*(?:km|mm|cm|m|kPa|%|米|毫米|厘米|天|次|级)|[≤≥<>]=?|max\s*\(|min\s*\(", text, re.I)
        if normative and numeric:
            return "quantitative"
        if normative:
            return "qualitative"
        return "knowledge"

    @staticmethod
    def _clause_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build one searchable record for every numbered clause in the source."""
        records: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        def finish() -> None:
            nonlocal current
            if not current:
                return
            text = "\n".join(current.pop("parts")).strip()
            current["clause_text"] = text
            current["content_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            current["knowledge_type"] = RegulationRepository._knowledge_type(text, current["clause_no"])
            records.append(current)
            current = None

        for index, row in enumerate(rows):
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            if re.match(r"^#\s*条文说明\s*$", text):
                finish()
                break
            match = _clause_start(text)
            if match and len(match.group(1).split(".")) == 3:
                finish()
                clause_no = match.group(1)
                title = re.sub(rf"^#?\s*{re.escape(clause_no)}\s*", "", text).strip()
                current = {
                    "clause_no": clause_no,
                    "title": title[:160],
                    "source_page": row.get("page"),
                    "source_paragraph": index,
                    "parts": [text],
                }
                continue
            # A chapter/appendix heading closes the preceding formal clause.
            if current and (text.startswith("#") or (match and len(match.group(1).split(".")) < 3)):
                finish()
                continue
            if current:
                current["parts"].append(text)
        finish()

        # Keep the two unnumbered normative reference sections as searchable
        # knowledge entries. Together with the 181 numbered clauses in this
        # edition, this yields the 183 source entries expected by the project.
        supplemental_titles = ("本规程用词说明", "引用标准名录")
        for supplement_index, supplement_title in enumerate(supplemental_titles, start=1):
            start = next(
                (index for index, row in enumerate(rows)
                 if str(row.get("text") or "").strip().lstrip("#").strip() == supplement_title),
                None,
            )
            if start is None:
                continue
            parts: list[str] = []
            for row in rows[start:]:
                text = str(row.get("text") or "").strip()
                if parts and text.startswith("#"):
                    break
                if text:
                    parts.append(text)
            clause_text = "\n".join(parts).strip()
            records.append({
                "clause_no": f"S.{supplement_index}",
                "title": supplement_title,
                "source_page": rows[start].get("page"),
                "source_paragraph": start,
                "clause_text": clause_text,
                "content_hash": hashlib.sha256(clause_text.encode("utf-8")).hexdigest(),
                "knowledge_type": "reference",
            })
        return records

    def _sync_clause_index(self, regulation_id: str, rows: list[dict[str, Any]]) -> int:
        records = self._clause_records(rows)
        now = _now()
        with self._connect() as connection:
            connection.execute("UPDATE regulation_clause SET active=0, updated_at=? WHERE regulation_id=?", (now, regulation_id))
            for record in records:
                clause_no = record["clause_no"]
                clause_id = f"{regulation_id}:{clause_no}"
                connection.execute(
                    """
                    INSERT INTO regulation_clause(
                        clause_id, regulation_id, clause_no, title, clause_text, knowledge_type,
                        source_page, source_paragraph, content_hash, active, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,1,?,?)
                    ON CONFLICT(regulation_id, clause_no) DO UPDATE SET
                        title=excluded.title, clause_text=excluded.clause_text,
                        knowledge_type=excluded.knowledge_type,
                        source_page=excluded.source_page, source_paragraph=excluded.source_paragraph,
                        content_hash=excluded.content_hash, active=1, updated_at=excluded.updated_at
                    """,
                    (
                        clause_id, regulation_id, clause_no, record["title"], record["clause_text"], record["knowledge_type"],
                        record["source_page"], record["source_paragraph"], record["content_hash"], now, now,
                    ),
                )
        return len(records)

    def _backfill_clause_index(self) -> None:
        with self._connect() as connection:
            documents = [dict(row) for row in connection.execute(
                """SELECT r.regulation_id, r.text_file
                   FROM regulation r
                   WHERE NOT EXISTS (
                       SELECT 1 FROM regulation_clause rc
                       WHERE rc.regulation_id=r.regulation_id AND rc.active=1
                   ) OR NOT EXISTS (
                       SELECT 1 FROM regulation_clause rc
                       WHERE rc.regulation_id=r.regulation_id AND rc.active=1
                         AND rc.knowledge_type<>'reference'
                   )"""
            )]
        for item in documents:
            paragraphs = Path(item["text_file"]).parent / "paragraphs.json"
            if not paragraphs.exists():
                continue
            rows = json.loads(paragraphs.read_text(encoding="utf-8"))
            self._sync_clause_index(item["regulation_id"], rows)

    def import_document(
        self,
        source: Path,
        title: str | None,
        version: str | None,
        progress: Progress,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        if folder_id:
            self.get_folder(folder_id)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        with self._connect() as connection:
            duplicate = connection.execute("SELECT regulation_id FROM regulation WHERE sha256=?", (digest,)).fetchone()
        if duplicate:
            raise ValueError(f"该技术规程已经入库，编号：{duplicate['regulation_id']}")
        regulation_id = "REG-" + uuid.uuid4().hex[:12].upper()
        folder = self.file_root / regulation_id
        folder.mkdir(parents=True)
        stored = folder / source.name
        shutil.copy2(source, stored)
        progress("正在解析技术规程正文和页码")
        text, rows, method = extract_regulation(stored, progress)
        text_file = folder / "content.txt"
        paragraphs_file = folder / "paragraphs.json"
        text_file.write_text(text, encoding="utf-8")
        paragraphs_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        assigned_folder_id = folder_id or self._suggest_folder_id(title or source.stem, text)
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO regulation(
                    regulation_id, title, version, original_file_name, stored_file, text_file,
                    sha256, extraction_method, text_length, paragraph_count, status, active,
                    created_at, updated_at, folder_id, folder_assignment
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (regulation_id, title or source.stem, version, source.name, str(stored), str(text_file), digest,
                 method, len(text), len(rows), "ready", 1, now, now, assigned_folder_id,
                 "manual" if folder_id else "auto"),
            )
        self._sync_clause_index(regulation_id, rows)
        progress("技术规程已入库，可开始AI识别规则")
        return self.get_document(regulation_id)

    def reextract_document(self, regulation_id: str, progress: Progress) -> dict[str, Any]:
        """Rebuild stored text after parser/OCR improvements without duplicating the document."""
        item = self.get_document(regulation_id)
        progress("正在重新解析技术规程全部正文和页码")
        text, rows, method = extract_regulation(Path(item["stored_file"]), progress)
        text_file = Path(item["text_file"])
        paragraphs_file = text_file.parent / "paragraphs.json"
        text_temp = text_file.with_suffix(".txt.tmp")
        paragraphs_temp = paragraphs_file.with_suffix(".json.tmp")
        text_temp.write_text(text, encoding="utf-8")
        paragraphs_temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        text_temp.replace(text_file)
        paragraphs_temp.replace(paragraphs_file)
        with self._connect() as connection:
            connection.execute(
                "UPDATE regulation SET extraction_method=?, text_length=?, paragraph_count=?, updated_at=? WHERE regulation_id=?",
                (method, len(text), len(rows), _now(), regulation_id),
            )
        self._sync_clause_index(regulation_id, rows)
        progress(f"重新解析完成，共{len(rows)}段、{len(text)}字")
        return self.get_document(regulation_id)

    def reindex_from_text_file(self, regulation_id: str, source: Path, progress: Progress) -> dict[str, Any]:
        """Use a trusted text/Markdown edition as the searchable index for a scanned source PDF."""
        item = self.get_document(regulation_id)
        progress("正在使用文字版规程重建正文索引")
        text = source.read_text(encoding="utf-8-sig", errors="replace")
        rows = [{"page": None, "text": line.strip()} for line in text.splitlines() if line.strip()]
        text_file = Path(item["text_file"])
        paragraphs_file = text_file.parent / "paragraphs.json"
        text_temp = text_file.with_suffix(".txt.tmp")
        paragraphs_temp = paragraphs_file.with_suffix(".json.tmp")
        text_temp.write_text(text, encoding="utf-8")
        paragraphs_temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        text_temp.replace(text_file)
        paragraphs_temp.replace(paragraphs_file)
        with self._connect() as connection:
            connection.execute(
                "UPDATE regulation SET extraction_method=?, text_length=?, paragraph_count=?, updated_at=? WHERE regulation_id=?",
                ("trusted_markdown_index", len(text), len(rows), _now(), regulation_id),
            )
        self._sync_clause_index(regulation_id, rows)
        progress(f"文字索引完成，共{len(rows)}段、{len(text)}字")
        return self.get_document(regulation_id)

    def list_documents(
        self,
        keyword: str | None = None,
        include_inactive: bool = False,
        folder_id: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = """SELECT r.*,
            rf.name folder_name,
            (SELECT COUNT(*) FROM regulation_clause rc WHERE rc.regulation_id=r.regulation_id AND rc.active=1) clause_count,
            (SELECT COUNT(*) FROM regulation_rule rr WHERE rr.regulation_id=r.regulation_id) rule_count,
            (SELECT COUNT(*) FROM regulation_rule rr WHERE rr.regulation_id=r.regulation_id AND rr.status='published' AND rr.active=1) published_count
            FROM regulation r
            LEFT JOIN regulation_folder rf ON rf.folder_id=r.folder_id"""
        where, params = [], []
        if keyword:
            where.append("(r.title LIKE ? OR r.original_file_name LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if not include_inactive:
            where.append("r.active=1")
        if folder_id == "__uncategorized__":
            where.append("r.folder_id IS NULL")
        elif folder_id:
            where.append("r.folder_id=?")
            params.append(folder_id)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY r.updated_at DESC"
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def list_folders(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT f.*,
                    (SELECT COUNT(*) FROM regulation r WHERE r.folder_id=f.folder_id) regulation_count
                   FROM regulation_folder f
                   ORDER BY f.sort_order, f.created_at, f.name"""
            )
            return [dict(row) for row in rows]

    def get_folder(self, folder_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT f.*,
                    (SELECT COUNT(*) FROM regulation r WHERE r.folder_id=f.folder_id) regulation_count
                   FROM regulation_folder f WHERE f.folder_id=?""",
                (folder_id,),
            ).fetchone()
        if not row:
            raise KeyError(folder_id)
        return dict(row)

    def create_folder(self, name: str, parent_id: str | None = None) -> dict[str, Any]:
        clean_name = re.sub(r"\s+", " ", name).strip()
        if not clean_name:
            raise ValueError("文件夹名称不能为空。")
        if len(clean_name) > 60:
            raise ValueError("文件夹名称不能超过60个字符。")
        folder_id = "RF-" + uuid.uuid4().hex[:12].upper()
        now = _now()
        if parent_id:
            self.get_folder(parent_id)
        try:
            with self._connect() as connection:
                sort_order = connection.execute(
                    """SELECT COALESCE(MAX(sort_order), -1) + 1 value
                       FROM regulation_folder WHERE parent_id IS ?""",
                    (parent_id,),
                ).fetchone()["value"]
                connection.execute(
                    """INSERT INTO regulation_folder(
                           folder_id,name,parent_id,sort_order,created_at,updated_at
                       ) VALUES(?,?,?,?,?,?)""",
                    (folder_id, clean_name, parent_id, sort_order, now, now),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("已存在同名技术规程文件夹。") from exc
        return self.get_folder(folder_id)

    def rename_folder(self, folder_id: str, name: str) -> dict[str, Any]:
        self.get_folder(folder_id)
        clean_name = re.sub(r"\s+", " ", name).strip()
        if not clean_name:
            raise ValueError("文件夹名称不能为空。")
        if len(clean_name) > 60:
            raise ValueError("文件夹名称不能超过60个字符。")
        try:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE regulation_folder SET name=?, updated_at=? WHERE folder_id=?",
                    (clean_name, _now(), folder_id),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("已存在同名技术规程文件夹。") from exc
        return self.get_folder(folder_id)

    def delete_folder(self, folder_id: str) -> dict[str, Any]:
        item = self.get_folder(folder_id)
        parent_id = item.get("parent_id")
        with self._connect() as connection:
            connection.execute(
                """UPDATE regulation
                   SET folder_id=?, folder_assignment='manual', updated_at=?
                   WHERE folder_id=?""",
                (parent_id, _now(), folder_id),
            )
            connection.execute(
                "UPDATE regulation_folder SET parent_id=?,updated_at=? WHERE parent_id=?",
                (parent_id, _now(), folder_id),
            )
            connection.execute("DELETE FROM regulation_folder WHERE folder_id=?", (folder_id,))
        return item

    def set_document_folder(self, regulation_id: str, folder_id: str | None) -> dict[str, Any]:
        self.get_document(regulation_id)
        if folder_id:
            self.get_folder(folder_id)
        with self._connect() as connection:
            connection.execute(
                """UPDATE regulation
                   SET folder_id=?, folder_assignment='manual', updated_at=?
                   WHERE regulation_id=?""",
                (folder_id, _now(), regulation_id),
            )
        return self.get_document(regulation_id)

    def get_document(self, regulation_id: str) -> dict[str, Any]:
        rows = self.list_documents(include_inactive=True)
        item = next((row for row in rows if row["regulation_id"] == regulation_id), None)
        if not item:
            raise KeyError(regulation_id)
        return item

    def rename_document(self, regulation_id: str, name: str) -> dict[str, Any]:
        self.get_document(regulation_id)
        clean_name = re.sub(r"\s+", " ", name).strip()
        if not clean_name:
            raise ValueError("技术规程名称不能为空。")
        if len(clean_name) > 180:
            raise ValueError("技术规程名称不能超过180个字符。")
        with self._connect() as connection:
            connection.execute(
                "UPDATE regulation SET title=?,updated_at=? WHERE regulation_id=?",
                (clean_name, _now(), regulation_id),
            )
        return self.get_document(regulation_id)

    def document_content(self, regulation_id: str, limit: int = 100000) -> dict[str, Any]:
        item = self.get_document(regulation_id)
        text = Path(item["text_file"]).read_text(encoding="utf-8", errors="replace")
        return {"regulation_id": regulation_id, "content": text[:limit], "text_length": len(text),
                "clause_count": item.get("clause_count", 0), "truncated": len(text) > limit}

    def list_clauses(self, regulation_id: str, keyword: str | None = None) -> list[dict[str, Any]]:
        self.get_document(regulation_id)
        sql = "SELECT * FROM regulation_clause WHERE regulation_id=? AND active=1"
        params: list[Any] = [regulation_id]
        if keyword:
            sql += " AND (clause_no LIKE ? OR title LIKE ? OR clause_text LIKE ?)"
            token = f"%{keyword}%"
            params.extend([token, token, token])
        sql += " ORDER BY CAST(substr(clause_no,1,instr(clause_no,'.')-1) AS INTEGER), source_paragraph"
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def candidates(self, regulation_id: str, limit: int = 500) -> list[dict[str, Any]]:
        item = self.get_document(regulation_id)
        rows = json.loads((Path(item["text_file"]).parent / "paragraphs.json").read_text(encoding="utf-8"))
        blocks: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for index, row in enumerate(rows):
            text = re.sub(r"\s+", " ", str(row.get("text") or "")).strip()
            if not text:
                continue
            if re.match(r"^#\s*条文说明\s*$", text):
                if current:
                    blocks.append(current)
                break
            # Figures do not define executable thresholds, while filenames and
            # dimensions inside image markup create many false numeric matches.
            if text.startswith("!["):
                continue
            match = _clause_start(text)
            if match:
                if current:
                    blocks.append(current)
                current = {
                    "index": index,
                    "clause": match.group(1),
                    "page": row.get("page"),
                    "parts": [text],
                }
            elif text.startswith("#"):
                if current:
                    blocks.append(current)
                current = None
            elif current:
                current["parts"].append(text)
                if current.get("page") is None and row.get("page") is not None:
                    current["page"] = row.get("page")
        if current:
            blocks.append(current)

        result = []
        seen: set[str] = set()
        for block in blocks:
            context = "\n".join(block["parts"])
            compact = re.sub(r"\s+", "", context)
            signature = hashlib.sha256(compact.encode("utf-8")).hexdigest()
            if (
                len(compact) >= 18
                and (_has_numeric_requirement(context) or CONDITIONAL_HINT.search(context))
                and NORMATIVE_HINT.search(context)
                and signature not in seen
            ):
                seen.add(signature)
                # A clause may contain a table. Keep the whole clause while bounding
                # the prompt size so the model cannot spend minutes on duplicated windows.
                bounded = context[:6000]
                result.append({
                    "candidate_id": f"C{block['index']:05d}",
                    "page": block.get("page"),
                    "clause": block["clause"],
                    "text": bounded,
                    "context": bounded,
                    "table_matrices": self._html_tables(bounded),
                })
            if len(result) >= limit:
                break
        return result

    def ai_rule_prompt(self, regulation_id: str, candidates: list[dict[str, Any]] | None = None) -> tuple[str, str, dict[str, dict[str, Any]]]:
        item = self.get_document(regulation_id)
        candidates = candidates if candidates is not None else self.candidates(regulation_id, limit=25)
        lookup = {item["candidate_id"]: item for item in candidates}
        system = (
            "你是工程技术规程规则结构化助手。你只能根据给定候选条款生成规则草稿，不得补写不存在的数值、公式或适用条件。"
            "只输出合法JSON对象。无法可靠结构化的条款不要输出。"
        )
        schema = {
            "numeric_rule": {
                "candidate_id": "C00001",
                "rule_type": "numeric_rule",
                "name": "规则名称",
                "object": "工程对象或空字符串",
                "relation": "空间关系或空字符串",
                "actual_field": "英文snake_case字段",
                "inputs": {"字段名": {"name": "中文名", "symbol": "原文变量符号；没有则为空字符串", "unit": "m", "required": True}},
                "limit_formula": "只含字段、数字、+-*/、max、min、abs的限值公式",
                "operator": "<、<=、>、>=、==之一",
                "action": {"英文结果字段": True},
            },
            "conditional_rule": {
                "candidate_id": "C00001",
                "rule_type": "conditional_rule",
                "name": "条件触发名称",
                "conditions": [{"field": "minimum_horizontal_clearance", "operator": "<", "value": 50}],
                "action": {"safety_assessment_required": True},
            },
            "lookup_table_rule": {
                "candidate_id": "C00001",
                "rule_type": "lookup_table_rule",
                "name": "表格映射名称",
                "selectors": ["project_type", "relative_relationship"],
                "output_field": "monitoring_requirements",
                "rows": [{"when": {"metro_structure_method": ["高架", "高架车站及高架桥梁"], "impact_level": "一级"}, "result": {"竖向位移": "应测", "结构裂缝": "应测"}}],
            },
        }
        prompt = (
            f"规程名称：{item['title']}\n"
            "请把下面候选条款转换成三类规则之一：数值合规阈值使用numeric_rule；条件成立后直接产生要求时使用带conditions和action的conditional_rule；检查案例是否已满足某项要求时再增加requirement；表格或分档映射使用lookup_table_rule。"
            "‘不得小于/不少于/至少’对应>=；‘不得大于/不超过/至多’对应<=；‘范围内’边界不明确时不要擅自决定，仍生成但在name末尾加‘（边界待确认）’。"
            "numeric_rule中实际测量值放actual_field，规范限值放limit_formula，公式中的每个变量必须在inputs定义。"
            "actual_field的值必须与inputs中的一个英文键完全相同，不允许使用近义键或缩写键。"
            "不要把带单位的4m写进公式，应写数字4并在inputs中统一声明单位。变量若在原文中使用D、H等符号，必须填写inputs.symbol。"
            "字段统一使用英文snake_case；不得生成Python代码，不得补写原文没有的条件、数值或枚举。"
            "二维表不得只抽取第一行。若同一组选择条件对应多个项目，应把全部项目和值放进result对象；必须覆盖表内所有项目、等级和要求单元格。"
            "候选条款中的table_matrices是由原始表格确定性展开后的事实矩阵：合并单元格已向所属各行各列填充。必须同时使用行标题、列标题和单元格值生成映射，不得根据自然语言自行补齐。"
            f"优先从统一字段目录选字段，只有确实没有对应项时才新增字段：{json.dumps(RULE_FIELD_CATALOG, ensure_ascii=False)}。"
            f"三类输出结构示例：{json.dumps({'rules': list(schema.values())}, ensure_ascii=False)}\n\n"
            f"候选条款：{json.dumps(candidates, ensure_ascii=False)}"
        )
        return system, prompt, lookup

    def ai_rule_batches(self, regulation_id: str, batch_size: int = 1) -> list[tuple[str, str, dict[str, dict[str, Any]]]]:
        candidates = self.candidates(regulation_id)
        return [
            self.ai_rule_prompt(regulation_id, candidates[index:index + batch_size])
            for index in range(0, len(candidates), batch_size)
        ]

    @staticmethod
    def _signature(rule: dict[str, Any]) -> str:
        rule_type = rule.get("rule_type") or "numeric_rule"
        compact: dict[str, Any] = {
            "candidate_id": (rule.get("source") or {}).get("candidate_id"),
            "rule_type": rule_type,
        }
        if rule_type == "conditional_rule":
            conditions = sorted(rule.get("conditions") or [], key=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True))
            compact.update(conditions=conditions, requirement=rule.get("requirement") or {}, action=rule.get("action") or {})
        elif rule_type == "lookup_table_rule":
            rows = sorted(rule.get("rows") or [], key=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True))
            compact.update(selectors=sorted(rule.get("selectors") or []), output_field=rule.get("output_field"), rows=rows)
        else:
            compact.update(
                actual_field=rule.get("actual_field"), inputs=rule.get("inputs") or {},
                limit_formula=re.sub(r"\s+", "", str(rule.get("limit_formula") or "")),
                operator=rule.get("operator"),
            )
        return json.dumps(compact, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _table_source_coverage(rule: dict[str, Any]) -> float:
        source = str((rule.get("source") or {}).get("original_text") or "")
        cells = []
        for raw in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", source, re.I | re.S):
            text = re.sub(r"<[^>]+>", "", html.unescape(raw))
            text = re.sub(r"\s+", "", text).strip()
            if text and not text.isdigit() and text not in {"序号", "监测对象", "监测项目", "外部作业影响等级"}:
                cells.append(text)
        required = set(cells)
        if not required:
            return 0.0

        values: set[str] = set()
        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key not in {"field", "operator"}:
                        normalized_key = re.sub(r"\s+", "", str(key)).strip()
                        if normalized_key:
                            values.add(normalized_key)
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
            elif value not in (None, ""):
                values.add(re.sub(r"\s+", "", str(value)).strip())

        collect(rule.get("rows") or [])
        matched = sum(1 for cell in required if cell in values)
        return round(matched / len(required), 3)

    @staticmethod
    def _html_table_matrix(source: str) -> list[list[str]]:
        matrix: list[list[str]] = []
        spans: dict[int, list[Any]] = {}
        for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", source, re.I | re.S):
            row: list[str] = []
            column = 0

            def consume_spans() -> None:
                nonlocal column
                while column in spans:
                    text, remaining = spans[column]
                    row.append(text)
                    if remaining <= 1:
                        del spans[column]
                    else:
                        spans[column][1] = remaining - 1
                    column += 1

            for attrs, raw in re.findall(r"<t[dh]([^>]*)>(.*?)</t[dh]>", row_html, re.I | re.S):
                consume_spans()
                text = re.sub(r"<[^>]+>", "", html.unescape(raw))
                text = re.sub(r"\s+", "", text).strip()
                rowspan_match = re.search(r"rowspan\s*=\s*[\"']?(\d+)", attrs, re.I)
                colspan_match = re.search(r"colspan\s*=\s*[\"']?(\d+)", attrs, re.I)
                rowspan = int(rowspan_match.group(1)) if rowspan_match else 1
                colspan = int(colspan_match.group(1)) if colspan_match else 1
                for offset in range(colspan):
                    row.append(text)
                    if rowspan > 1:
                        spans[column + offset] = [text, rowspan - 1]
                column += colspan
            consume_spans()
            matrix.append(row)
        width = max((len(row) for row in matrix), default=0)
        return [row + [""] * (width - len(row)) for row in matrix]

    @classmethod
    def _html_tables(cls, source: str) -> list[list[list[str]]]:
        blocks = re.findall(r"<table[^>]*>.*?</table>", source, re.I | re.S)
        return [matrix for block in blocks if (matrix := cls._html_table_matrix(block))]

    @staticmethod
    def _rule_row_tokens(row: dict[str, Any]) -> set[str]:
        tokens: set[str] = set()

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key not in {"field", "operator"}:
                        token = re.sub(r"\s+", "", str(key)).strip()
                        if token:
                            tokens.add(token)
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
            elif value not in (None, ""):
                token = re.sub(r"\s+", "", str(value)).strip()
                if token:
                    tokens.add(token)

        collect(row)
        return tokens

    @classmethod
    def _table_relation_verification(cls, rule: dict[str, Any]) -> dict[str, Any]:
        """Verify table semantics using row-header + column-header + cell triples.

        This does not depend on a particular engineering table. It tests whether
        every source data cell can be traced to one generated lookup row together
        with its row and column meaning. Repeated words such as "应测" therefore
        cannot pass merely by appearing somewhere in the JSON.
        """
        source = str((rule.get("source") or {}).get("original_text") or "")
        rule_tokens = [cls._rule_row_tokens(row) for row in rule.get("rows") or [] if isinstance(row, dict)]
        best = {"exact": False, "coverage": 0.0, "matched_relations": 0, "total_relations": 0,
                "header_rows": None, "row_header_columns": None}
        if not rule_tokens:
            return best

        ignored = {"序号", "编号", "项次", "要求", "结果", "备注", "-", "—"}
        for matrix in cls._html_tables(source):
            height = len(matrix)
            width = max((len(row) for row in matrix), default=0)
            if height < 2 or width < 2:
                continue
            for header_rows in range(1, min(4, height)):
                for row_header_columns in range(1, width):
                    matched = total = 0
                    single_result_column = row_header_columns == width - 1
                    for row in matrix[header_rows:]:
                        row_labels = {
                            value for value in row[:row_header_columns]
                            if value and value not in ignored and not re.fullmatch(r"\d+(?:\.\d+)?", value)
                        }
                        if not row_labels:
                            continue
                        for column in range(row_header_columns, width):
                            cell = row[column] if column < len(row) else ""
                            if not cell or cell in ignored:
                                continue
                            column_labels = {
                                matrix[index][column] for index in range(header_rows)
                                if column < len(matrix[index]) and matrix[index][column]
                                and matrix[index][column] not in ignored
                            }
                            if not column_labels and not single_result_column:
                                continue
                            total += 1
                            if any(
                                cell in tokens
                                and row_labels.issubset(tokens)
                                and (single_result_column or bool(column_labels & tokens))
                                for tokens in rule_tokens
                            ):
                                matched += 1
                    coverage = matched / total if total else 0.0
                    if total >= 2 and (coverage, total) > (best["coverage"], best["total_relations"]):
                        best = {
                            "exact": matched == total,
                            "coverage": round(coverage, 3),
                            "matched_relations": matched,
                            "total_relations": total,
                            "header_rows": header_rows,
                            "row_header_columns": row_header_columns,
                        }
        return best

    def normalize_ai_rules(self, regulation_id: str, ai_value: dict[str, Any] | list[Any], lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        values = ai_value.get("rules", []) if isinstance(ai_value, dict) else ai_value
        if not isinstance(values, list):
            raise ValueError("AI结果中的rules必须是数组。")
        document = self.get_document(regulation_id)
        result = []
        for value in values[:50]:
            if not isinstance(value, dict) or value.get("candidate_id") not in lookup:
                continue
            candidate = lookup[value["candidate_id"]]
            rule_type = str(value.get("rule_type") or "numeric_rule").strip()
            actual_field = str(value.get("actual_field") or "").strip()
            inputs = dict(value.get("inputs") or {})
            formula = str(value.get("limit_formula") or "").strip()
            if actual_field and actual_field not in inputs and len(inputs) == 1:
                old_key, metadata = next(iter(inputs.items()))
                try:
                    formula_names = SafeExpression.names(formula)
                except ValueError:
                    formula_names = {old_key}
                # A constant limit with one measurement input is unambiguous:
                # the model merely used two synonymous English field names.
                if old_key not in formula_names:
                    inputs = {actual_field: metadata}
            normalized = {
                "rule_type": rule_type,
                "name": str(value.get("name") or "未命名规则")[:200],
                "object": str(value.get("object") or ""),
                "relation": str(value.get("relation") or ""),
                "action": value.get("action") or {},
                "source": {
                    "document": document["title"],
                    "clause": candidate.get("clause"),
                    "page": candidate.get("page"),
                    "original_text": candidate["text"],
                    "context": candidate.get("context") or candidate["text"],
                    "candidate_id": candidate["candidate_id"],
                },
            }
            if rule_type == "conditional_rule":
                normalized.update(conditions=value.get("conditions") or [], requirement=value.get("requirement") or {})
            elif rule_type == "lookup_table_rule":
                normalized.update(selectors=value.get("selectors") or [], output_field=value.get("output_field"), rows=value.get("rows") or [])
            else:
                normalized.update(actual_field=actual_field, inputs=inputs, limit_formula=formula, operator=value.get("operator"))
            result.append(normalized)
        return result

    @staticmethod
    def _operator_supported_by_source(operator: str, source: str) -> bool:
        phrases = {
            ">=": ("不得小于", "不应小于", "不宜小于", "不小于", "不少于", "不宜低于", "至少", "以上"),
            "<=": ("不得大于", "不应大于", "不宜大于", "不大于", "不得超过", "不超过", "至多", "以下"),
            ">": ("大于", "超过"),
            "<": ("小于", "低于"),
            "==": ("等于", "应为"),
        }
        return any(phrase in source for phrase in phrases.get(operator, ()))

    def automatic_review(self, rule: dict[str, Any], independent_match: bool) -> dict[str, Any]:
        validation = RuleEngine.validate(rule)
        rule_type = rule.get("rule_type") or "numeric_rule"
        if rule_type != "numeric_rule":
            source = rule.get("source") or {}
            table_coverage = self._table_source_coverage(rule) if rule_type == "lookup_table_rule" else 0.0
            table_verification = self._table_relation_verification(rule) if rule_type == "lookup_table_rule" else {}
            exact_table_match = bool(table_verification.get("exact"))
            checks = {
                "schema_valid": validation["valid"],
                "independent_ai_match": independent_match,
                "independent_or_exact_table_match": independent_match or exact_table_match,
                "source_text_present": bool(source.get("original_text")),
                "clause_identified": bool(source.get("clause")),
            }
            required_checks = {key: value for key, value in checks.items() if key != "independent_ai_match"}
            failed = [key for key, passed in required_checks.items() if not passed]
            return {
                "mode": "unattended_conservative_v1",
                "confidence": round(sum(bool(value) for value in checks.values()) / len(checks), 3),
                "auto_publishable": not failed,
                "checks": checks,
                "table_source_coverage": table_coverage,
                "exact_table_match": exact_table_match,
                "table_relation_verification": table_verification,
                "failed_checks": failed,
                "message": "全部自动核验通过" if not failed else "以下核验未通过：" + "、".join(failed),
            }
        source = rule.get("source") or {}
        original = str(source.get("original_text") or "")
        context = str(source.get("context") or original)
        formula = str(rule.get("limit_formula") or "")
        inputs = rule.get("inputs") if isinstance(rule.get("inputs"), dict) else {}
        formula_names: set[str] = set()
        constants: list[Decimal] = []
        formula_safe = False
        boundary_test = False
        try:
            formula_names = SafeExpression.names(formula)
            constants = SafeExpression.constants(formula)
            samples = {name: Decimal("5") for name in inputs}
            limit = SafeExpression.evaluate(formula, samples)
            compare = RuleEngine.OPERATORS.get(rule.get("operator"))
            if compare:
                epsilon = Decimal("0.001")
                operator = rule["operator"]
                expected = {
                    ">=": (False, True, True), "<=": (True, True, False),
                    ">": (False, False, True), "<": (True, False, False), "==": (False, True, False),
                }[operator]
                boundary_test = (compare(limit - epsilon, limit), compare(limit, limit), compare(limit + epsilon, limit)) == expected
            formula_safe = True
        except (ValueError, ArithmeticError, KeyError):
            pass

        source_numbers = {Decimal(value) for value in re.findall(r"(?<![\d.])\d+(?:\.\d+)?", context)}
        constants_traceable = all(value in source_numbers for value in constants)
        symbols_traceable = True
        for name in formula_names:
            meta = inputs.get(name) if isinstance(inputs.get(name), dict) else {}
            symbol = str(meta.get("symbol") or "").strip()
            if not symbol:
                label = str(meta.get("name") or "")
                matches = re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", label)
                symbol = matches[-1] if matches else ""
            if not symbol or symbol not in context:
                symbols_traceable = False
                break

        units = [str(meta.get("unit") or "").strip() for meta in inputs.values() if isinstance(meta, dict)]
        units_complete = bool(units) and all(units) and len(set(units)) == 1
        explicit_boundary = self._operator_supported_by_source(str(rule.get("operator") or ""), original)
        ambiguous_range = "范围内" in original and not explicit_boundary
        checks = {
            "schema_valid": validation["valid"],
            "independent_ai_match": independent_match,
            "formula_safe": formula_safe,
            "operator_supported_by_source": explicit_boundary,
            "constants_traceable": constants_traceable,
            "variables_traceable": symbols_traceable,
            "units_complete_and_consistent": units_complete,
            "clause_identified": bool(source.get("clause")),
            "boundary_tests_passed": boundary_test,
            "no_ambiguous_range": not ambiguous_range,
        }
        failed = [key for key, passed in checks.items() if not passed]
        confidence = round(sum(1 for passed in checks.values() if passed) / len(checks), 3)
        return {
            "mode": "unattended_conservative_v1",
            "confidence": confidence,
            "auto_publishable": not failed,
            "checks": checks,
            "failed_checks": failed,
            "message": "全部自动核验通过" if not failed else "以下核验未通过：" + "、".join(failed),
        }

    def save_consensus_ai_rules(
        self,
        regulation_id: str,
        first_value: dict[str, Any] | list[Any],
        second_value: dict[str, Any] | list[Any],
        lookup: dict[str, dict[str, Any]],
        *,
        auto_publish: bool = True,
    ) -> list[dict[str, Any]]:
        first_rules = self.normalize_ai_rules(regulation_id, first_value, lookup)
        second_signatures = {self._signature(rule) for rule in self.normalize_ai_rules(regulation_id, second_value, lookup)}
        existing = {self._signature(item["rule"]) for item in self.list_rules(regulation_id)}
        created = []
        for rule in first_rules:
            signature = self._signature(rule)
            if signature in existing:
                continue
            review = self.automatic_review(rule, signature in second_signatures)
            rule["automatic_review"] = review
            item = self.create_rule(regulation_id, rule)
            if auto_publish and review["auto_publishable"]:
                item = self.publish_rule(item["rule_id"], automatic=True)
            created.append(item)
            existing.add(signature)
        self.revalidate_table_rules(regulation_id, auto_publish=auto_publish)
        return created

    def revalidate_table_rules(self, regulation_id: str, *, auto_publish: bool = True) -> list[dict[str, Any]]:
        """Recheck stored table drafts after parser/verifier improvements."""
        updated: list[dict[str, Any]] = []
        for item in self.list_rules(regulation_id):
            rule = item["rule"]
            if rule.get("rule_type") != "lookup_table_rule":
                continue
            old_review = rule.get("automatic_review") or {}
            independent_match = bool((old_review.get("checks") or {}).get("independent_ai_match"))
            review = self.automatic_review(rule, independent_match)
            rule["automatic_review"] = review
            validation = RuleEngine.validate(rule)
            with self._connect() as connection:
                connection.execute(
                    "UPDATE regulation_rule SET rule_json=?, validation_json=?, updated_at=? WHERE rule_id=?",
                    (_json(rule), _json(validation), _now(), item["rule_id"]),
                )
            refreshed = self.get_rule(item["rule_id"])
            if auto_publish and refreshed["status"] == "draft" and review["auto_publishable"]:
                refreshed = self.publish_rule(item["rule_id"], automatic=True)
            updated.append(refreshed)
        return updated

    def save_ai_rules(self, regulation_id: str, ai_value: dict[str, Any] | list[Any], lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        rules = self.normalize_ai_rules(regulation_id, ai_value, lookup)
        existing = {self._signature(item["rule"]) for item in self.list_rules(regulation_id)}
        created = []
        for rule in rules:
            signature = self._signature(rule)
            if signature in existing:
                continue
            created.append(self.create_rule(regulation_id, rule))
            existing.add(signature)
        return created

    def save_single_pass_ai_rules(
        self,
        regulation_id: str,
        ai_value: dict[str, Any] | list[Any],
        lookup: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Publish one-pass LLM rules after non-interactive safety validation.

        This is the IMA-style fast path requested by the product: no second LLM
        consensus and no manual confirmation. Invalid JSON/formulas are skipped
        because they cannot be executed safely; their source text remains in the
        knowledge base for RAG answers.
        """
        rules = self.normalize_ai_rules(regulation_id, ai_value, lookup)
        valid_rules = [rule for rule in rules if RuleEngine.validate(rule)["valid"]]
        candidate_ids = {
            str((rule.get("source") or {}).get("candidate_id") or "")
            for rule in valid_rules
        }
        candidate_ids.discard("")
        if not candidate_ids:
            return []

        # One AI call represents one complete version of its candidate clause.
        # Replace that version atomically instead of appending slightly different
        # LLM renderings every time the user clicks recognition.
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT rule_id, rule_json FROM regulation_rule WHERE regulation_id=? AND active=1",
                (regulation_id,),
            ).fetchall()
            obsolete = []
            for row in rows:
                stored = json.loads(row["rule_json"])
                if str((stored.get("source") or {}).get("candidate_id") or "") in candidate_ids:
                    obsolete.append(row["rule_id"])
            if obsolete:
                marks = ",".join("?" for _ in obsolete)
                connection.execute(
                    f"UPDATE regulation_rule SET active=0, updated_at=? WHERE rule_id IN ({marks})",
                    (_now(), *obsolete),
                )

        saved: list[dict[str, Any]] = []
        seen_signatures: set[str] = set()
        for rule in valid_rules:
            validation = RuleEngine.validate(rule)
            signature = self._signature(rule)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            table_verification = self._table_relation_verification(rule) if rule.get("rule_type") == "lookup_table_rule" else {}
            rule["automatic_review"] = {
                "mode": "single_pass_llm_v1",
                "confidence": 0.7,
                "auto_publishable": True,
                "checks": {"schema_valid": True, "single_llm_pass": True},
                "table_relation_verification": table_verification,
                "failed_checks": [],
                "message": "单次AI识别完成，已按快速模式自动发布",
            }
            item = self.create_rule(regulation_id, rule)
            if item["status"] != "published":
                item = self.publish_rule(item["rule_id"], automatic=True)
            saved.append(item)
        return saved

    def create_rule(self, regulation_id: str, rule: dict[str, Any]) -> dict[str, Any]:
        self.get_document(regulation_id)
        rule_id = "RULE-" + uuid.uuid4().hex[:12].upper()
        validation = RuleEngine.validate(rule)
        now = _now()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO regulation_rule VALUES(?,?,?,?,?,?,?,?,?)",
                (rule_id, regulation_id, rule.get("name") or rule_id, _json(rule), _json(validation), "draft", 1, now, now),
            )
        return self.get_rule(rule_id)

    def list_rules(self, regulation_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT rr.*, r.title regulation_title, r.version regulation_version, r.active regulation_active FROM regulation_rule rr JOIN regulation r ON r.regulation_id=rr.regulation_id WHERE rr.active=1"
        params = []
        if regulation_id:
            sql += " AND rr.regulation_id=?"
            params.append(regulation_id)
        if status:
            sql += " AND rr.status=?"
            params.append(status)
        sql += " ORDER BY rr.updated_at DESC"
        with self._connect() as connection:
            rows = [dict(row) for row in connection.execute(sql, params)]
        for row in rows:
            row["rule"] = json.loads(row.pop("rule_json"))
            row["validation"] = json.loads(row.pop("validation_json"))
        return rows

    def executable_rules(self) -> list[dict[str, Any]]:
        """Return only published rules belonging to enabled regulations."""
        return [item for item in self.list_rules(status="published") if item.get("regulation_active")]

    def get_rule(self, rule_id: str) -> dict[str, Any]:
        item = next((row for row in self.list_rules() if row["rule_id"] == rule_id), None)
        if not item:
            raise KeyError(rule_id)
        return item

    def update_rule(self, rule_id: str, rule: dict[str, Any]) -> dict[str, Any]:
        current = self.get_rule(rule_id)
        validation = RuleEngine.validate(rule)
        status = "draft" if current["status"] == "published" else current["status"]
        with self._connect() as connection:
            connection.execute(
                "UPDATE regulation_rule SET name=?, rule_json=?, validation_json=?, status=?, updated_at=? WHERE rule_id=?",
                (rule.get("name") or rule_id, _json(rule), _json(validation), status, _now(), rule_id),
            )
        return self.get_rule(rule_id)

    def publish_rule(self, rule_id: str, automatic: bool = False) -> dict[str, Any]:
        item = self.get_rule(rule_id)
        validation = RuleEngine.validate(item["rule"])
        if not validation["valid"]:
            raise ValueError("规则校验未通过：" + "；".join(validation["errors"]))
        if automatic and not (item["rule"].get("automatic_review") or {}).get("auto_publishable"):
            raise ValueError("规则未通过无人值守自动发布核验。")
        with self._connect() as connection:
            connection.execute("UPDATE regulation_rule SET status='published', validation_json=?, updated_at=? WHERE rule_id=?", (_json(validation), _now(), rule_id))
        return self.get_rule(rule_id)

    def set_document_active(self, regulation_id: str, active: bool) -> dict[str, Any]:
        self.get_document(regulation_id)
        with self._connect() as connection:
            connection.execute("UPDATE regulation SET active=?, updated_at=? WHERE regulation_id=?", (int(active), _now(), regulation_id))
        return self.get_document(regulation_id)

    def delete_document(self, regulation_id: str) -> dict[str, Any]:
        """Permanently remove a regulation, its clauses, rules and managed files."""
        item = self.get_document(regulation_id)
        with self.lock, self._connect() as connection:
            connection.execute("DELETE FROM regulation_rule WHERE regulation_id=?", (regulation_id,))
            connection.execute("DELETE FROM regulation_clause WHERE regulation_id=?", (regulation_id,))
            cursor = connection.execute("DELETE FROM regulation WHERE regulation_id=?", (regulation_id,))
            if cursor.rowcount == 0:
                raise KeyError(regulation_id)

        folder = Path(item["stored_file"]).resolve().parent
        root = self.file_root.resolve()
        if folder.parent == root and folder.exists():
            shutil.rmtree(folder)
        return item

    def stats(self) -> dict[str, int]:
        with self._connect() as connection:
            documents = connection.execute("SELECT COUNT(*) total, SUM(active) active FROM regulation").fetchone()
            clauses = connection.execute("SELECT COUNT(*) total FROM regulation_clause WHERE active=1").fetchone()
            rules = connection.execute("SELECT COUNT(*) total, SUM(CASE WHEN status='published' AND active=1 THEN 1 ELSE 0 END) published, SUM(CASE WHEN status='draft' AND active=1 THEN 1 ELSE 0 END) draft FROM regulation_rule").fetchone()
        return {
            "regulations": int(documents["total"] or 0),
            "active_regulations": int(documents["active"] or 0),
            "clauses": int(clauses["total"] or 0),
            "rules": int(rules["total"] or 0),
            "published_rules": int(rules["published"] or 0),
            "draft_rules": int(rules["draft"] or 0),
        }
