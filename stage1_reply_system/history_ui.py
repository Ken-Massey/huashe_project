"""Desktop manager for the historical incoming-letter/reply database."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from stage1_reply_system.history import (
    build_history_database,
    history_database_stats,
    load_history_cases,
    set_history_case_active,
)


class HistoryDatabaseManager(tk.Toplevel):
    def __init__(self, parent: tk.Misc, database_file: str | Path, report_root: str | Path):
        super().__init__(parent)
        self.database_file = Path(database_file)
        self.report_root = Path(report_root)
        self.cases: dict[str, dict[str, object]] = {}
        self.title("历史来函与回函数据库")
        self.geometry("1240x760")
        self.minsize(1040, 660)
        self.transient(parent)
        self._build()
        self._refresh()

    def _build(self) -> None:
        shell = ttk.Frame(self, padding=14)
        shell.pack(fill="both", expand=True)
        top = ttk.Frame(shell)
        top.pack(fill="x", pady=(0, 10))
        self.stats_var = tk.StringVar(value="正在读取数据库")
        ttk.Label(top, textvariable=self.stats_var, font=("Microsoft YaHei UI", 11, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        columns = ("id", "active", "quality", "project", "stage", "type", "pair", "updated")
        self.tree = ttk.Treeview(shell, columns=columns, show="headings", height=15)
        specs = (
            ("id", "编号", 55), ("active", "状态", 65), ("quality", "质量", 95),
            ("project", "项目名称", 320), ("stage", "阶段", 70), ("type", "类型", 70),
            ("pair", "配对分", 75), ("updated", "更新时间", 145),
        )
        for name, label, width in specs:
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, anchor="w" if name == "project" else "center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._show_selected)

        detail = ttk.LabelFrame(shell, text="选中案例详情", padding=10)
        detail.pack(fill="x", pady=(10, 0))
        self.detail_text = tk.Text(detail, height=8, wrap="word", font=("Microsoft YaHei UI", 9), relief="flat")
        self.detail_text.pack(fill="x")
        self.detail_text.configure(state="disabled")

        commands = ttk.Frame(shell)
        commands.pack(fill="x", pady=(10, 0))
        self.update_button = ttk.Button(commands, text="选择资料文件夹并增量更新", command=self._choose_and_update)
        self.update_button.pack(side="left")
        ttk.Button(commands, text="刷新列表", command=self._refresh).pack(side="left", padx=6)
        ttk.Button(commands, text="启用选中案例", command=lambda: self._set_active(True)).pack(side="left")
        ttk.Button(commands, text="停用选中案例", command=lambda: self._set_active(False)).pack(side="left", padx=6)
        ttk.Button(commands, text="打开回函原文", command=self._open_reply).pack(side="right")

    def _refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.cases.clear()
        for case in load_history_cases(self.database_file, include_inactive=True):
            iid = str(case["case_id"])
            self.cases[iid] = case
            self.tree.insert("", "end", iid=iid, values=(
                case["case_id"],
                "启用" if case["active"] else "停用",
                "可匹配" if case["quality_status"] == "ready" else "待复核",
                case["project_name"] or "未识别项目名称",
                case["stage"] or "未知",
                case["project_type"] or "未知",
                "" if case["pair_score"] is None else case["pair_score"],
                case["updated_at"],
            ))
        stats = history_database_stats(self.database_file)
        self.stats_var.set(
            f"总计 {stats['total']} 例  |  启用 {stats['active']}  |  停用 {stats['inactive']}  |  "
            f"可匹配 {stats['ready']}  |  待复核 {stats['review_required']}"
        )

    def _selected(self) -> dict[str, object] | None:
        selected = self.tree.selection()
        return self.cases.get(selected[0]) if selected else None

    def _show_selected(self, event: object = None) -> None:
        case = self._selected()
        if not case:
            return
        issues = "、".join(case["quality_issues"]) or "无"
        methods = "、".join(case["structure_methods"]) or "未识别"
        lines = "、".join(case["metro_lines"]) or "未识别"
        preview = str(case["advice_text"] or "未提取到审核意见")[:700]
        text = (
            f"质量问题：{issues}\n结构形式：{methods}；地铁线路：{lines}\n"
            f"来函：{case['incoming_file'] or '未配对'}\n回函：{case['primary_reply_file']}\n\n"
            f"审核意见原文预览：\n{preview}"
        )
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state="disabled")

    def _choose_and_update(self) -> None:
        folder = filedialog.askdirectory(title="选择包含历史来函和回函的资料文件夹", parent=self)
        if not folder:
            return
        self.update_button.configure(state="disabled")
        self.status_var.set("正在扫描资料")
        thread = threading.Thread(target=self._update_worker, args=(folder,), daemon=True)
        thread.start()

    def _update_worker(self, folder: str) -> None:
        try:
            result = build_history_database(
                [folder], self.database_file, rebuild=False, allow_pdf_ocr=True,
                progress=lambda current, total, name: self.after(
                    0, self.status_var.set, f"正在处理 {current}/{total}：{name}"
                ),
            )
            report_dir = self.report_root / datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / "history_database_update_report.json"
            report_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            self.after(0, self._update_finished, result, report_file)
        except Exception as exc:
            self.after(0, self._update_failed, exc)

    def _update_finished(self, result: dict[str, object], report_file: Path) -> None:
        self.update_button.configure(state="normal")
        self.status_var.set("增量更新完成")
        self._refresh()
        messagebox.showinfo(
            "更新完成",
            f"本次处理 {result['processed_case_count']} 例；数据库现有 {result['stored_case_count']} 例；"
            f"警告 {len(result['warnings'])} 条。\n\n报告：{report_file}",
            parent=self,
        )

    def _update_failed(self, error: Exception) -> None:
        self.update_button.configure(state="normal")
        self.status_var.set("更新失败")
        messagebox.showerror("更新失败", f"{type(error).__name__}: {error}", parent=self)

    def _set_active(self, active: bool) -> None:
        case = self._selected()
        if not case:
            messagebox.showinfo("请选择案例", "请先选择一条历史案例。", parent=self)
            return
        action = "启用" if active else "停用"
        if not messagebox.askyesno(f"确认{action}", f"{action}案例：{case['project_name']}？", parent=self):
            return
        set_history_case_active(int(case["case_id"]), active, self.database_file)
        self._refresh()

    def _open_reply(self) -> None:
        case = self._selected()
        if not case:
            messagebox.showinfo("请选择案例", "请先选择一条历史案例。", parent=self)
            return
        path = Path(str(case["primary_reply_file"]))
        if not path.exists():
            messagebox.showerror("文件不存在", str(path), parent=self)
            return
        os.startfile(path)


def open_history_database_manager(
    parent: tk.Misc,
    database_file: str | Path,
    report_root: str | Path,
) -> HistoryDatabaseManager:
    return HistoryDatabaseManager(parent, database_file, report_root)
