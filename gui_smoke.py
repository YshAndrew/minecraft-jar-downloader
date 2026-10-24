# -*- coding: utf-8 -*-
"""GUI 冒烟测试（CI / 本机）：创建主窗口 → 等待版本清单加载 → 关闭窗口。
用于在打包前捕获控件构建或界面更新链路中的运行时错误。
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk  # noqa: E402

import gui  # noqa: E402
from gui import APP_TITLE, AmdApp  # noqa: E402


def _force_utf8():
    """Windows 控制台默认 cp1252，中文 print 会抛 UnicodeEncodeError；强制 UTF-8 输出。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


_force_utf8()

TIMEOUT = 20  # 版本清单加载超时（秒）


def main():
    # CI 无人值守：弹窗一律替换为空操作，避免清单拉取失败时模态框阻塞整个任务
    gui.messagebox.showerror = lambda *a, **k: None
    gui.messagebox.showwarning = lambda *a, **k: None
    gui.messagebox.showinfo = lambda *a, **k: None
    gui.messagebox.askyesno = lambda *a, **k: False

    root = tk.Tk()
    app = AmdApp(root)
    deadline = time.time() + TIMEOUT
    loaded = []  # 必须在窗口销毁前抓取控件数据，destroy 后控件句柄即失效
    latest = ""

    def poll():
        nonlocal latest
        try:
            vals = app.version_cb["values"]
        except tk.TclError:
            vals = None
        if vals:
            loaded.append(vals)
            latest = app.version_var.get()
            root.destroy()
        elif time.time() > deadline:
            root.destroy()
        else:
            root.after(100, poll)

    poll()
    root.mainloop()

    count = len(loaded[0]) if loaded else 0
    assert count > 0, f"{TIMEOUT}s 内未加载到版本列表"
    print(f"GUI 冒烟通过：{APP_TITLE} · 加载 {count} 个版本 · 默认 {latest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
