from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    from .control import ControlState
    from .gui_config import apply_gui_values, extract_gui_values
    from .modules import get_module_spec, list_module_keys
    from .notice import (
        MODULE_SWITCH_TEXT,
        NOTICE_TEXT,
        NOTICE_TITLE,
        PROJECT_INFO_OR,
        PROJECT_INFO_TITLE,
        PROJECT_INFO_PREFIX,
        PROJECT_INFO_SUFFIX,
        PROJECT_REPOSITORY_GITEE_LABEL,
        PROJECT_REPOSITORY_GITEE_URL,
        PROJECT_REPOSITORY_LABEL,
        PROJECT_REPOSITORY_URL,
        USAGE_TEXT,
        USAGE_TITLE,
    )
    from .windows import set_process_dpi_awareness
    from .workspace_config import WorkspaceConfig, load_workspace_config, save_workspace_config
except ImportError:
    if __package__ not in {None, ""}:
        raise

    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from cishen_clicker.control import ControlState
    from cishen_clicker.gui_config import apply_gui_values, extract_gui_values
    from cishen_clicker.modules import get_module_spec, list_module_keys
    from cishen_clicker.notice import (
        MODULE_SWITCH_TEXT,
        NOTICE_TEXT,
        NOTICE_TITLE,
        PROJECT_INFO_OR,
        PROJECT_INFO_TITLE,
        PROJECT_INFO_PREFIX,
        PROJECT_INFO_SUFFIX,
        PROJECT_REPOSITORY_GITEE_LABEL,
        PROJECT_REPOSITORY_GITEE_URL,
        PROJECT_REPOSITORY_LABEL,
        PROJECT_REPOSITORY_URL,
        USAGE_TEXT,
        USAGE_TITLE,
    )
    from cishen_clicker.windows import set_process_dpi_awareness
    from cishen_clicker.workspace_config import WorkspaceConfig, load_workspace_config, save_workspace_config


def _resource_path(relative_path: str) -> Path:
    """兼容开发模式与 PyInstaller 打包后的资源路径"""
    import sys as _sys

    if getattr(_sys, "frozen", False):
        base = Path(_sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parents[1]
    return base / relative_path


class MiningGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("次神助手")
        self.root.geometry("760x700")
        self.root.resizable(False, False)
        self.root.minsize(760, 700)
        self.root.maxsize(760, 700)

        self._icon_img: tk.PhotoImage | None = None
        icon_path = _resource_path("resources/avatar.png")
        if icon_path.exists():
            self._icon_img = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self._icon_img)

        self.config_path_var = tk.StringVar(value="config.json")
        self.status_var = tk.StringVar(value="空闲")
        self.module_options = list_module_keys()
        self.module_var = tk.StringVar(value=self.module_options[0])
        self.field_vars: dict[str, tk.StringVar] = {}
        self.workspace_config: WorkspaceConfig | None = None
        self.current_page = ""
        self.current_module_key: str | None = None
        self.page_frame = None
        self.params_frame = None
        self.log_text = None

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.control: ControlState | None = None
        self.worker: threading.Thread | None = None

        self._build_ui()
        self._load_form()
        self.root.after(100, self._drain_log_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.page_frame = ttk.Frame(self.root, padding=12)
        self.page_frame.pack(fill=tk.BOTH, expand=True)

    def _clear_page(self) -> None:
        if self.page_frame is None:
            return
        for child in self.page_frame.winfo_children():
            child.destroy()
        self.params_frame = None
        self.log_text = None

    def _show_home_page(self) -> None:
        if self.current_page == "module" and self.workspace_config is not None:
            self._sync_current_fields_to_workspace()
        self._stop_active_session()

        self.current_page = "home"
        self.current_module_key = None
        self.field_vars = {}
        self._clear_page()

        if self.page_frame is None:
            return

        title = ttk.Label(self.page_frame, text="次神助手", font=("Microsoft YaHei", 16, "bold"))
        title.pack(anchor=tk.W)

        content = ttk.Frame(self.page_frame)
        content.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        module_frame = ttk.LabelFrame(content, text="功能模块")
        module_frame.pack(side=tk.LEFT, fill=tk.Y)
        for module_key in self.module_options:
            module_spec = get_module_spec(module_key)
            ttk.Button(
                module_frame,
                text=module_spec.label,
                command=lambda key=module_key: self._open_module(key),
            ).pack(fill=tk.X, padx=10, pady=6)

        info_frame = ttk.Frame(content)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

        usage_frame = ttk.LabelFrame(info_frame, text=USAGE_TITLE)
        usage_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(usage_frame, text=USAGE_TEXT, wraplength=500, justify=tk.LEFT).pack(
            fill=tk.X, padx=10, pady=10
        )

        notice_frame = ttk.LabelFrame(info_frame, text=NOTICE_TITLE)
        notice_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(notice_frame, text=NOTICE_TEXT, wraplength=500, justify=tk.LEFT).pack(
            fill=tk.X, padx=10, pady=10
        )

        project_frame = ttk.LabelFrame(info_frame, text=PROJECT_INFO_TITLE)
        project_frame.pack(fill=tk.X, pady=(10, 0))
        project_intro = ttk.Frame(project_frame)
        project_intro.pack(fill=tk.X, padx=10, pady=(10, 0))
        ttk.Label(project_intro, text=PROJECT_INFO_PREFIX, wraplength=500, justify=tk.LEFT).pack(
            side=tk.LEFT
        )
        link_label = ttk.Label(
            project_intro,
            text=PROJECT_REPOSITORY_LABEL,
            foreground="#0563c1",
            cursor="hand2",
            font=("Microsoft YaHei", 9, "underline"),
        )
        link_label.pack(side=tk.LEFT)
        link_label.bind("<Button-1>", lambda _event: webbrowser.open(PROJECT_REPOSITORY_URL))
        ttk.Label(project_intro, text=PROJECT_INFO_OR).pack(side=tk.LEFT)
        link_label_gitee = ttk.Label(
            project_intro,
            text=PROJECT_REPOSITORY_GITEE_LABEL,
            foreground="#0563c1",
            cursor="hand2",
            font=("Microsoft YaHei", 9, "underline"),
        )
        link_label_gitee.pack(side=tk.LEFT)
        link_label_gitee.bind("<Button-1>", lambda _event: webbrowser.open(PROJECT_REPOSITORY_GITEE_URL))
        ttk.Label(
            project_frame,
            text=PROJECT_INFO_SUFFIX,
            wraplength=500,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=10, pady=(4, 10))

    def _show_module_page(self, module_key: str) -> None:
        module_spec = get_module_spec(module_key)
        self.current_page = "module"
        self.current_module_key = module_key
        self._clear_page()

        if self.page_frame is None:
            return

        header_frame = ttk.Frame(self.page_frame)
        header_frame.pack(fill=tk.X)
        ttk.Button(header_frame, text="返回首页", command=self._show_home_page).pack(side=tk.LEFT)
        ttk.Label(
            header_frame,
            text=f"{module_spec.label}模块",
            font=("Microsoft YaHei", 14, "bold"),
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Label(self.page_frame, text=MODULE_SWITCH_TEXT).pack(anchor=tk.W, pady=(8, 0))

        config_frame = ttk.LabelFrame(self.page_frame, text="配置")
        config_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.config_path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4), pady=8
        )
        ttk.Button(config_frame, text="浏览", command=self._browse_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(config_frame, text="重新载入", command=self._load_form).pack(side=tk.LEFT, padx=4)
        ttk.Button(config_frame, text="保存", command=self._save_form).pack(side=tk.LEFT, padx=(4, 8))

        self.params_frame = ttk.LabelFrame(self.page_frame, text="关键参数")
        self.params_frame.pack(fill=tk.X, pady=(10, 0))
        self.params_frame.columnconfigure(1, weight=1)
        self.params_frame.columnconfigure(3, weight=1)
        self._render_module_fields()

        if module_key != "mining":
            ttk.Label(
                self.page_frame,
                text="该功能入口已预留，具体自动化流程后续实现。",
            ).pack(fill=tk.X, pady=(8, 0))

        status_frame = ttk.Frame(self.page_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(status_frame, text="状态").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=(8, 0))

        controls_frame = ttk.Frame(self.page_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(controls_frame, text="开始/继续", command=self._start).pack(side=tk.LEFT)
        ttk.Button(controls_frame, text="暂停", command=self._pause).pack(side=tk.LEFT, padx=8)
        ttk.Button(controls_frame, text="结束", command=self._stop).pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(self.page_frame, text="日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = ScrolledText(log_frame, height=16, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _browse_config(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 config.json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")),
        )
        if path:
            self.config_path_var.set(path)
            self._load_form()

    def _load_form(self) -> None:
        try:
            workspace_config = load_workspace_config(self._config_path())
            self.workspace_config = self._ensure_workspace_modules(workspace_config)
        except Exception as exc:
            messagebox.showerror("载入失败", str(exc))
            return

        self.module_var.set(self.workspace_config.active_module)
        if self.current_page == "module":
            self._show_module_page(self.workspace_config.active_module)
        else:
            self._show_home_page()
        self._log(f"已载入配置：{self._config_path()}")

    def _save_form(self) -> Path | None:
        try:
            path = self._config_path()
            if self.workspace_config is None:
                self.workspace_config = self._ensure_workspace_modules(load_workspace_config(path))
            self._sync_current_fields_to_workspace()
            save_workspace_config(path, self.workspace_config)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))
            return None

        self._log(f"已保存配置：{path}")
        return path

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            if self.control and self.control.should_stop():
                self.status_var.set("正在结束")
                self._log("正在结束旧任务，请稍后再开始")
                return
            if self.control:
                self.control.start()
            self.status_var.set("运行中")
            self._log("已继续")
            return

        path = self._save_form()
        if path is None:
            return

        self.control = ControlState()
        self.control.start()
        self.worker = threading.Thread(
            target=self._worker_loop,
            args=(path, self.control),
            daemon=True,
        )
        self.worker.start()
        self.status_var.set("运行中")
        self._log("已开始")

    def _pause(self) -> None:
        if self.control:
            self.control.pause()
        self.status_var.set("已暂停")
        self._log("已暂停")

    def _stop(self) -> None:
        if self.control:
            self.control.stop()
        self.status_var.set("已结束")
        self._log("已结束")

    def _worker_loop(self, config_path: Path, control: ControlState) -> None:
        try:
            workspace_config = self._ensure_workspace_modules(load_workspace_config(config_path))
            module_key = workspace_config.active_module
            module_spec = get_module_spec(module_key)
            runtime = module_spec.create_runtime(workspace_config.modules[module_key], config_path.parent)
            self._log(f"模块={module_spec.label}")

            while not control.should_stop():
                if not control.wait_until_running():
                    break
                module_spec.run_cycle(
                    runtime,
                    live=True,
                    debug=False,
                    control=control,
                    logger=self._log,
                )
                if control.should_stop():
                    break
                time.sleep(_runtime_loop_interval(runtime))
        except Exception:
            self._log("错误：\n" + traceback.format_exc())
        finally:
            self._log("已结束")
            self.log_queue.put("__STATUS__:已结束")

    def _config_path(self) -> Path:
        return Path(self.config_path_var.get()).expanduser().resolve()

    def _on_module_selected(self, _event=None) -> None:
        self._open_module(self.module_var.get())

    def _open_module(self, module_key: str) -> None:
        if module_key not in self.module_options:
            raise KeyError(module_key)
        if self.current_page == "module" and self.workspace_config is not None:
            self._sync_current_fields_to_workspace()
        self._stop_active_session()
        self.module_var.set(module_key)
        if self.workspace_config is not None:
            self.workspace_config = WorkspaceConfig(
                active_module=module_key,
                modules=self.workspace_config.modules,
            )
        self._show_module_page(module_key)

    def _render_module_fields(self) -> None:
        if self.params_frame is None:
            return
        for child in self.params_frame.winfo_children():
            child.destroy()

        module_key = self.module_var.get()
        module_spec = get_module_spec(module_key)
        module_raw = {}
        if self.workspace_config is not None:
            module_raw = self.workspace_config.modules.get(module_key, {})

        self.field_vars = {field.key: tk.StringVar() for field in module_spec.fields}
        values = extract_gui_values(module_raw, module_spec.fields)
        for key, value in values.items():
            self.field_vars[key].set(value)

        tool_toggle_keys = {"use_drill", "use_bomb"}
        tool_toggle_fields = {
            field.key: field
            for field in module_spec.fields
            if field.key in tool_toggle_keys and field.kind == "check"
        }
        visible_fields = [
            field
            for field in module_spec.fields
            if field.key not in tool_toggle_keys
        ]

        for index, field in enumerate(visible_fields):
            row = index // 2
            col = (index % 2) * 2
            if field.kind == "check":
                ttk.Checkbutton(
                    self.params_frame,
                    text=field.label,
                    variable=self.field_vars[field.key],
                    onvalue="true",
                    offvalue="false",
                ).grid(row=row, column=col, columnspan=2, sticky=tk.W, padx=8, pady=6)
            else:
                ttk.Label(self.params_frame, text=field.label).grid(row=row, column=col, sticky=tk.W, padx=8, pady=6)
                ttk.Entry(self.params_frame, textvariable=self.field_vars[field.key], width=22).grid(
                    row=row, column=col + 1, sticky=tk.EW, padx=(4, 12), pady=6
                )

        if tool_toggle_fields:
            row = len(visible_fields) // 2
            col = (len(visible_fields) % 2) * 2
            tool_frame = ttk.Frame(self.params_frame)
            tool_frame.grid(row=row, column=col, columnspan=2, sticky=tk.EW, padx=8, pady=6)
            for col, key, padx in (
                (0, "use_drill", (0, 0)),
                (1, "use_bomb", (24, 0)),
            ):
                field = tool_toggle_fields.get(key)
                if field is None:
                    continue
                ttk.Checkbutton(
                    tool_frame,
                    text=field.label,
                    variable=self.field_vars[field.key],
                    onvalue="true",
                    offvalue="false",
                ).grid(row=0, column=col, sticky=tk.W, padx=padx)

    def _sync_current_fields_to_workspace(self) -> None:
        if self.workspace_config is None:
            return
        module_key = self.module_var.get()
        module_spec = get_module_spec(module_key)
        modules = dict(self.workspace_config.modules)
        module_raw = modules.get(module_key, {})
        values = {key: var.get() for key, var in self.field_vars.items()}
        modules[module_key] = apply_gui_values(module_raw, values, module_spec.fields)
        self.workspace_config = WorkspaceConfig(active_module=module_key, modules=modules)

    def _ensure_workspace_modules(self, workspace_config: WorkspaceConfig) -> WorkspaceConfig:
        modules = dict(workspace_config.modules)
        for module_key in self.module_options:
            modules.setdefault(module_key, {})
        active_module = workspace_config.active_module
        if active_module not in modules:
            active_module = self.module_options[0]
        return WorkspaceConfig(active_module=active_module, modules=modules)

    def _stop_active_session(self) -> None:
        worker = self.worker
        control = self.control
        if worker is None and control is None:
            return

        if control is not None:
            control.stop()
        if worker is not None and worker.is_alive():
            worker.join(1.0)

        self.worker = None
        self.control = None
        self.status_var.set("空闲")

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{stamp}] {message}")

    def _drain_log_queue(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            if message.startswith("__STATUS__:"):
                self.status_var.set(message.split(":", 1)[1])
                continue
            if self.log_text is None:
                continue
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(100, self._drain_log_queue)

    def _on_close(self) -> None:
        if self.control:
            self.control.stop()
        self.root.destroy()


def _runtime_loop_interval(runtime) -> float:
    config = getattr(runtime, "config", None)
    if config is not None:
        return float(getattr(config, "loop_interval_seconds", 0.5))
    if isinstance(runtime, dict):
        raw_config = runtime.get("raw_config", {})
        return float(raw_config.get("loop_interval_seconds", 0.5))
    return 0.5


def main() -> None:
    set_process_dpi_awareness()
    root = tk.Tk()
    MiningGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
