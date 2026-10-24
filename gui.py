# -*- coding: utf-8 -*-
"""AMD GUI（tkinter）：类型 / 版本 / 路径选择 + 进度显示。
Andrew Minecraft Downloader · 阿曼达 (AMD)
"""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from downloader import DownloadError, download
from manifest import ManifestError, fetch_manifest, latest_release, list_versions, resolve_download

APP_TITLE = "Andrew Minecraft Downloader · 阿曼达 (AMD)"
APP_VERSION = "1.0.0"
KIND_NAMES = {"server": "服务端 jar", "client": "客户端 jar"}


def default_dir():
    """默认保存目录：用户下载目录下的 Minecraft 文件夹。"""
    if sys.platform == "win32":
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "Downloads", "Minecraft")


class AmdApp:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP_TITLE} v{APP_VERSION}")
        root.geometry("660x430")
        root.minsize(600, 400)
        self.msg_queue = queue.Queue()
        self.worker = None
        self._build_widgets()
        self.refresh_versions()

    def _build_widgets(self):
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        # 下载类型
        ttk.Label(frm, text="下载类型").grid(row=0, column=0, sticky="w", **pad)
        self.kind = tk.StringVar(value="server")
        ttk.Radiobutton(frm, text="服务端 jar", variable=self.kind, value="server").grid(row=0, column=1, sticky="w", **pad)
        ttk.Radiobutton(frm, text="客户端 jar", variable=self.kind, value="client").grid(row=0, column=2, sticky="w", **pad)

        # 游戏版本
        ttk.Label(frm, text="游戏版本").grid(row=1, column=0, sticky="w", **pad)
        self.version_var = tk.StringVar()
        self.version_cb = ttk.Combobox(frm, textvariable=self.version_var, state="readonly")
        self.version_cb.grid(row=1, column=1, sticky="we", **pad)
        ttk.Button(frm, text="刷新", command=self.refresh_versions).grid(row=1, column=2, sticky="w", **pad)

        # 保存路径
        ttk.Label(frm, text="保存路径").grid(row=2, column=0, sticky="w", **pad)
        self.path_var = tk.StringVar(value=default_dir())
        ttk.Entry(frm, textvariable=self.path_var).grid(row=2, column=1, sticky="we", **pad)
        ttk.Button(frm, text="浏览…", command=self.choose_dir).grid(row=2, column=2, sticky="w", **pad)

        # 下载按钮
        self.download_btn = ttk.Button(frm, text="开始下载", command=self.start_download)
        self.download_btn.grid(row=3, column=1, sticky="we", **pad)

        # 进度与状态
        self.progress = ttk.Progressbar(frm, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, sticky="we", **pad)
        self.status_var = tk.StringVar(value="就绪：等待获取版本清单")
        ttk.Label(frm, textvariable=self.status_var).grid(row=5, column=0, columnspan=3, sticky="w", **pad)

        self.root.after(100, self._drain_queue)

    # ---- 版本清单 ----
    def refresh_versions(self):
        self.status_var.set("正在获取版本清单…")
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
        self.status_var.set(f"准备下载 {KIND_NAMES[kind]}（{version}）…")
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
            self.status_var.set(f"就绪：已加载 {len(ids)} 个版本（默认最新发布版 {latest}）")
        elif tag == "progress":
            _, downloaded, total, speed = msg
            if total:
                self.progress["maximum"] = total
                self.progress["value"] = downloaded
                self.status_var.set(f"{downloaded/1048576:.1f} / {total/1048576:.1f} MB · {speed/1048576:.1f} MB/s")
            else:
                self.status_var.set(f"已下载 {downloaded/1048576:.1f} MB")
        elif tag == "done":
            _, kind, dest = msg
            self.progress["value"] = self.progress["maximum"]
            self.download_btn.state(["!disabled"])
            self.status_var.set("下载完成，sha1 校验通过 ✓")
            if messagebox.askyesno(APP_TITLE, f"{kind} 下载完成（sha1 校验通过）\n\n{dest}\n\n打开所在文件夹？"):
                self.open_folder(dest)
        elif tag == "error":
            self.download_btn.state(["!disabled"])
            self.status_var.set("任务失败")
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
