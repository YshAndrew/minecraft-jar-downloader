# -*- coding: utf-8 -*-
"""GUI 冒烟测试（CI / 本机）：创建主窗口 → 等待版本清单加载 → 关闭窗口。
用于在打包前捕获控件构建或界面更新链路中的运行时错误。
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk  # noqa: E402

from gui import APP_TITLE, AmdApp  # noqa: E402

TIMEOUT = 20  # 版本清单加载超时（秒）


def main():
    root = tk.Tk()
    app = AmdApp(root)
    deadline = time.time() + TIMEOUT

    def poll():
        if app.version_cb["values"]:
            root.destroy()
        elif time.time() > deadline:
            root.destroy()
        else:
            root.after(100, poll)

    poll()
    root.mainloop()

    count = len(app.version_cb["values"])
    latest = app.version_var.get()
    assert count > 0, f"{TIMEOUT}s 内未加载到版本列表"
    print(f"GUI 冒烟通过：{APP_TITLE} · 加载 {count} 个版本 · 默认 {latest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
