# -*- coding: utf-8 -*-
"""下载引擎：流式下载 + 进度回调 + sha1 校验（AMD · Andrew Minecraft Downloader）"""

import hashlib
import os
import time
import urllib.request

from manifest import HTTP_TIMEOUT, USER_AGENT

CHUNK = 64 * 1024  # 每块 64 KB


class DownloadError(Exception):
    """下载/校验失败"""


def verify_sha1(path, expected_sha1):
    """校验文件 sha1 是否与期望值一致（不区分大小写）。"""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest().lower() == expected_sha1.lower()


def download(url, dest_path, expected_sha1=None, expected_size=None, progress_cb=None):
    """流式下载到临时文件，下载完成后校验 sha1 并重命名到目标路径。

    - progress_cb(downloaded, total, speed)：下载中回调；total 未知时为 None；
    - sha1 不匹配或网络异常时抛出 DownloadError，并清理残留临时文件。
    """
    dest_path = os.path.abspath(dest_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + ".part"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    start = time.monotonic()
    sha1 = hashlib.sha1()
    downloaded = 0
    total = expected_size
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            if total is None:
                try:
                    total = int(resp.headers.get("Content-Length") or 0) or None
                except (TypeError, ValueError):
                    total = None
            with open(tmp_path, "wb") as f:
                while True:
                    block = resp.read(CHUNK)
                    if not block:
                        break
                    f.write(block)
                    sha1.update(block)
                    downloaded += len(block)
                    if progress_cb:
                        elapsed = max(time.monotonic() - start, 1e-6)
                        progress_cb(downloaded, total, downloaded / elapsed)
    except Exception as exc:
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)
        raise DownloadError(f"下载失败：{exc}") from exc

    if expected_sha1:
        actual = sha1.hexdigest().lower()
        if actual != expected_sha1.lower():
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
            raise DownloadError(f"sha1 校验失败（期望 {expected_sha1}，实际 {actual}）")

    os.replace(tmp_path, dest_path)
    return dest_path
