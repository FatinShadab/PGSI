"""
Simple modern GUI for PGSI Analyzer.

Provides a desktop interface to configure tool paths and benchmark options,
then runs the existing PGSI orchestration pipeline in the background.
"""

import os
import queue
import re
import csv
import subprocess
import sys
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Set

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..benchmarks.registry import list_algorithms as list_builtin_algorithms, list_methods
from ..benchmarks.discovery import build_registry, list_algorithms_from_registry
from ..benchmarks.template import generate_benchmark_template


class PGSIGuiApp:
    """Tkinter GUI wrapper for PGSI Analyzer orchestration."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PGSI Analyzer")
        self.root.geometry("1100x760")
        self.root.minsize(1000, 700)

        self._log_queue: "queue.Queue[str]" = queue.Queue()
        self._run_thread: Optional[threading.Thread] = None
        self._process: Optional[subprocess.Popen] = None
        self._is_running = False
        self._progress_current = 0
        self._progress_total = 0

        self.algorithms = list_builtin_algorithms()
        self.methods = list_methods()
        self.algorithm_vars: Dict[str, tk.BooleanVar] = {}
        self.method_vars: Dict[str, tk.BooleanVar] = {}
        self._algo_inner: Optional[ttk.Frame] = None
        self._algo_canvas: Optional[tk.Canvas] = None
        self._algo_columns = 3
        self.algorithm_runs_overrides: Dict[str, int] = {}
        self.load_project_dir_var = tk.StringVar(value=str((Path.cwd() / "benchmarks").resolve()))
        self.create_parent_dir_var = tk.StringVar(value=str(Path.cwd().resolve()))
        self.create_project_name_var = tk.StringVar(value="my-benchmarks")
        self.create_algorithm_vars: Dict[str, tk.BooleanVar] = {}
        self.current_project_dir: Optional[Path] = None

        self._apply_theme()
        self._build_ui()
        self._schedule_log_pump()

    def _apply_theme(self) -> None:
        """Apply a modern-ish ttk style without external dependencies."""
        style = ttk.Style(self.root)
        available = set(style.theme_names())
        preferred = "clam" if "clam" in available else style.theme_use()
        style.theme_use(preferred)

        # Modern dark theme palette.
        bg_root = "#0F1115"
        bg_card = "#151922"
        bg_section = "#1B2130"
        accent = "#4CAF50"
        accent_hover = "#5CC15F"
        text_main = "#E6EDF3"
        text_muted = "#B8C4D6"
        border = "#2A3345"

        modern_font = ("Segoe UI", 10)
        modern_font_bold = ("Segoe UI Semibold", 10)

        self.root.configure(bg=bg_root)

        style.configure(
            "Card.TFrame",
            background=bg_card,
            borderwidth=1,
            relief="flat",
        )
        style.configure(
            "Header.TLabel",
            font=("Segoe UI Semibold", 14),
            background=bg_root,
            foreground=text_main,
        )
        style.configure(
            "Section.TLabelframe",
            background=bg_section,
            bordercolor=border,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Section.TLabelframe.Label",
            font=modern_font_bold,
            background=bg_root,
            foreground=text_main,
        )
        style.configure("TFrame", background=bg_card)
        style.configure("TLabel", font=modern_font, background=bg_card, foreground=text_main)
        style.configure(
            "TEntry",
            fieldbackground="#111723",
            foreground=text_main,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            insertcolor=text_main,
            padding=6,
        )
        style.configure(
            "TButton",
            font=modern_font,
            background="#232C3E",
            foreground=text_muted,
            bordercolor=border,
            focusthickness=1,
            focuscolor=accent,
            padding=(10, 7),
        )
        style.map(
            "TButton",
            background=[("active", "#2A344A"), ("pressed", "#313E57")],
            foreground=[("disabled", "#667085")],
        )
        style.configure(
            "Run.TButton",
            font=modern_font_bold,
            background=accent,
            foreground="#0B0F14",
            bordercolor=accent,
            padding=(12, 8),
        )
        style.map(
            "Run.TButton",
            background=[("active", accent_hover), ("pressed", "#3F9F43"), ("disabled", "#5E8B63")],
            foreground=[("disabled", "#0F1115")],
        )
        style.configure(
            "Vertical.TScrollbar",
            background="#293247",
            troughcolor="#141A25",
            arrowcolor=text_muted,
            bordercolor=border,
        )
        style.configure(
            "Green.Horizontal.TProgressbar",
            troughcolor="#111723",
            background=accent,
            bordercolor=border,
            lightcolor=accent_hover,
            darkcolor="#3F9F43",
        )

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="Card.TFrame", padding=14)
        outer.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(
            outer,
            text="PGSI Analyzer GUI - Configure, Run, and Analyze",
            style="Header.TLabel",
        )
        header.pack(anchor=tk.W, pady=(0, 8))

        self.page_container = ttk.Frame(outer, style="Card.TFrame")
        self.page_container.pack(fill=tk.BOTH, expand=True)
        self.page_container.columnconfigure(0, weight=1)
        self.page_container.rowconfigure(0, weight=1)

        self.project_page = ttk.Frame(self.page_container, style="Card.TFrame")
        self.project_page.grid(row=0, column=0, sticky="nsew")
        self._build_project_page(self.project_page)

        self.run_page = ttk.Frame(self.page_container, style="Card.TFrame")
        self.run_page.grid(row=0, column=0, sticky="nsew")
        self._build_run_page(self.run_page)

        self.project_page.tkraise()

    def _build_project_page(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        frame = ttk.LabelFrame(parent, text="Step 1: Load or Create Project", style="Section.TLabelframe", padding=14)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(
            frame,
            text="Choose a benchmark project folder, or create one in-place.\n"
                 "Then continue to configuration and run.",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        create_frame = ttk.LabelFrame(frame, text="Create Project", style="Section.TLabelframe", padding=10)
        create_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        create_frame.columnconfigure(0, weight=0)
        create_frame.columnconfigure(1, weight=1)
        create_frame.columnconfigure(2, weight=0)
        create_frame.rowconfigure(3, weight=1)

        ttk.Label(create_frame, text="Parent folder").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(create_frame, textvariable=self.create_parent_dir_var).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(
            create_frame,
            text="Browse",
            command=lambda: self._set_var_from_dir(self.create_parent_dir_var),
        ).grid(row=0, column=2, padx=(6, 0), pady=3)

        ttk.Label(create_frame, text="Project name").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(create_frame, textvariable=self.create_project_name_var).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=3
        )

        ttk.Label(create_frame, text="Algorithms to include").grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 4))
        algo_canvas, algo_inner = self._make_scrollable_checks(create_frame, 3, 0)
        algo_canvas.grid_configure(columnspan=3, padx=(0, 0), pady=(0, 6))
        for name in list_builtin_algorithms():
            var = tk.BooleanVar(value=True)
            self.create_algorithm_vars[name] = var
            ttk.Checkbutton(algo_inner, text=name, variable=var).pack(anchor=tk.W, pady=1)

        create_btns = ttk.Frame(create_frame)
        create_btns.grid(row=4, column=0, columnspan=3, sticky="ew")
        ttk.Button(
            create_btns,
            text="All",
            command=lambda: self._toggle_group(self.create_algorithm_vars, True),
        ).pack(side=tk.LEFT)
        ttk.Button(
            create_btns,
            text="None",
            command=lambda: self._toggle_group(self.create_algorithm_vars, False),
        ).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(create_btns, text="Create Project", command=self._create_project_from_gui).pack(side=tk.RIGHT)

        load_frame = ttk.LabelFrame(frame, text="Load Existing Project", style="Section.TLabelframe", padding=10)
        load_frame.grid(row=2, column=0, sticky="nsew")
        load_frame.columnconfigure(0, weight=0)
        load_frame.columnconfigure(1, weight=1)
        load_frame.columnconfigure(2, weight=0)
        load_frame.columnconfigure(3, weight=0)
        ttk.Label(load_frame, text="Project folder").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(load_frame, textvariable=self.load_project_dir_var).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(
            load_frame,
            text="Browse",
            command=lambda: self._set_var_from_dir(self.load_project_dir_var),
        ).grid(row=0, column=2, padx=(6, 0), pady=3)
        ttk.Button(load_frame, text="Load Project", command=self._load_project_from_gui).grid(
            row=0, column=3, padx=(6, 0), pady=3, sticky="e"
        )

        bottom = ttk.Frame(parent, style="Card.TFrame")
        bottom.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(bottom, text="Continue ->", style="Run.TButton", command=self._continue_to_run_page).pack(side=tk.RIGHT)

    def _build_run_page(self, parent: ttk.Frame) -> None:
        content = ttk.Frame(parent, style="Card.TFrame")
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=3)
        content.rowconfigure(2, weight=2)

        self._build_paths_section(content)
        self._build_run_config_section(content)
        self._build_selection_section(content)
        self._build_log_section(content)

    def _build_paths_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Setup: Tool Paths", style="Section.TLabelframe", padding=10)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=(0, 0), pady=(0, 10))
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=0)

        self.env_file_var = tk.StringVar()
        self._add_path_row(frame, 0, "Env file (.env)", self.env_file_var, file_kind="file")

    def _build_run_config_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Run Configuration", style="Section.TLabelframe", padding=10)
        frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        # Scrollable run configuration container to keep all controls reachable
        # on smaller window heights.
        canvas = tk.Canvas(frame, highlightthickness=0, bg="#151922")
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        form = ttk.Frame(canvas, style="Card.TFrame")
        canvas_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def _sync_form_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

        form.bind("<Configure>", _sync_form_scroll)
        canvas.bind("<Configure>", _sync_form_scroll)
        form.columnconfigure(0, weight=1)
        form.rowconfigure(99, weight=1)

        self.output_dir_var = tk.StringVar(value=str((Path.cwd() / "results").resolve()))
        self.runs_var = tk.StringVar(value="50")
        self.carbon_intensity_var = tk.StringVar(value="0.000475")
        self.alpha_var = tk.StringVar(value="0.4")
        self.beta_var = tk.StringVar(value="0.4")
        self.gamma_var = tk.StringVar(value="0.2")

        self._add_labeled_entry(form, 0, "Output directory", self.output_dir_var)
        ttk.Button(form, text="Browse Output Folder", command=self._browse_output_dir).grid(
            row=2, column=0, sticky="ew", pady=(2, 8)
        )
        self._add_labeled_entry(form, 3, "Runs per benchmark", self.runs_var)
        ttk.Button(form, text="Per-Algorithm Runs...", command=self._open_algorithm_runs_dialog).grid(
            row=5, column=0, sticky="ew", pady=(0, 8)
        )
        self._add_labeled_entry(form, 6, "Carbon intensity", self.carbon_intensity_var)
        self._add_labeled_entry(form, 8, "GreenScore alpha", self.alpha_var)
        self._add_labeled_entry(form, 10, "GreenScore beta", self.beta_var)
        self._add_labeled_entry(form, 12, "GreenScore gamma", self.gamma_var)

    def _build_selection_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Benchmarks Selection", style="Section.TLabelframe", padding=10)
        frame.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)

        algorithm_top = ttk.Frame(frame)
        algorithm_top.grid(row=0, column=0, sticky="ew")
        ttk.Label(algorithm_top, text="Algorithms").pack(side=tk.LEFT)
        ttk.Button(algorithm_top, text="Discover Extended Algorithms", command=self._discover_extended_algorithms).pack(
            side=tk.RIGHT, padx=(6, 0)
        )
        ttk.Button(algorithm_top, text="All", command=lambda: self._toggle_group(self.algorithm_vars, True)).pack(side=tk.RIGHT)

        method_top = ttk.Frame(frame)
        method_top.grid(row=0, column=1, sticky="ew")
        ttk.Label(method_top, text="Methods").pack(side=tk.LEFT)
        ttk.Button(method_top, text="All", command=lambda: self._toggle_group(self.method_vars, True)).pack(side=tk.RIGHT)
        ttk.Button(method_top, text="None", command=lambda: self._toggle_group(self.method_vars, False)).pack(side=tk.RIGHT, padx=(0, 4))

        algo_canvas, algo_inner = self._make_scrollable_checks(frame, 1, 0)
        self._algo_canvas = algo_canvas
        self._algo_inner = algo_inner
        method_canvas, method_inner = self._make_scrollable_checks(frame, 1, 1)

        algo_canvas.bind("<Configure>", self._on_algo_area_resized, add="+")

        self._render_algorithm_checkboxes()

        for name in self.methods:
            var = tk.BooleanVar(value=True)
            self.method_vars[name] = var
            ttk.Checkbutton(method_inner, text=name, variable=var).pack(anchor=tk.W, pady=1)

        algo_canvas.yview_moveto(0.0)
        method_canvas.yview_moveto(0.0)

    def _build_log_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Run Log", style="Section.TLabelframe", padding=10)
        frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            frame,
            height=8,
            wrap=tk.WORD,
            font=("Cascadia Mono", 10),
            bg="#0F1623",
            fg="#DCE6F3",
            insertbackground="#DCE6F3",
            relief="flat",
            borderwidth=1,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(state=tk.DISABLED)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_label_var = tk.StringVar(value="Progress: idle")
        self.progress_bar = ttk.Progressbar(
            frame,
            orient=tk.HORIZONTAL,
            mode="determinate",
            maximum=100,
            variable=self.progress_var,
            style="Green.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(frame, textvariable=self.progress_label_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        footer = ttk.Frame(frame)
        footer.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        footer.columnconfigure(2, weight=1)

        self.status_var = tk.StringVar(value="Ready. (Step 2)")
        ttk.Button(footer, text="<- Back", command=lambda: self.project_page.tkraise()).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        self.open_results_button = ttk.Button(footer, text="Open Output Folder", command=self._open_output_folder)
        self.open_results_button.grid(row=0, column=3, sticky="e", padx=(10, 0))

        self.stop_button = ttk.Button(footer, text="Stop", command=self._on_stop, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=4, sticky="e", padx=(10, 0))

        self.run_button = ttk.Button(footer, text="Run PGSI Analysis", style="Run.TButton", command=self._on_run)
        self.run_button.grid(row=0, column=5, sticky="e", padx=(10, 0))

    def _make_scrollable_checks(self, parent: ttk.Frame, row: int, col: int):
        outer = ttk.Frame(parent)
        outer.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0), pady=(8, 0))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        canvas = tk.Canvas(outer, highlightthickness=0, bg="#151922")
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        inner = ttk.Frame(canvas, style="Card.TFrame")
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_configure)
        return canvas, inner

    def _add_labeled_entry(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=(3, 1))
        ttk.Entry(parent, textvariable=var).grid(row=row + 1, column=0, sticky="ew", pady=(0, 6))

    def _render_algorithm_checkboxes(self) -> None:
        if self._algo_inner is None:
            return

        for child in self._algo_inner.winfo_children():
            child.destroy()

        columns = max(1, self._algo_columns)
        for idx, name in enumerate(self.algorithms):
            if name not in self.algorithm_vars:
                self.algorithm_vars[name] = tk.BooleanVar(value=True)
            row = idx // columns
            col = idx % columns
            ttk.Checkbutton(
                self._algo_inner,
                text=name,
                variable=self.algorithm_vars[name],
            ).grid(row=row, column=col, sticky="w", padx=(0, 10), pady=2)

        for col in range(columns):
            self._algo_inner.columnconfigure(col, weight=1)

    def _on_algo_area_resized(self, event: tk.Event) -> None:
        width = int(getattr(event, "width", 0) or 0)
        # Responsive breakpoints for algorithm checkbox columns.
        if width < 360:
            columns = 1
        elif width < 560:
            columns = 2
        elif width < 820:
            columns = 3
        else:
            columns = 4

        if columns != self._algo_columns:
            self._algo_columns = columns
            self._render_algorithm_checkboxes()

    def _discover_extended_algorithms(self) -> None:
        discovered = self._scan_extended_algorithms()
        if not discovered:
            messagebox.showinfo(
                "Discover Algorithms",
                "No additional algorithms found in user benchmark folders.",
            )
            return

        before = set(self.algorithms)
        for name in sorted(discovered):
            if name not in before:
                self.algorithms.append(name)
        self.algorithms = sorted(set(self.algorithms))
        self._render_algorithm_checkboxes()
        added = sorted(set(self.algorithms) - before)
        if added:
            self._enqueue_log(f"Discovered {len(added)} extended algorithms: {', '.join(added)}")
        messagebox.showinfo(
            "Discover Algorithms",
            f"Discovered {len(added)} new algorithm(s)." if added else "No new algorithms were added.",
        )

    def _open_algorithm_runs_dialog(self) -> None:
        selected_algorithms = self._selected_algorithms()
        if selected_algorithms == ["all"]:
            selected_algorithms = self.algorithms
        if not selected_algorithms:
            messagebox.showinfo("Per-Algorithm Runs", "Select at least one algorithm first.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Per-Algorithm Runs")
        dialog.geometry("520x520")
        dialog.transient(self.root)
        dialog.grab_set()

        container = ttk.Frame(dialog, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            container,
            text="Set optional run overrides per algorithm. Leave blank to use global runs.",
        ).pack(anchor=tk.W, pady=(0, 8))

        canvas = tk.Canvas(container, highlightthickness=0, bg="#151922")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        inner = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _sync_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(window, width=canvas.winfo_width())

        inner.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", _sync_scroll)

        entry_vars: Dict[str, tk.StringVar] = {}
        for row, algo in enumerate(sorted(selected_algorithms)):
            ttk.Label(inner, text=algo).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
            var = tk.StringVar(value=str(self.algorithm_runs_overrides.get(algo, "")) if algo in self.algorithm_runs_overrides else "")
            entry_vars[algo] = var
            ttk.Entry(inner, textvariable=var, width=10).grid(row=row, column=1, sticky="w", pady=3)

        button_row = ttk.Frame(dialog, padding=(10, 0, 10, 10))
        button_row.pack(fill=tk.X)

        def _clear_all() -> None:
            for var in entry_vars.values():
                var.set("")

        def _save() -> None:
            updated: Dict[str, int] = {}
            for algo, var in entry_vars.items():
                text = var.get().strip()
                if not text:
                    continue
                try:
                    value = int(text)
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Run value for '{algo}' must be an integer.")
                    return
                if value <= 0:
                    messagebox.showerror("Invalid Input", f"Run value for '{algo}' must be positive.")
                    return
                updated[algo] = value
            self.algorithm_runs_overrides.update(updated)
            for algo in selected_algorithms:
                if algo not in updated and algo in self.algorithm_runs_overrides:
                    del self.algorithm_runs_overrides[algo]
            self._enqueue_log(
                f"Per-algorithm overrides set for {len(self.algorithm_runs_overrides)} algorithm(s)."
            )
            dialog.destroy()

        ttk.Button(button_row, text="Clear", command=_clear_all).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(button_row, text="Save", command=_save).pack(side=tk.RIGHT)

    def _scan_extended_algorithms(self) -> Set[str]:
        candidates: List[Path] = []
        env_dir = os.environ.get("PGSI_ANALYZER_BENCHMARKS_DIR")
        if env_dir:
            candidates.append(Path(env_dir))
        if self.current_project_dir:
            candidates.append(self.current_project_dir)
        candidates.append(Path.cwd() / "benchmarks")
        candidates.append(Path.cwd() / "src" / "pgsi_analyzer" / "benchmarks")

        discovered: Set[str] = set()
        valid_methods = set(self.methods)
        for root in candidates:
            if not root.exists() or not root.is_dir():
                continue
            for algo_dir in root.iterdir():
                if not algo_dir.is_dir():
                    continue
                method_dirs = [p for p in algo_dir.iterdir() if p.is_dir() and p.name in valid_methods]
                if method_dirs:
                    discovered.add(algo_dir.name)
        return discovered

    def _add_path_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        var: tk.StringVar,
        file_kind: str = "file",
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=3)
        if file_kind == "dir":
            cmd = lambda: self._set_var_from_dir(var)
        else:
            cmd = lambda: self._set_var_from_file(var)
        ttk.Button(parent, text="Browse", command=cmd).grid(row=row, column=2, padx=(6, 0), pady=3)

    def _set_var_from_file(self, var: tk.StringVar) -> None:
        selected = filedialog.askopenfilename()
        if selected:
            var.set(selected)

    def _set_var_from_dir(self, var: tk.StringVar) -> None:
        selected = filedialog.askdirectory()
        if selected:
            var.set(selected)

    def _browse_output_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_dir_var.get() or str(Path.cwd()))
        if selected:
            self.output_dir_var.set(selected)

    def _open_output_folder(self) -> None:
        path = Path(self.output_dir_var.get()).expanduser()
        if not path.exists():
            messagebox.showwarning("Output Folder", f"Folder does not exist yet:\n{path}")
            return
        try:
            resolved = path.resolve()
            if os.name == "nt":
                os.startfile(str(resolved))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(resolved)])
            else:
                subprocess.Popen(["xdg-open", str(resolved)])
        except Exception:
            messagebox.showinfo("Output Folder", f"Output folder:\n{path}")

    def _toggle_group(self, mapping: Dict[str, tk.BooleanVar], value: bool) -> None:
        for var in mapping.values():
            var.set(value)

    def _selected_algorithms(self) -> List[str]:
        selected = [name for name, var in self.algorithm_vars.items() if var.get()]
        return selected or ["all"]

    def _selected_methods(self) -> List[str]:
        selected = [name for name, var in self.method_vars.items() if var.get()]
        return selected or ["all"]

    def _on_run(self) -> None:
        if self._is_running:
            messagebox.showinfo("PGSI Run", "A benchmark run is already in progress.")
            return

        try:
            runs = int(self.runs_var.get().strip())
            if runs <= 0:
                raise ValueError("runs must be positive")
            carbon_intensity = float(self.carbon_intensity_var.get().strip())
            alpha = float(self.alpha_var.get().strip())
            beta = float(self.beta_var.get().strip())
            gamma = float(self.gamma_var.get().strip())
        except Exception as exc:
            messagebox.showerror("Invalid Input", f"Please check numeric fields.\n\nDetails: {exc}")
            return

        output_dir = Path(self.output_dir_var.get().strip() or "results")
        env_file_text = self.env_file_var.get().strip()
        env_file = Path(env_file_text) if env_file_text else None

        self._is_running = True
        self._progress_current = 0
        self._progress_total = 0
        self.progress_var.set(0.0)
        self.progress_bar.configure(maximum=100)
        self.progress_label_var.set("Progress: starting...")
        self.run_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status_var.set("Running benchmark suite...")
        self._enqueue_log("=" * 72)
        self._enqueue_log("Starting PGSI benchmark run from GUI...")

        args = self._build_cli_command(
            algorithms=self._selected_algorithms(),
            methods=self._selected_methods(),
            runs=runs,
            output_dir=output_dir,
            carbon_intensity=carbon_intensity,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            env_file=env_file,
            algorithm_runs=self.algorithm_runs_overrides,
            benchmarks_dir=self.current_project_dir,
        )
        self._run_thread = threading.Thread(target=self._run_pipeline_worker, args=(args,), daemon=True)
        self._run_thread.start()

    def _build_cli_command(
        self,
        algorithms: List[str],
        methods: List[str],
        runs: int,
        output_dir: Path,
        carbon_intensity: float,
        alpha: float,
        beta: float,
        gamma: float,
        env_file: Optional[Path],
        algorithm_runs: Dict[str, int],
        benchmarks_dir: Optional[Path],
    ) -> List[str]:
        cmd = [
            sys.executable,
            "-c",
            "from pgsi_analyzer.cli.main import main; raise SystemExit(main())",
            "benchmark",
            "run",
            "--runs",
            str(runs),
            "--output",
            str(output_dir),
            "--carbon-intensity",
            str(carbon_intensity),
            "--alpha",
            str(alpha),
            "--beta",
            str(beta),
            "--gamma",
            str(gamma),
            "--algorithms",
            *algorithms,
            "--methods",
            *methods,
        ]
        if env_file:
            cmd.extend(["--env-file", str(env_file)])
        if algorithm_runs:
            cmd.append("--algorithm-runs")
            for algorithm, run_count in sorted(algorithm_runs.items()):
                cmd.append(f"{algorithm}={run_count}")
        if benchmarks_dir:
            cmd.extend(["--benchmarks-dir", str(benchmarks_dir)])
        return cmd

    def _refresh_algorithms_from_project(self) -> None:
        if self.current_project_dir is None:
            return
        registry = build_registry(self.current_project_dir)
        self.algorithms = list_algorithms_from_registry(registry)
        self._render_algorithm_checkboxes()

    def _is_pgsi_project_dir(self, path: Path) -> bool:
        if not path.exists() or not path.is_dir():
            return False
        valid_methods = set(self.methods)
        for algo_dir in path.iterdir():
            if not algo_dir.is_dir():
                continue
            for method_dir in algo_dir.iterdir():
                if method_dir.is_dir() and method_dir.name in valid_methods and (method_dir / "main.py").exists():
                    return True
        return False

    def _load_project_from_gui(self) -> None:
        path = Path(self.load_project_dir_var.get().strip()).expanduser()
        if not path.exists() or not path.is_dir():
            messagebox.showerror("Load Project", f"Project folder not found:\n{path}")
            return
        if not self._is_pgsi_project_dir(path):
            messagebox.showerror(
                "Load Project",
                f"Folder is not a valid pgsi-analyzer project:\n{path}\n\n"
                "Expected at least one benchmark folder with <algorithm>/<method>/main.py",
            )
            return
        self.current_project_dir = path.resolve()
        self._refresh_algorithms_from_project()
        self._enqueue_log(f"Loaded project: {self.current_project_dir}")
        messagebox.showinfo("Load Project", f"Project loaded:\n{self.current_project_dir}")

    def _create_project_from_gui(self) -> None:
        parent_dir = Path(self.create_parent_dir_var.get().strip()).expanduser()
        project_name = self.create_project_name_var.get().strip()
        if not project_name:
            messagebox.showerror("Create Project", "Project name is required.")
            return
        selected_algorithms = [name for name, var in self.create_algorithm_vars.items() if var.get()]
        if not selected_algorithms:
            messagebox.showerror("Create Project", "Select at least one algorithm.")
            return
        path = parent_dir / project_name
        try:
            generate_benchmark_template(path, algorithms=selected_algorithms, force=False)
        except Exception as exc:
            messagebox.showerror("Create Project", f"Failed to create project:\n{exc}")
            return
        self.current_project_dir = path.resolve()
        self._refresh_algorithms_from_project()
        self._enqueue_log(f"Created project: {self.current_project_dir}")
        messagebox.showinfo("Create Project", f"Project created:\n{self.current_project_dir}")

    def _continue_to_run_page(self) -> None:
        if self.current_project_dir is None:
            messagebox.showinfo(
                "Project Required",
                "Load an existing project or create one before continuing.",
            )
            return
        self.status_var.set(f"Ready. Project: {self.current_project_dir}")
        self.run_page.tkraise()

    def _run_pipeline_worker(self, cmd: List[str]) -> None:
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            if (Path.cwd() / "src").exists():
                existing = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = f"{Path.cwd() / 'src'}{os.pathsep}{existing}" if existing else str(Path.cwd() / "src")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
            assert self._process.stdout is not None
            for line in self._process.stdout:
                self._enqueue_log(line.rstrip("\n"))
            return_code = self._process.wait()
            self._process = None
            if return_code == 0:
                self._enqueue_log("")
                self._enqueue_log("Completed successfully.")
                self.root.after(0, self._on_run_success)
            else:
                self._enqueue_log("")
                self._enqueue_log(f"Run failed with exit code: {return_code}")
                self.root.after(0, lambda: self.status_var.set("Failed. Check run log."))
        except Exception as exc:
            self._enqueue_log("")
            self._enqueue_log(f"Run failed: {exc}")
            self._enqueue_log(traceback.format_exc())
            self.root.after(0, lambda: self.status_var.set("Failed. Check run log."))
        finally:
            self._process = None
            self.root.after(0, self._finish_run)

    def _on_stop(self) -> None:
        if not self._is_running:
            return
        if self._process is None:
            messagebox.showinfo("Stop Run", "Run is starting up. Please wait a moment and try again.")
            return
        confirm = messagebox.askyesno("Stop Run", "Stop the current benchmark run?")
        if not confirm:
            return
        try:
            self._process.terminate()
            self._enqueue_log("Stop requested by user.")
            self.status_var.set("Stopping benchmark suite...")
        except Exception as exc:
            messagebox.showerror("Stop Run", f"Failed to stop run:\n{exc}")

    def _finish_run(self) -> None:
        self._is_running = False
        self.run_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        if self._progress_total > 0 and self._progress_current >= self._progress_total:
            self.progress_label_var.set(f"Progress: {self._progress_total}/{self._progress_total} (complete)")
        elif self._progress_total > 0:
            self.progress_label_var.set(f"Progress: {self._progress_current}/{self._progress_total} (stopped)")
        else:
            self.progress_label_var.set("Progress: idle")

    def _on_run_success(self) -> None:
        """Update status and show GreenScore ranking popup after successful run."""
        self.status_var.set("Completed successfully.")
        self._show_greenscore_pyramid_popup()

    def _get_greenscore_csv_path(self) -> Optional[Path]:
        """Resolve the best candidate path for GreenScore CSV in output directory."""
        output_dir = Path(self.output_dir_var.get().strip() or "results").expanduser().resolve()
        direct = output_dir / "GreenScore.csv"
        if direct.exists():
            return direct
        for pattern in ("*GreenScore*.csv", "*greenscore*.csv", "*.csv"):
            for candidate in output_dir.glob(pattern):
                if "greenscore" in candidate.name.lower():
                    return candidate
        return None

    def _load_greenscore_ranking(self) -> List[tuple[str, float]]:
        """Read GreenScore CSV and return (method, score) sorted ascending."""
        csv_path = self._get_greenscore_csv_path()
        if csv_path is None:
            return []

        ranking: List[tuple[str, float]] = []
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                method = (row.get("method") or "").strip()
                score_text = (row.get("green_score") or row.get("greenscore") or "").strip()
                if not method or not score_text:
                    continue
                try:
                    score = float(score_text)
                except ValueError:
                    continue
                ranking.append((method, score))
        ranking.sort(key=lambda item: item[1])
        return ranking

    def _show_greenscore_pyramid_popup(self) -> None:
        """Display final GreenScore ranking as a pyramid (best at top)."""
        ranking = self._load_greenscore_ranking()
        if not ranking:
            messagebox.showinfo(
                "GreenScore Ranking",
                "Run completed, but no GreenScore.csv ranking data was found in the output directory.",
            )
            return

        popup = tk.Toplevel(self.root)
        popup.title("Final GreenScore Ranking (Pyramid)")
        popup.geometry("620x520")
        popup.transient(self.root)
        popup.grab_set()

        container = ttk.Frame(popup, padding=12)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Most efficient at top (lowest GreenScore)",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        canvas = tk.Canvas(
            container,
            bg="#0F1623",
            highlightthickness=1,
            highlightbackground="#2A3345",
        )
        canvas.grid(row=1, column=0, sticky="nsew")

        def _draw_pyramid(_event=None) -> None:
            canvas.delete("all")
            width = max(canvas.winfo_width(), 560)
            height = max(canvas.winfo_height(), 360)
            top_y = 28
            bottom_y = height - 24
            center_x = width // 2
            half_base = int(width * 0.38)
            levels = max(len(ranking), 1)
            level_h = (bottom_y - top_y) / levels

            # Pyramid silhouette.
            canvas.create_polygon(
                center_x,
                top_y,
                center_x - half_base,
                bottom_y,
                center_x + half_base,
                bottom_y,
                fill="#162236",
                outline="#355173",
                width=2,
            )

            # Tier colors: light at top (best), darker at bottom (least efficient).
            tier_colors = ["#2E8B57", "#327D64", "#3A6F73", "#445F7C", "#4F4F7D", "#5D4A72"]
            for idx, (method, score) in enumerate(ranking):
                y0 = top_y + idx * level_h
                y1 = y0 + level_h
                # Linear width interpolation from apex to base.
                ratio0 = (y0 - top_y) / (bottom_y - top_y) if bottom_y > top_y else 0.0
                ratio1 = (y1 - top_y) / (bottom_y - top_y) if bottom_y > top_y else 0.0
                half_w0 = max(6, half_base * ratio0)
                half_w1 = max(8, half_base * ratio1)
                color = tier_colors[min(idx, len(tier_colors) - 1)]

                canvas.create_polygon(
                    center_x - half_w0,
                    y0,
                    center_x + half_w0,
                    y0,
                    center_x + half_w1,
                    y1,
                    center_x - half_w1,
                    y1,
                    fill=color,
                    outline="#1B2A3D",
                    width=1,
                )

                label = f"{idx + 1}. {method}  ({score:.6f})"
                canvas.create_text(
                    center_x,
                    (y0 + y1) / 2,
                    text=label,
                    fill="#E6EDF3",
                    font=("Segoe UI Semibold", 10),
                )

            canvas.create_text(
                center_x,
                bottom_y + 14,
                text="Least efficient (highest GreenScore)",
                fill="#B8C4D6",
                font=("Segoe UI", 9),
            )

        canvas.bind("<Configure>", _draw_pyramid)
        popup.after(0, _draw_pyramid)

        ttk.Button(container, text="Close", command=popup.destroy).grid(row=2, column=0, sticky="e", pady=(10, 0))

    def _enqueue_log(self, text: str) -> None:
        self._log_queue.put(text)

    def _update_progress_from_log_line(self, line: str) -> None:
        """Update progress widgets from orchestrator progress lines: [x/y]."""
        match = re.search(r"\[(\d+)/(\d+)\]", line)
        if not match:
            return
        current = int(match.group(1))
        total = int(match.group(2))
        if total <= 0:
            return
        self._progress_current = current
        self._progress_total = total
        self.progress_bar.configure(maximum=total)
        self.progress_var.set(current)
        self.progress_label_var.set(f"Progress: {current}/{total}")

    def _schedule_log_pump(self) -> None:
        self._flush_log_queue()
        self.root.after(120, self._schedule_log_pump)

    def _flush_log_queue(self) -> None:
        updated = False
        while True:
            try:
                line = self._log_queue.get_nowait()
            except queue.Empty:
                break
            self._update_progress_from_log_line(line)
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"{line}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
            updated = True

        if updated:
            self.log_text.update_idletasks()


def main() -> int:
    """Launch the PGSI GUI app."""
    root = tk.Tk()
    PGSIGuiApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

