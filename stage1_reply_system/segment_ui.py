"""Tkinter dialogs for maintaining and selecting metro segment references."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

from stage1_reply_system.segment_database import (
    build_autofill_suggestion,
    delete_segment,
    export_segments_csv,
    find_nearby_segments,
    import_segments_csv,
    list_segments,
    save_segment,
)


METHOD_CATEGORIES = {
    "明挖": "地下现浇",
    "暗挖（矿山法）": "地下现浇",
    "盾构": "地下装配式",
    "高架": "高架结构",
}


class SegmentManager(tk.Toplevel):
    def __init__(self, parent: tk.Misc, database_file: str | Path, on_change: Callable[[], None] | None = None):
        super().__init__(parent)
        self.database_file = Path(database_file)
        self.on_change = on_change
        self.selected_id: int | None = None
        self.vars: dict[str, tk.StringVar] = {}
        self.title("轨道区段基础数据库")
        self.geometry("1100x700")
        self.minsize(920, 620)
        self.transient(parent)
        self._build()
        self._refresh()

    def _v(self, name: str, default: str = "") -> tk.StringVar:
        value = tk.StringVar(value=default)
        self.vars[name] = value
        return value

    def _build(self) -> None:
        shell = ttk.Frame(self, padding=14)
        shell.pack(fill="both", expand=True)
        ttk.Label(
            shell,
            text="仅录入已经核实的轨道区段参考点；删除操作会停用记录，不破坏既往审核的来源追溯。",
        ).pack(anchor="w", pady=(0, 10))

        columns = ("id", "line", "section", "method", "condition", "depth", "longitude", "latitude")
        self.tree = ttk.Treeview(shell, columns=columns, show="headings", height=12)
        headings = ("编号", "线路", "区段", "形式", "状态", "埋深(m)", "经度", "纬度")
        widths = (55, 85, 210, 90, 75, 80, 105, 105)
        for name, heading, width in zip(columns, headings, widths):
            self.tree.heading(name, text=heading)
            self.tree.column(name, width=width, anchor="center" if name != "section" else "w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._load_selected)

        form = ttk.LabelFrame(shell, text="区段资料", padding=12)
        form.pack(fill="x", pady=(12, 0))
        for column in (1, 3, 5):
            form.columnconfigure(column, weight=1)
        fields = (
            ("线路", "line_name"), ("区段名称", "section_name"), ("结构形式", "structure_method"),
            ("结构类别", "structure_category"), ("结构状态", "structure_condition"), ("埋深(m)", "buried_depth_m"),
            ("经度", "longitude"), ("纬度", "latitude"), ("来源项目", "source_project"),
            ("来源文件", "source_file"), ("备注", "notes"),
        )
        for index, (label, name) in enumerate(fields):
            row, pair = divmod(index, 3)
            label_column = pair * 2
            ttk.Label(form, text=label).grid(row=row, column=label_column, sticky="w", padx=(0, 6), pady=4)
            if name == "structure_method":
                widget = ttk.Combobox(form, textvariable=self._v(name, "盾构"), values=tuple(METHOD_CATEGORIES), state="readonly")
                widget.bind("<<ComboboxSelected>>", self._method_changed)
            elif name == "structure_category":
                widget = ttk.Combobox(form, textvariable=self._v(name, "地下装配式"), values=("地下装配式", "地下现浇", "地面结构", "高架结构"), state="readonly")
            elif name == "structure_condition":
                widget = ttk.Combobox(form, textvariable=self._v(name, "较好"), values=("较好", "较差"), state="readonly")
            else:
                widget = ttk.Entry(form, textvariable=self._v(name))
            widget.grid(row=row, column=label_column + 1, sticky="ew", padx=(0, 12), pady=4)

        commands = ttk.Frame(shell)
        commands.pack(fill="x", pady=(10, 0))
        ttk.Button(commands, text="新建/清空", command=self._clear).pack(side="left")
        ttk.Button(commands, text="保存", command=self._save).pack(side="left", padx=6)
        ttk.Button(commands, text="停用选中记录", command=self._delete).pack(side="left")
        ttk.Button(commands, text="导入 CSV", command=self._import_csv).pack(side="right")
        ttk.Button(commands, text="导出 CSV", command=self._export_csv).pack(side="right", padx=6)

    def _method_changed(self, event: object = None) -> None:
        self.vars["structure_category"].set(METHOD_CATEGORIES[self.vars["structure_method"].get()])

    def _refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for item in list_segments(self.database_file):
            self.tree.insert("", "end", iid=str(item["id"]), values=(
                item["id"], item["line_name"], item["section_name"], item["structure_method"],
                item["structure_condition"], item["buried_depth_m"], item["longitude"], item["latitude"],
            ))
        if self.on_change:
            self.on_change()

    def _load_selected(self, event: object = None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_id = int(selected[0])
        item = next(record for record in list_segments(self.database_file) if record["id"] == self.selected_id)
        for name in self.vars:
            self.vars[name].set("" if item.get(name) is None else str(item[name]))

    def _clear(self) -> None:
        self.selected_id = None
        for variable in self.vars.values():
            variable.set("")
        self.vars["structure_method"].set("盾构")
        self.vars["structure_category"].set("地下装配式")
        self.vars["structure_condition"].set("较好")
        self.tree.selection_remove(self.tree.selection())

    def _save(self) -> None:
        try:
            segment_id = save_segment({name: var.get() for name, var in self.vars.items()}, self.database_file, segment_id=self.selected_id)
        except Exception as exc:
            messagebox.showerror("无法保存", str(exc), parent=self)
            return
        self.selected_id = segment_id
        self._refresh()
        self.tree.selection_set(str(segment_id))
        self.tree.see(str(segment_id))

    def _delete(self) -> None:
        if self.selected_id is None:
            messagebox.showinfo("请选择记录", "请先在上方表格中选择一个区段。", parent=self)
            return
        if not messagebox.askyesno("确认停用", "停用后，该区段不再参与新的地图匹配。", parent=self):
            return
        delete_segment(self.selected_id, self.database_file)
        self._clear()
        self._refresh()

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV 文件", "*.csv")], parent=self)
        if not path:
            return
        try:
            result = import_segments_csv(path, self.database_file)
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc), parent=self)
            return
        self._refresh()
        messagebox.showinfo(
            "导入完成",
            f"成功导入 {result['imported_count']} 条，失败 {len(result['errors'])} 条。",
            parent=self,
        )

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")], parent=self)
        if path:
            export_segments_csv(path, list_segments(self.database_file))
            messagebox.showinfo("导出完成", path, parent=self)


class MapPicker(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        database_file: str | Path,
        on_apply: Callable[[float, float, dict[str, Any] | None], None],
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        line_name: str | None = None,
    ):
        super().__init__(parent)
        try:
            import tkintermapview
        except ImportError as exc:
            self.destroy()
            raise RuntimeError("缺少 tkintermapview，请在 PyCharm 解释器中安装 requirements.txt。") from exc
        self.database_file = Path(database_file)
        self.on_apply = on_apply
        self.line_name = line_name
        self.selected_position = (latitude or 32.0603, longitude or 118.7969)
        self.has_user_position = latitude is not None and longitude is not None
        self.candidates: dict[str, dict[str, Any]] = {}
        self.position_marker = None
        self.title("地图拾取与轨道区段匹配")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.transient(parent)

        shell = ttk.Frame(self, padding=10)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=3)
        shell.columnconfigure(1, weight=2)
        shell.rowconfigure(0, weight=1)
        self.map = tkintermapview.TkinterMapView(shell, corner_radius=0)
        self.map.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.map.set_position(*self.selected_position)
        self.map.set_zoom(13 if self.has_user_position else 11)
        self.map.add_left_click_map_command(self._map_clicked)
        for segment in list_segments(self.database_file):
            self.map.set_marker(
                segment["latitude"], segment["longitude"],
                text=f"{segment['line_name']} {segment['section_name']}",
            )
        if self.has_user_position:
            self.position_marker = self.map.set_marker(*self.selected_position, text="项目位置")

        panel = ttk.Frame(shell)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(3, weight=1)
        panel.columnconfigure(0, weight=1)
        ttk.Label(panel, text="在左侧地图单击项目位置", font=("Microsoft YaHei UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.position_var = tk.StringVar(value=self._position_text())
        ttk.Label(panel, textvariable=self.position_var).grid(row=1, column=0, sticky="w", pady=(6, 10))
        ttk.Label(panel, text="2 公里内候选区段（线路一致优先）").grid(row=2, column=0, sticky="w")
        self.tree = ttk.Treeview(panel, columns=("section", "distance", "score"), show="headings", height=14)
        self.tree.heading("section", text="线路 / 区段")
        self.tree.heading("distance", text="距离(m)")
        self.tree.heading("score", text="匹配分")
        self.tree.column("section", width=250)
        self.tree.column("distance", width=75, anchor="center")
        self.tree.column("score", width=70, anchor="center")
        self.tree.grid(row=3, column=0, sticky="nsew")
        self.detail_var = tk.StringVar(value="尚未选择候选区段。")
        ttk.Label(panel, textvariable=self.detail_var, wraplength=390, justify="left").grid(row=4, column=0, sticky="ew", pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._candidate_selected)
        ttk.Button(panel, text="仅采用坐标", command=self._apply_position).grid(row=5, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(panel, text="采用坐标和选中区段", command=self._apply_segment).grid(row=6, column=0, sticky="ew", pady=(6, 0))
        if self.has_user_position:
            self._search()

    def _position_text(self) -> str:
        lat, lon = self.selected_position
        return f"纬度 {lat:.7f}，经度 {lon:.7f}"

    def _map_clicked(self, coordinates: tuple[float, float]) -> None:
        self.selected_position = coordinates
        self.has_user_position = True
        if self.position_marker is not None:
            self.position_marker.delete()
        self.position_marker = self.map.set_marker(*coordinates, text="项目位置")
        self.position_var.set(self._position_text())
        self._search()

    def _search(self) -> None:
        lat, lon = self.selected_position
        matches = find_nearby_segments(
            lat, lon, self.database_file, line_name=self.line_name, max_distance_m=2_000, limit=8
        )
        self.tree.delete(*self.tree.get_children())
        self.candidates.clear()
        for item in matches:
            iid = str(item["id"])
            self.candidates[iid] = item
            self.tree.insert("", "end", iid=iid, values=(
                f"{item['line_name']} / {item['section_name']}", item["distance_m"], item["match_score"]
            ))
        if matches:
            self.tree.selection_set(str(matches[0]["id"]))
            self._candidate_selected()
        else:
            self.detail_var.set("2 公里内没有已录入的区段。可仅采用坐标，再到区段数据库补录资料。")

    def _candidate_selected(self, event: object = None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item = self.candidates[selected[0]]
        self.detail_var.set(
            f"结构形式：{item['structure_method']}\n结构状态：{item['structure_condition']}\n"
            f"结构埋深：{item['buried_depth_m'] if item['buried_depth_m'] is not None else '未录入'} m\n"
            f"来源项目：{item['source_project'] or '未填写'}"
        )

    def _apply_position(self) -> None:
        if not self.has_user_position:
            messagebox.showinfo("尚未拾取", "请先在地图上单击项目位置。", parent=self)
            return
        lat, lon = self.selected_position
        self.on_apply(lat, lon, None)
        self.destroy()

    def _apply_segment(self) -> None:
        selected = self.tree.selection()
        if not self.has_user_position or not selected:
            messagebox.showinfo("尚未选择", "请拾取项目位置并选择一个候选区段。", parent=self)
            return
        item = self.candidates[selected[0]]
        text = (
            f"采用区段：{item['line_name']} / {item['section_name']}\n"
            f"距拾取位置：{item['distance_m']} m\n"
            f"结构形式：{item['structure_method']}\n结构状态：{item['structure_condition']}\n"
            f"结构埋深：{item['buried_depth_m'] if item['buried_depth_m'] is not None else '未录入'} m\n\n"
            "确认后将回填到地铁结构页面。"
        )
        if not messagebox.askyesno("确认回填区段资料", text, parent=self):
            return
        lat, lon = self.selected_position
        suggestion = build_autofill_suggestion(item)
        suggestion["autofill_source"]["confirmed_by_user"] = True
        self.on_apply(lat, lon, suggestion)
        self.destroy()


def open_segment_manager(parent: tk.Misc, database_file: str | Path) -> SegmentManager:
    return SegmentManager(parent, database_file)


def open_map_picker(
    parent: tk.Misc,
    database_file: str | Path,
    on_apply: Callable[[float, float, dict[str, Any] | None], None],
    **kwargs: Any,
) -> MapPicker:
    return MapPicker(parent, database_file, on_apply, **kwargs)
