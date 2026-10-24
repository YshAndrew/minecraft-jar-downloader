# -*- coding: utf-8 -*-
"""AMD 自检（M1 验收 & CI 冒烟）：联网拉取清单 → 下载最新版服务端 jar → sha1 校验。"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manifest import fetch_manifest, latest_release, resolve_download  # noqa: E402
from downloader import download  # noqa: E402


def main():
    print("[1/4] 拉取版本清单 ...", flush=True)
    manifest = fetch_manifest(force=True)
    ver = latest_release(manifest)
    print(f"[2/4] 最新发布版：{ver}", flush=True)
    url, sha1, size = resolve_download(manifest, ver, "server")
    print(f"[3/4] jar 直链：{url}", flush=True)
    tmp = tempfile.mkdtemp(prefix="amd_selftest_")
    dest = os.path.join(tmp, f"minecraft_server_{ver}.jar")

    def cb(d, t, s):
        if t:
            print(f"\r      已下载 {d/1048576:.1f} / {t/1048576:.1f} MB  {s/1048576:.1f} MB/s", end="", flush=True)
        else:
            print(f"\r      已下载 {d/1048576:.1f} MB", end="", flush=True)

    t0 = time.monotonic()
    download(url, dest, expected_sha1=sha1, expected_size=size, progress_cb=cb)
    dt = time.monotonic() - t0
    print(f"\n[4/4] 完成：{dest}", flush=True)
    print(f"      大小 {os.path.getsize(dest):,} 字节 · 耗时 {dt:.1f}s · sha1 校验通过 ✓", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
