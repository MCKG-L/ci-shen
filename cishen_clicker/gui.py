from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    from .__main__ import run_once
    from .config import load_config
    from .control import ControlState, Hotkeys
    from .gui_config import CONFIG_FIELDS, apply_gui_values, extract_gui_values, load_raw_config, save_raw_config
    from .notice import NOTICE_TEXT, NOTICE_TITLE
    from .strategy import MiningStrategy
    from .tool_usage import ToolUsageState
    from .vision import load_templates
except ImportError:
    if __package__ not in {None, ""}:
        raise

    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from cishen_clicker.__main__ import run_once
    from cishen_clicker.config import load_config
    from cishen_clicker.control import ControlState, Hotkeys
    from cishen_clicker.gui_config import CONFIG_FIELDS, apply_gui_values, extract_gui_values, load_raw_config, save_raw_config
    from cishen_clicker.notice import NOTICE_TEXT, NOTICE_TITLE
    from cishen_clicker.strategy import MiningStrategy
    from cishen_clicker.tool_usage import ToolUsageState
    from cishen_clicker.vision import load_templates


class MiningGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("次神挖矿助手")
        self.root.geometry("760x620")
        self.root.resizable(False, False)
        self.root.minsize(760, 620)
        self.root.maxsize(760, 620)

        self.config_path_var = tk.StringVar(value="config.json")
        self.status_var = tk.StringVar(value="空闲")
        self.field_vars = {field.key: tk.StringVar() for field in CONFIG_FIELDS}

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.control: ControlState | None = None
        self.worker: threading.Thread | None = None
        self.hotkeys_installed = False

        self._build_ui()
        self._load_form()
        self.root.after(100, self._drain_log_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        notice_frame = ttk.LabelFrame(outer, text=NOTICE_TITLE)
        notice_frame.pack(fill=tk.X)
        ttk.Label(notice_frame, text=NOTICE_TEXT, wraplength=720, justify=tk.LEFT).pack(
            fill=tk.X, padx=8, pady=6
        )

        config_frame = ttk.LabelFrame(outer, text="配置")
        config_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.config_path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4), pady=8
        )
        ttk.Button(config_frame, text="浏览", command=self._browse_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(config_frame, text="重新载入", command=self._load_form).pack(side=tk.LEFT, padx=4)
        ttk.Button(config_frame, text="保存", command=self._save_form).pack(side=tk.LEFT, padx=(4, 8))

        params_frame = ttk.LabelFrame(outer, text="关键参数")
        params_frame.pack(fill=tk.X, pady=(10, 0))
        for index, field in enumerate(CONFIG_FIELDS):
            row = index // 2
            col = (index % 2) * 2
            if field.kind == "check":
                ttk.Checkbutton(
                    params_frame,
                    text=field.label,
                    variable=self.field_vars[field.key],
                    onvalue="true",
                    offvalue="false",
                ).grid(row=row, column=col, columnspan=2, sticky=tk.W, padx=8, pady=6)
            else:
                ttk.Label(params_frame, text=field.label).grid(row=row, column=col, sticky=tk.W, padx=8, pady=6)
                ttk.Entry(params_frame, textvariable=self.field_vars[field.key], width=22).grid(
                    row=row, column=col + 1, sticky=tk.EW, padx=(4, 12), pady=6
                )
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)

        status_frame = ttk.Frame(outer)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(status_frame, text="状态").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=(8, 0))

        controls_frame = ttk.Frame(outer)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(controls_frame, text="开始/继续F6", command=self._start).pack(side=tk.LEFT)
        ttk.Button(controls_frame, text="暂停F9", command=self._pause).pack(side=tk.LEFT, padx=8)
        ttk.Button(controls_frame, text="结束F10", command=self._stop).pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(outer, text="日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = ScrolledText(log_frame, height=18, state=tk.DISABLED)
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
            raw = load_raw_config(self._config_path())
            values = extract_gui_values(raw)
        except Exception as exc:
            messagebox.showerror("载入失败", str(exc))
            return

        for key, value in values.items():
            self.field_vars[key].set(value)
        self._log(f"已载入配置：{self._config_path()}")

    def _save_form(self) -> Path | None:
        try:
            path = self._config_path()
            raw = load_raw_config(path)
            values = {key: var.get() for key, var in self.field_vars.items()}
            updated = apply_gui_values(raw, values)
            save_raw_config(path, updated)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))
            return None

        self._log(f"已保存配置：{path}")
        return path

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
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
        install_gui_hotkeys(self.root, self._start, self._pause, self._stop)
        self.hotkeys_installed = True
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
            config = load_config(config_path)
            templates = load_templates(config.templates_dir)

            strategy = MiningStrategy()
            tool_state = ToolUsageState(interval_loops=config.tool_interval_loops)
            self._log(f"窗口标题={config.window_title!r} 模板数={len(templates)}")

            while not control.should_stop():
                if not control.wait_until_running():
                    break
                run_once(
                    config,
                    templates,
                    live=True,
                    debug=False,
                    control=control,
                    strategy=strategy,
                    tool_state=tool_state,
                    logger=self._log,
                )
                if control.should_stop():
                    break
                time.sleep(config.loop_interval_seconds)
        except Exception:
            self._log("错误：\n" + traceback.format_exc())
        finally:
            self._log("已结束")
            self.log_queue.put("__STATUS__:已结束")

    def _config_path(self) -> Path:
        return Path(self.config_path_var.get()).expanduser().resolve()

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
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(100, self._drain_log_queue)

    def _on_close(self) -> None:
        if self.control:
            self.control.stop()
        self.root.destroy()


def install_gui_hotkeys(
    root: tk.Tk,
    start_callback,
    pause_callback,
    stop_callback,
    keyboard_module=None,
) -> None:
    try:
        keyboard = keyboard_module
        if keyboard is None:
            import keyboard as keyboard
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少 keyboard 依赖，请运行：python -m pip install -r requirements.txt") from exc

    hotkeys = Hotkeys()

    def schedule(callback):
        return lambda: root.after(0, callback)

    keyboard.add_hotkey(hotkeys.start, schedule(start_callback))
    keyboard.add_hotkey(hotkeys.pause, schedule(pause_callback))
    keyboard.add_hotkey(hotkeys.stop, schedule(stop_callback))


def main() -> None:
    root = tk.Tk()
    MiningGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
