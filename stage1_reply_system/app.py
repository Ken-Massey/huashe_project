"""Local desktop interface for the complete stage-one review pipeline."""

from __future__ import annotations

import json
import os
import re
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stage1_reply_system.input_builder import METHOD_CATEGORY_DEFAULTS, build_input
from stage1_reply_system.history_ui import open_history_database_manager
from stage1_reply_system.pipeline import run_stage1_pipeline
from stage1_reply_system.segment_ui import open_map_picker, open_segment_manager


DATABASE_FILE = ROOT / "data" / "history_replies.sqlite3"
OUTPUT_ROOT = ROOT / "outputs" / "one_click_runs"
SEGMENT_DATABASE_FILE = ROOT / "data" / "metro_segments.sqlite3"
HISTORY_UPDATE_REPORT_ROOT = ROOT / "outputs" / "history_database_updates"


BOOL_VALUES = ("未知", "是", "否")
BOOL_MAP = {"未知": None, "是": True, "否": False}
PROTECTION_ZONE_VALUES = ("特别保护区", "控制保护区（非特别保护区）", "保护区外", "待判断")


class ScrollableTab(ttk.Frame):
    """Notebook page with a vertical scrollbar and mouse-wheel support."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        background = ttk.Style().lookup("TFrame", "background") or "#f0f0f0"
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=background)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, padding=18)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)

    def _update_scroll_region(self, event: object = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def scroll_mousewheel(self, event: tk.Event) -> None:
        bounds = self.canvas.bbox("all")
        if not bounds or bounds[3] <= self.canvas.winfo_height():
            return
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")


class StageOneApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("轨道交通保护区第一阶段智能审核")
        self.root.geometry("1120x780")
        self.root.minsize(980, 680)
        self.last_output_dir: Path | None = None
        self.autofill_source: dict[str, object] | None = None
        self.autofill_snapshot: dict[str, object] | None = None
        self.vars: dict[str, tk.Variable] = {}
        self.other_vars: dict[str, tk.BooleanVar] = {}
        self.support_vars: dict[str, tk.BooleanVar] = {}
        self._configure_style()
        self._build_layout()
        self.root.bind_all("<MouseWheel>", self._scroll_active_tab, add="+")

    def _configure_style(self) -> None:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("TLabel", font=("Microsoft YaHei UI", 10))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(10, 7))
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=(14, 8))
        style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 10), padding=(18, 8))
        style.configure("Header.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Status.TLabel", font=("Microsoft YaHei UI", 10), foreground="#245b47")

    def _var(self, name: str, value: object = "") -> tk.Variable:
        variable = tk.StringVar(value=value)
        self.vars[name] = variable
        return variable

    def _scroll_active_tab(self, event: tk.Event) -> None:
        if event.widget.winfo_toplevel() is not self.root:
            return
        selected = self.notebook.select()
        pages = {
            str(self.project_page): self.project_page,
            str(self.metro_page): self.metro_page,
            str(self.pit_page): self.pit_page,
        }
        page = pages.get(selected)
        if page is not None:
            page.scroll_mousewheel(event)

    def _build_layout(self) -> None:
        shell = ttk.Frame(self.root, padding=18)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="轨道交通保护区第一阶段智能审核", style="Header.TLabel").pack(anchor="w")

        self.notebook = ttk.Notebook(shell)
        self.notebook.pack(fill="both", expand=True, pady=(14, 12))
        self.project_page = ScrollableTab(self.notebook)
        self.metro_page = ScrollableTab(self.notebook)
        self.pit_page = ScrollableTab(self.notebook)
        self.project_tab = self.project_page.content
        self.metro_tab = self.metro_page.content
        self.pit_tab = self.pit_page.content
        self.result_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.project_page, text="项目与函件")
        self.notebook.add(self.metro_page, text="地铁结构")
        self.notebook.add(self.pit_page, text="基坑与地质")
        self.notebook.add(self.result_tab, text="审核结果")

        self._build_project_tab()
        self._build_metro_tab()
        self._build_pit_tab()
        self._build_result_tab()

        command_bar = ttk.Frame(shell)
        command_bar.pack(fill="x")
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(command_bar, textvariable=self.status_var, style="Status.TLabel").pack(side="left")
        self.open_button = ttk.Button(command_bar, text="打开结果目录", command=self._open_result, state="disabled")
        self.open_button.pack(side="right", padx=(8, 0))
        self.reply_word_button = ttk.Button(command_bar, text="打开回函 Word", command=self._open_reply_word, state="disabled")
        self.reply_word_button.pack(side="right", padx=(8, 0))
        self.audit_word_button = ttk.Button(command_bar, text="打开审核记录", command=self._open_audit_word, state="disabled")
        self.audit_word_button.pack(side="right", padx=(8, 0))
        self.run_button = ttk.Button(command_bar, text="开始审核", style="Accent.TButton", command=self._start_review)
        self.run_button.pack(side="right")
        ttk.Button(command_bar, text="回函数据库", command=self._open_history_database).pack(side="right", padx=(0, 8))

    def _entry_row(self, parent: ttk.Frame, row: int, label: str, name: str, *, browse: str | None = None) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        entry = ttk.Entry(parent, textvariable=self.vars.get(name) or self._var(name))
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        if browse:
            ttk.Button(parent, text="选择文件", command=lambda: self._browse(name, browse)).grid(row=row, column=2, padx=(8, 0), pady=6)
        return entry

    def _combo_row(self, parent: ttk.Frame, row: int, label: str, name: str, values: tuple[str, ...], default: str) -> ttk.Combobox:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        combo = ttk.Combobox(parent, textvariable=self.vars.get(name) or self._var(name, default), values=values, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", pady=6)
        return combo

    def _build_project_tab(self) -> None:
        tab = self.project_tab
        tab.columnconfigure(0, weight=1)

        required = ttk.LabelFrame(tab, text="计算必填", padding=12)
        required.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        required.columnconfigure(1, weight=1)
        self._entry_row(required, 0, "函件 PDF", "incoming_letter", browse="pdf")
        self._combo_row(required, 1, "项目类型", "project_type", ("基坑",), "基坑")
        stage = self._combo_row(required, 2, "项目阶段", "project_stage", ("出让", "规划", "设计", "施工"), "规划")
        stage.bind("<<ComboboxSelected>>", lambda event: self._refresh_stage_fields())
        self._combo_row(required, 3, "相对关系", "relative_relationship", ("交叉", "单侧", "双侧"), "单侧")

        conditions = ttk.LabelFrame(tab, text="条件判断", padding=12)
        conditions.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        conditions.columnconfigure(1, weight=1)
        ttk.Label(conditions, text="涉及其他").grid(row=0, column=0, sticky="nw", padx=(0, 10), pady=8)
        checks = ttk.Frame(conditions)
        checks.grid(row=0, column=1, sticky="w", pady=8)
        for index, label in enumerate(("红线", "接口", "临时结构", "协议")):
            variable = tk.BooleanVar(value=False)
            self.other_vars[label] = variable
            ttk.Checkbutton(checks, text=label, variable=variable).grid(row=0, column=index, padx=(0, 14))

        auxiliary = ttk.LabelFrame(tab, text="辅助信息（可选）", padding=12)
        auxiliary.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        auxiliary.columnconfigure(1, weight=1)
        self._entry_row(auxiliary, 0, "项目位置", "project_address")
        self._entry_row(auxiliary, 1, "地图位置名称", "map_label")

        coordinates = ttk.Frame(auxiliary)
        coordinates.grid(row=2, column=1, sticky="ew", pady=6)
        coordinates.columnconfigure((0, 1), weight=1)
        ttk.Entry(coordinates, textvariable=self._var("longitude")).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Entry(coordinates, textvariable=self._var("latitude")).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(coordinates, text="地图拾取", command=self._open_map_picker).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(6, 0))
        ttk.Button(coordinates, text="区段数据库", command=self._open_segment_manager).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(6, 0))
        ttk.Label(auxiliary, text="经度 / 纬度").grid(row=2, column=0, sticky="w", padx=(0, 10))

        self.stage_frame = ttk.LabelFrame(tab, text="阶段参数", padding=12)
        self.stage_frame.grid(row=3, column=0, sticky="ew")
        self.stage_frame.columnconfigure(0, weight=1)
        self._refresh_stage_fields()

    def _build_metro_tab(self) -> None:
        tab = self.metro_tab
        tab.columnconfigure(0, weight=1)

        required = ttk.LabelFrame(tab, text="计算必填", padding=12)
        required.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        required.columnconfigure(1, weight=1)
        method = self._combo_row(required, 0, "结构形式", "structure_method", ("明挖", "暗挖（矿山法）", "盾构", "高架"), "盾构")
        method.bind("<<ComboboxSelected>>", self._method_changed)
        self._combo_row(required, 1, "结构类别", "structure_category", ("地下装配式", "地下现浇", "地面结构", "高架结构"), "地下装配式")
        self.method_parameter_frame = ttk.Frame(required)
        self.method_parameter_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        conditions = ttk.LabelFrame(tab, text="条件判断", padding=12)
        conditions.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        conditions.columnconfigure(1, weight=1)
        self._combo_row(conditions, 0, "结构状态", "structure_condition", ("较好", "较差"), "较好")
        self._combo_row(conditions, 1, "特殊区段", "is_special_section", BOOL_VALUES, "未知")
        self._combo_row(conditions, 2, "越江河湖区段", "is_cross_river_segment", BOOL_VALUES, "未知")
        self._combo_row(conditions, 3, "病害情况", "disease_severity", ("无明显病害", "一般", "严重", "未知"), "未知")

        auxiliary = ttk.LabelFrame(tab, text="辅助信息", padding=12)
        auxiliary.grid(row=2, column=0, sticky="ew")
        auxiliary.columnconfigure(1, weight=1)
        self._entry_row(auxiliary, 0, "地铁线路", "metro_line_name")
        self._entry_row(auxiliary, 1, "地铁区间", "metro_section_name")
        self._entry_row(auxiliary, 2, "结构埋深（m）", "buried_depth_m")
        self._refresh_method_parameter()

    def _build_pit_tab(self) -> None:
        tab = self.pit_tab
        tab.columnconfigure(0, weight=1)

        required = ttk.LabelFrame(tab, text="计算必填", padding=12)
        required.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        required.columnconfigure(1, weight=1)
        ttk.Label(required, text="支护构件").grid(row=0, column=0, sticky="nw", padx=(0, 10), pady=8)
        support = ttk.Frame(required)
        support.grid(row=0, column=1, sticky="w", pady=8)
        components = ("围护桩", "地下连续墙", "非挤土工程桩", "挤土工程桩", "锚杆", "锚索", "土钉", "上方基坑", "其他")
        for index, label in enumerate(components):
            variable = tk.BooleanVar(value=False)
            self.support_vars[label] = variable
            ttk.Checkbutton(support, text=label, variable=variable).grid(row=index // 4, column=index % 4, sticky="w", padx=(0, 16), pady=3)
        self._combo_row(required, 1, "保护区位置", "protection_zone_location", PROTECTION_ZONE_VALUES, "待判断")

        conditions = ttk.LabelFrame(tab, text="条件判断", padding=12)
        conditions.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        conditions.columnconfigure(1, weight=1)
        self._combo_row(conditions, 0, "软弱土", "is_soft_soil", BOOL_VALUES, "未知")
        self._combo_row(conditions, 1, "复杂地质水文", "is_complex_geology_or_hydrology", BOOL_VALUES, "未知")
        self._combo_row(conditions, 2, "地质灾害", "has_geological_hazard", BOOL_VALUES, "未知")
        self._combo_row(conditions, 3, "承压水降深", "confined_water_drawdown", BOOL_VALUES, "未知")

        auxiliary = ttk.LabelFrame(tab, text="辅助信息", padding=12)
        auxiliary.grid(row=2, column=0, sticky="ew")
        auxiliary.columnconfigure(1, weight=1)
        self._entry_row(auxiliary, 0, "围护结构形式", "retaining_structure_type")
        self._combo_row(auxiliary, 1, "地段区域", "terrain_zone", ("漫滩", "非漫滩"), "非漫滩")
        self._entry_row(auxiliary, 2, "地质说明", "geology_description")
        self._entry_row(auxiliary, 3, "人工备注", "manual_notes")

    def _build_result_tab(self) -> None:
        self.result_text = tk.Text(
            self.result_tab,
            wrap="word",
            font=("Microsoft YaHei UI", 10),
            padx=12,
            pady=12,
            relief="flat",
            background="#f7f8fa",
        )
        scrollbar = ttk.Scrollbar(self.result_tab, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.result_text.insert("1.0", "尚未运行审核。")
        self.result_text.configure(state="disabled")

    def _refresh_stage_fields(self) -> None:
        for child in self.stage_frame.winfo_children():
            child.destroy()
        stage = self.vars["project_stage"].get()
        applicable = {
            "出让": {"land_use_type", "minimum_horizontal_clearance_m"},
            "规划": {"pit_depth_m", "pit_length_m", "pit_width_m", "pit_area_m2", "minimum_horizontal_clearance_m", "minimum_vertical_clearance_m"},
            "设计": {"pit_depth_m", "pit_length_m", "pit_area_m2", "minimum_horizontal_clearance_m", "minimum_vertical_clearance_m", "dewatering_method", "expert_opinion_file", "scheme_file"},
            "施工": {"pit_depth_m", "pit_length_m", "pit_area_m2", "minimum_horizontal_clearance_m", "minimum_vertical_clearance_m", "dewatering_method", "expert_opinion_file", "scheme_file"},
        }[stage]
        stage_names = {
            "land_use_type", "pit_depth_m", "pit_length_m", "pit_width_m", "pit_area_m2",
            "minimum_horizontal_clearance_m", "minimum_vertical_clearance_m",
            "dewatering_method", "expert_opinion_file", "scheme_file",
        }
        for name in stage_names - applicable:
            if name in self.vars:
                self.vars[name].set("")
        grouped_rows: list[tuple[str, list[tuple[str, str, str | None]]]]
        if stage == "出让":
            grouped_rows = [
                ("计算必填", [("水平距离（m）", "minimum_horizontal_clearance_m", None)]),
                ("辅助信息", [("用地性质", "land_use_type", None)]),
            ]
        elif stage == "规划":
            grouped_rows = [
                ("计算必填", [
                    ("基坑深度（m）", "pit_depth_m", None),
                    ("水平距离（m）", "minimum_horizontal_clearance_m", None),
                    ("竖向距离（m）", "minimum_vertical_clearance_m", None),
                ]),
                ("条件判断", [
                    ("基坑长度（m）", "pit_length_m", None),
                    ("基坑面积（m²）", "pit_area_m2", None),
                ]),
                ("辅助信息", [("基坑宽度（m）", "pit_width_m", None)]),
            ]
        else:
            grouped_rows = [
                ("计算必填", [
                    ("基坑深度（m）", "pit_depth_m", None),
                    ("水平距离（m）", "minimum_horizontal_clearance_m", None),
                    ("竖向距离（m）", "minimum_vertical_clearance_m", None),
                ]),
                ("条件判断", [
                    ("基坑长度（m）", "pit_length_m", None),
                    ("基坑面积（m²）", "pit_area_m2", None),
                ]),
                ("辅助信息", [
                    ("降水方式", "dewatering_method", None),
                    ("专家意见文件", "expert_opinion_file", "document"),
                    ("方案文件", "scheme_file", "document"),
                ]),
            ]
        self.stage_frame.columnconfigure(0, weight=1)
        for group_row, (title, rows) in enumerate(grouped_rows):
            group = ttk.LabelFrame(self.stage_frame, text=title, padding=10)
            group.grid(row=group_row, column=0, sticky="ew", pady=(0, 8))
            group.columnconfigure(1, weight=1)
            for row, (label, name, browse) in enumerate(rows):
                self._entry_row(group, row, label, name, browse=browse)

    def _refresh_method_parameter(self) -> None:
        for child in self.method_parameter_frame.winfo_children():
            child.destroy()
        parameters = {
            "明挖": ("明挖原开挖深度H（m）", "original_excavation_depth_m"),
            "暗挖（矿山法）": ("矿山法毛洞跨度W（m）", "mined_tunnel_span_m"),
            "盾构": ("盾构外径/结构宽度D（m）", "outer_diameter_or_width_m"),
            "高架": ("高架单桩桩径P（m）", "elevated_pile_diameter_m"),
        }
        label, active_name = parameters[self.vars["structure_method"].get()]
        parameter_names = {name for _, name in parameters.values()}
        for name in parameter_names - {active_name}:
            if name in self.vars:
                self.vars[name].set("")
        self.method_parameter_frame.columnconfigure(1, weight=1)
        self._entry_row(self.method_parameter_frame, 0, label, active_name)

    def _method_changed(self, event: object = None) -> None:
        method = self.vars["structure_method"].get()
        self.vars["structure_category"].set(METHOD_CATEGORY_DEFAULTS[method])
        self._refresh_method_parameter()

    def _browse(self, name: str, kind: str) -> None:
        filetypes = [("PDF 文件", "*.pdf")] if kind == "pdf" else [("方案文件", "*.pdf *.doc *.docx"), ("所有文件", "*.*")]
        selected = filedialog.askopenfilename(filetypes=filetypes)
        if selected:
            self.vars[name].set(selected)

    def _open_segment_manager(self) -> None:
        open_segment_manager(self.root, SEGMENT_DATABASE_FILE)

    def _open_history_database(self) -> None:
        open_history_database_manager(self.root, DATABASE_FILE, HISTORY_UPDATE_REPORT_ROOT)

    def _open_map_picker(self) -> None:
        try:
            latitude = self._number(self.vars["latitude"].get(), "纬度", allow_negative=True)
            longitude = self._number(self.vars["longitude"].get(), "经度", allow_negative=True)
            open_map_picker(
                self.root,
                SEGMENT_DATABASE_FILE,
                self._apply_map_selection,
                latitude=latitude,
                longitude=longitude,
                line_name=self.vars["metro_line_name"].get(),
            )
        except Exception as exc:
            messagebox.showerror("地图无法打开", str(exc))

    def _apply_map_selection(self, latitude: float, longitude: float, suggestion: dict[str, object] | None) -> None:
        self.vars["latitude"].set(f"{latitude:.7f}")
        self.vars["longitude"].set(f"{longitude:.7f}")
        if suggestion is None:
            self.autofill_source = None
            self.autofill_snapshot = None
            return
        field_names = (
            "metro_line_name", "metro_section_name", "structure_method",
            "structure_category", "structure_condition", "buried_depth_m",
        )
        snapshot: dict[str, object] = {}
        for name in field_names:
            value = suggestion.get(name)
            text = "" if value is None else str(value)
            self.vars[name].set(text)
            snapshot[name] = text
        self._refresh_method_parameter()
        self.autofill_source = dict(suggestion["autofill_source"])
        self.autofill_snapshot = snapshot

    @staticmethod
    def _optional_text(value: str) -> str | None:
        value = value.strip()
        return value or None

    @staticmethod
    def _number(value: str, label: str, *, allow_negative: bool = False) -> float | None:
        value = value.strip()
        if not value:
            return None
        try:
            number = float(value)
        except ValueError as exc:
            raise ValueError(f"{label}必须填写数字。") from exc
        if number < 0 and not allow_negative:
            raise ValueError(f"{label}不能小于0。")
        return number

    def _collect_input(self) -> dict[str, object]:
        raw = {name: variable.get() for name, variable in self.vars.items()}
        pdf = raw.get("incoming_letter", "").strip()
        if not pdf:
            raise ValueError("请选择函件 PDF。")
        project_name = self._optional_text(raw.get("project_name", ""))
        case_id = raw.get("case_id", "").strip()
        if not case_id:
            base = re.sub(r"\W+", "-", project_name or Path(pdf).stem).strip("-")[:40]
            case_id = f"{base}-{datetime.now():%Y%m%d%H%M%S}"
            if "case_id" in self.vars:
                self.vars["case_id"].set(case_id)

        numeric_labels = {
            "longitude": "经度", "latitude": "纬度", "buried_depth_m": "结构埋深",
            "outer_diameter_or_width_m": "盾构外径/结构宽度D",
            "original_excavation_depth_m": "原开挖深度H", "mined_tunnel_span_m": "毛洞跨度W",
            "elevated_pile_diameter_m": "高架单桩桩径P", "pit_depth_m": "基坑深度",
            "pit_length_m": "基坑长度", "pit_width_m": "基坑宽度", "pit_area_m2": "基坑面积",
            "minimum_horizontal_clearance_m": "水平距离", "minimum_vertical_clearance_m": "竖向距离",
        }
        values: dict[str, object] = {
            name: self._optional_text(str(value)) for name, value in raw.items()
        }
        for name, label in numeric_labels.items():
            values[name] = self._number(raw.get(name, ""), label, allow_negative=name in ("longitude", "latitude"))
        values.update({
            "incoming_letter": pdf,
            "case_id": case_id,
            "project_name": project_name,
            "other_involvements": [name for name, variable in self.other_vars.items() if variable.get()],
            "support_components": [name for name, variable in self.support_vars.items() if variable.get()],
        })
        current_snapshot = {
            name: raw.get(name, "") for name in (
                "metro_line_name", "metro_section_name", "structure_method",
                "structure_category", "structure_condition", "buried_depth_m",
            )
        }
        if self.autofill_source and current_snapshot == self.autofill_snapshot:
            values["autofill_source"] = self.autofill_source
        for name in (
            "is_special_section", "is_cross_river_segment", "is_soft_soil",
            "is_complex_geology_or_hydrology", "has_geological_hazard",
            "confined_water_drawdown",
        ):
            values[name] = BOOL_MAP[raw.get(name, "未知")]
        values["dewatering_involved"] = bool(values.get("dewatering_method")) if raw.get("dewatering_method", "").strip() else None
        return build_input(values)

    def _start_review(self) -> None:
        try:
            manual_input = self._collect_input()
        except Exception as exc:
            messagebox.showerror("输入有误", str(exc))
            return
        self.run_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.reply_word_button.configure(state="disabled")
        self.audit_word_button.configure(state="disabled")
        self.status_var.set("正在启动审核")
        self._set_result("正在处理，请稍候……")
        thread = threading.Thread(target=self._run_worker, args=(manual_input,), daemon=True)
        thread.start()

    def _run_worker(self, manual_input: dict[str, object]) -> None:
        try:
            result = run_stage1_pipeline(
                manual_input["source_documents"][0]["path"],
                manual_input,
                DATABASE_FILE,
                OUTPUT_ROOT,
                run_name=manual_input["project"].get("project_name") or manual_input["case_id"],
                progress=lambda message: self.root.after(0, self.status_var.set, message),
            )
            self.root.after(0, self._finish_success, result)
        except Exception as exc:
            self.root.after(0, self._finish_error, exc)

    def _finish_success(self, result: dict[str, object]) -> None:
        self.last_output_dir = Path(result["output_dir"])
        summary = result["summary"]
        decisions = summary["decision_summary"]
        missing = summary["missing_required_inputs"]
        lines = [
            "审核完成",
            "",
            f"总体状态：{summary['overall_status']}",
            f"退让距离：{decisions['setback_distance']}",
            f"影响等级：{decisions['impact_level']}",
            f"安全评估：{decisions['safety_assessment']}",
            f"保护监测：{decisions['protective_monitoring']}",
            "",
            f"历史匹配：{summary['history_match_project'] or '未自动采用'}",
            f"匹配相似度：{summary['history_match_similarity']}",
            f"历史案例编号：{summary.get('history_match_case_id') or '未自动采用'}",
            f"历史案例质量：{summary.get('history_match_quality_status') or '未自动采用'}",
            f"质量提示：{'、'.join(summary.get('history_match_quality_issues') or []) or '无'}",
            f"匹配回函：{summary.get('history_match_reply_file') or '未自动采用'}",
            "",
            "匹配分项：",
        ]
        component_labels = {
            "project_name": "项目名称",
            "project_stage": "项目阶段",
            "project_type": "项目类型",
            "relative_relationship": "相对关系",
            "structure_method": "结构形式",
            "metro_line": "地铁线路",
            "pit_depth": "基坑深度",
            "horizontal_clearance": "水平净距",
            "vertical_clearance": "竖向净距",
            "letter_semantics": "函件语义",
        }
        components = summary.get("history_match_component_scores") or {}
        lines.extend(
            f"- {component_labels.get(name, name)}：{'无数据' if score is None else score}"
            for name, score in components.items()
        )
        if not components:
            lines.append("- 未达到自动匹配阈值")
        lines.extend([
            "",
            "待补充资料：",
        ])
        lines.extend(f"- {item['label']}" for item in missing)
        if not missing:
            lines.append("- 无")
        lines.extend(["", f"结果目录：{self.last_output_dir}"])
        self._set_result("\n".join(lines))
        self.status_var.set("审核完成")
        self.run_button.configure(state="normal")
        self.open_button.configure(state="normal")
        self.reply_word_button.configure(state="normal")
        self.audit_word_button.configure(state="normal")
        self.notebook.select(self.result_tab)

    def _finish_error(self, error: Exception) -> None:
        self.status_var.set("审核失败")
        self.run_button.configure(state="normal")
        self._set_result(f"审核失败\n\n{type(error).__name__}: {error}")
        messagebox.showerror("审核失败", str(error))

    def _set_result(self, text: str) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def _open_result(self) -> None:
        if self.last_output_dir and self.last_output_dir.exists():
            os.startfile(self.last_output_dir)

    def _open_reply_word(self) -> None:
        if self.last_output_dir:
            path = self.last_output_dir / "回函辅助草稿.docx"
            if path.exists():
                os.startfile(path)

    def _open_audit_word(self) -> None:
        if self.last_output_dir:
            path = self.last_output_dir / "内部自动审核记录.docx"
            if path.exists():
                os.startfile(path)


def main() -> None:
    root = tk.Tk()
    StageOneApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
