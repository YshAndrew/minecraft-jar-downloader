# -*- coding: utf-8 -*-
"""AMD GUI（tkinter + ttk 定制主题，纯标准库）。
Andrew Minecraft Downloader · 阿曼达 —— Minecraft 服务端 / 客户端 jar 下载器

视觉方向：低饱和「草方块」材质风 —— 石纸底色、苔藓绿主色、泥土棕点缀。
"""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from downloader import DownloadError, download
from manifest import ManifestError, fetch_manifest, latest_release, list_versions, resolve_download

APP_TITLE = "Andrew Minecraft Downloader"
APP_SUBTITLE = "阿曼达下载器"
APP_VERSION = "1.0.0"
KIND_NAMES = {"server": "服务端", "client": "客户端"}

# 低饱和材质配色（草方块主题）
C = {
    "bg":         "#efece4",  # 窗口底色 · 石纸
    "panel":      "#f7f5ef",  # 控件面板
    "panel_dk":   "#e3dfd3",  # 进度槽 / 凹槽
    "border":     "#d6d0c2",
    "text":       "#3a3f38",  # 墨绿灰正文
    "muted":      "#858a7f",
    "accent":     "#5f8a4e",  # 草绿主色
    "accent_dk":  "#47693a",  # 草绿深（按压）
    "accent_lt":  "#cfe0c6",  # 草绿浅（提示）
    "field_bg":   "#ffffff",
    "header":     "#2e3a2c",  # 深苔藓页眉
    "header_tx":  "#f2efe4",
    "header_sub": "#a8b8a0",
    "header_hi":  "#d4b25e",  # 暖金 · 标题首字母高亮
    "ok":         "#4e7a5a",
    "err":        "#a35d4c",
}


def font_family():
    """跨平台中文字体：Windows 用微软雅黑，其余用思源黑体（缺失时回退默认）。"""
    if sys.platform == "win32":
        return "Microsoft YaHei UI"
    return "Noto Sans CJK SC"


def _font_str(fam, size):
    """转成 Tcl 可接受的字体字符串（含空格的家族名需加花括号）。"""
    return f"{{{fam}}} {size}" if " " in fam else f"{fam} {size}"


def default_dir():
    """默认保存目录：用户下载目录下的 Minecraft 文件夹。"""
    if sys.platform == "win32":
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "Downloads", "Minecraft")


def _resource_path(name):
    """兼容源码运行与 PyInstaller 单文件打包的资源定位。"""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", name)


def _apply_window_icon(root):
    """设置窗口图标（assets/icon.png，由 tools/make_icon.py 生成）。"""
    try:
        img = tk.PhotoImage(file=_resource_path("icon.png"))
        root.iconphoto(True, img)
        root._amd_icon = img  # 防止被垃圾回收
    except Exception:
        pass


def setup_style(root):
    """注册整套定制主题（基于 clam，跨平台稳定）。"""
    fam = font_family()
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Amd.TFrame", background=C["bg"])
    style.configure("AmdPanel.TFrame", background=C["panel"])

    style.configure("Amd.TLabel", background=C["bg"], foreground=C["text"], font=(fam, 10))
    style.configure("AmdMuted.TLabel", background=C["bg"], foreground=C["muted"], font=(fam, 9))
    style.configure(
        "AmdHeader.TLabel", background=C["header"], foreground=C["header_tx"],
        font=(fam, 15, "bold"), padding=0, borderwidth=0, relief="flat",
    )
    style.configure(
        "AmdHeaderHi.TLabel", background=C["header"], foreground=C["header_hi"],
        font=(fam, 15, "bold"), padding=0, borderwidth=0, relief="flat",
    )
    style.configure("AmdSub.TLabel", background=C["header"], foreground=C["header_sub"], font=(fam, 9))
    style.configure("AmdStatus.TLabel", background=C["bg"], foreground=C["text"], font=(fam, 10))
    style.configure("AmdOk.TLabel", background=C["bg"], foreground=C["ok"], font=(fam, 10, "bold"))
    style.configure("AmdErr.TLabel", background=C["bg"], foreground=C["err"], font=(fam, 10, "bold"))

    style.configure(
        "Amd.TRadiobutton", background=C["bg"], foreground=C["text"],
        font=(fam, 10), indicatorbackground=C["panel"], indicatorforeground=C["accent"],
    )
    style.map("Amd.TRadiobutton", background=[("active", C["bg"])])

    style.configure(
        "Amd.TCombobox", fieldbackground=C["field_bg"], background=C["field_bg"],
        foreground=C["text"], bordercolor=C["border"], lightcolor=C["border"],
        darkcolor=C["border"], arrowsize=15, padding=4,
    )
    style.map(
        "Amd.TCombobox",
        fieldbackground=[("readonly", C["field_bg"])],
        foreground=[("readonly", C["text"])],
        bordercolor=[("focus", C["accent"])],
        lightcolor=[("focus", C["accent"])],
    )

    style.configure(
        "Amd.TEntry", fieldbackground=C["field_bg"], foreground=C["text"],
        bordercolor=C["border"], lightcolor=C["border"], darkcolor=C["border"], padding=4,
    )
    style.map(
        "Amd.TEntry",
        bordercolor=[("focus", C["accent"])],
        lightcolor=[("focus", C["accent"])],
        darkcolor=[("focus", C["accent"])],
    )

    style.configure(
        "Amd.TButton", background=C["accent"], foreground="#f6f4ec",
        bordercolor=C["accent_dk"], font=(fam, 10, "bold"), padding=(16, 6),
    )
    style.map(
        "Amd.TButton",
        background=[("active", C["accent_dk"]), ("disabled", "#b8b3a4")],
        foreground=[("disabled", "#eceae0")],
        bordercolor=[("disabled", "#a39d8f")],
    )

    style.configure(
        "AmdSec.TButton", background=C["panel"], foreground=C["text"],
        bordercolor=C["border"], font=(fam, 9), padding=(10, 4),
    )
    style.map(
        "AmdSec.TButton",
        background=[("active", C["panel_dk"])],
        foreground=[("active", C["text"])],
    )

    style.configure(
        "Amd.Horizontal.TProgressbar", background=C["accent"], troughcolor=C["panel_dk"],
        bordercolor=C["border"], lightcolor=C["accent"], darkcolor=C["accent"],
    )

    # 下拉列表样式
    root.option_add("*TCombobox*Listbox.font", _font_str(fam, 10))
    root.option_add("*TCombobox*Listbox.background", C["field_bg"])
    root.option_add("*TCombobox*Listbox.foreground", C["text"])
    root.option_add("*Font", _font_str(fam, 10))
    return style


class AmdApp:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP_TITLE} v{APP_VERSION}")
        root.geometry("680x470")
        root.minsize(620, 440)
        setup_style(root)
        _apply_window_icon(root)
        self.msg_queue = queue.Queue()
        self.worker = None
        self._build_widgets()
        self.refresh_versions()

    def _build_widgets(self):
        # ---- 页眉（标题首字母 A / M / D 以暖金高亮）----
        head = tk.Frame(self.root, bg=C["header"], height=64)
        head.pack(fill="x")
        head.pack_propagate(False)
        title_row = tk.Frame(head, bg=C["header"])
        title_row.pack(anchor="w", padx=18, pady=(10, 0))
        segments = (("A", True), ("ndrew ", False), ("M", True), ("inecraft ", False), ("D", True), ("ownloader", False))
        for text, highlight in segments:
            style_name = "AmdHeaderHi.TLabel" if highlight else "AmdHeader.TLabel"
            ttk.Label(title_row, text=text, style=style_name).pack(side="left")
        ttk.Label(head, text=APP_SUBTITLE, style="AmdSub.TLabel").pack(anchor="w", padx=18)

        # ---- 表单 ----
        body = ttk.Frame(self.root, style="Amd.TFrame", padding=(18, 14, 18, 8))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        pad = {"padx": (0, 8), "pady": 6}

        ttk.Label(body, text="下载类型", style="Amd.TLabel").grid(row=0, column=0, sticky="w", **pad)
        type_row = ttk.Frame(body, style="Amd.TFrame")
        type_row.grid(row=0, column=1, columnspan=2, sticky="w", **pad)
        self.kind = tk.StringVar(value="server")
        ttk.Radiobutton(type_row, text="服务端", variable=self.kind, value="server", style="Amd.TRadiobutton").pack(side="left", padx=(0, 16))
        ttk.Radiobutton(type_row, text="客户端", variable=self.kind, value="client", style="Amd.TRadiobutton").pack(side="left")

        ttk.Label(body, text="游戏版本", style="Amd.TLabel").grid(row=1, column=0, sticky="w", **pad)
        self.version_var = tk.StringVar()
        self.version_cb = ttk.Combobox(body, textvariable=self.version_var, state="readonly", style="Amd.TCombobox")
        self.version_cb.grid(row=1, column=1, sticky="we", **pad)
        ttk.Button(body, text="刷新", style="AmdSec.TButton", command=self.refresh_versions).grid(row=1, column=2, sticky="w", **pad)

        ttk.Label(body, text="保存路径", style="Amd.TLabel").grid(row=2, column=0, sticky="w", **pad)
        self.path_var = tk.StringVar(value=default_dir())
        ttk.Entry(body, textvariable=self.path_var, style="Amd.TEntry").grid(row=2, column=1, sticky="we", **pad)
        ttk.Button(body, text="浏览…", style="AmdSec.TButton", command=self.choose_dir).grid(row=2, column=2, sticky="w", **pad)

        self.download_btn = ttk.Button(body, text="开始下载", style="Amd.TButton", command=self.start_download)
        self.download_btn.grid(row=3, column=1, columnspan=2, sticky="we", pady=(10, 4))

        # ---- 进度与状态 ----
        self.progress = ttk.Progressbar(body, mode="determinate", style="Amd.Horizontal.TProgressbar")
        self.progress.grid(row=4, column=0, columnspan=3, sticky="we", pady=(6, 2))
        self.status_var = tk.StringVar(value="就绪：等待获取版本清单")
        self.status_label = ttk.Label(body, textvariable=self.status_var, style="AmdStatus.TLabel")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="w", **pad)

        # ---- 页脚 ----
        foot = tk.Frame(self.root, bg=C["bg"])
        foot.pack(fill="x", side="bottom")
        ttk.Label(
            foot, text=f"v{APP_VERSION} · 数据源 piston-meta.mojang.com · MIT License",
            style="AmdMuted.TLabel",
        ).pack(anchor="e", padx=18, pady=(0, 8))

        self.root.after(100, self._drain_queue)

    # ---- 版本清单 ----
    def refresh_versions(self):
        self.status_var.set("正在获取版本清单…")
        self.status_label.configure(style="AmdStatus.TLabel")
        self._run_bg(self._load_versions)

    def _load_versions(self):
        try:
            manifest = fetch_manifest()
            versions = list_versions(manifest)
            latest = latest_release(manifest)
            self.msg_queue.put(("versions", versions, latest))
        except ManifestError as exc:
            self.msg_queue.put(("error", str(exc)))

    # ---- 路径选择 ----
    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.path_var.get() or None, title="选择保存文件夹")
        if d:
            self.path_var.set(os.path.normpath(d))

    # ---- 下载 ----
    def start_download(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo(APP_TITLE, "已有下载任务进行中，请稍候")
            return
        kind = self.kind.get()
        version = self.version_var.get().strip()
        dest_dir = self.path_var.get().strip()
        if not version:
            messagebox.showwarning(APP_TITLE, "请先选择游戏版本")
            return
        if not dest_dir:
            messagebox.showwarning(APP_TITLE, "请填写保存路径")
            return
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"无法创建保存目录：\n{exc}")
            return
        filename = f"minecraft_{kind}_{version}.jar"
        dest = os.path.join(dest_dir, filename)
        self.download_btn.state(["disabled"])
        self.progress["value"] = 0
        self.status_var.set(f"准备下载{KIND_NAMES[kind]}（{version}）…")
        self.status_label.configure(style="AmdStatus.TLabel")
        self._run_bg(self._do_download, kind, version, dest)

    def _do_download(self, kind, version, dest):
        try:
            manifest = fetch_manifest()
            url, sha1, size = resolve_download(manifest, version, kind)
            download(
                url, dest,
                expected_sha1=sha1, expected_size=size,
                progress_cb=lambda d, t, s: self.msg_queue.put(("progress", d, t, s)),
            )
            self.msg_queue.put(("done", KIND_NAMES[kind], dest))
        except (DownloadError, ManifestError) as exc:
            self.msg_queue.put(("error", str(exc)))
        except Exception as exc:  # 兜底：任何未预期异常都要反馈给用户而不是闪退
            self.msg_queue.put(("error", f"发生未预期错误：{exc}"))

    # ---- 后台线程与消息泵 ----
    def _run_bg(self, fn, *args):
        self.worker = threading.Thread(target=fn, args=args, daemon=True)
        self.worker.start()

    def _drain_queue(self):
        try:
            while True:
                self._handle(self.msg_queue.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _handle(self, msg):
        tag = msg[0]
        if tag == "versions":
            _, versions, latest = msg
            ids = [v for v, _ in versions]
            self.version_cb["values"] = ids
            self.version_var.set(latest)
            self.status_var.set(f"就绪：已加载 {len(ids)} 个版本")
        elif tag == "progress":
            _, downloaded, total, speed = msg
            if total and speed:
                remain = (total - downloaded) / speed
                self.progress["maximum"] = total
                self.progress["value"] = downloaded
                self.status_var.set(
                    f"{downloaded/1048576:.1f} / {total/1048576:.1f} MB · {speed/1048576:.1f} MB/s · "
                    f"剩余约 {remain:.0f}s"
                )
            else:
                self.status_var.set(f"已下载 {downloaded/1048576:.1f} MB")
        elif tag == "done":
            _, kind, dest = msg
            self.progress["value"] = self.progress["maximum"]
            self.download_btn.state(["!disabled"])
            self.status_var.set("下载完成，sha1 校验通过 ✓")
            self.status_label.configure(style="AmdOk.TLabel")
            if messagebox.askyesno(APP_TITLE, f"{kind}下载完成（sha1 校验通过）\n\n{dest}\n\n打开所在文件夹？"):
                self.open_folder(dest)
        elif tag == "error":
            self.download_btn.state(["!disabled"])
            self.status_var.set("任务失败")
            self.status_label.configure(style="AmdErr.TLabel")
            messagebox.showerror(APP_TITLE, str(msg[1]))

    @staticmethod
    def open_folder(path):
        folder = os.path.dirname(path)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except OSError:
            pass


def main():
    root = tk.Tk()
    AmdApp(root)
    root.mainloop()
