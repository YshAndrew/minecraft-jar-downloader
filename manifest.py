# -*- coding: utf-8 -*-
"""Mojang 官方版本清单与下载信息解析（AMD · Andrew Minecraft Downloader）"""

import json
import os
import sys
import time
import urllib.request

APP_NAME = "AMD"
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
MANIFEST_TTL = 3600  # 版本清单缓存时长：1 小时
USER_AGENT = "AndrewMinecraftDownloader/1.0.0 (AMD)"
HTTP_TIMEOUT = 20


class ManifestError(Exception):
    """版本清单相关错误"""


def _app_data_dir():
    """跨平台应用数据目录（打包成 exe 后同样可用）。"""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def _cache_file():
    return os.path.join(_app_data_dir(), "version_manifest_v2.json")


def _http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.load(resp)


def fetch_manifest(use_cache=True, force=False):
    """获取版本清单。

    - use_cache: 缓存未过期时直接读本地，联网失败时自动降级用旧缓存；
    - force: 强制联网刷新。
    """
    cache = _cache_file()
    if not force and use_cache and os.path.isfile(cache):
        if time.time() - os.path.getmtime(cache) < MANIFEST_TTL:
            with open(cache, "r", encoding="utf-8") as f:
                return json.load(f)
    try:
        manifest = _http_json(MANIFEST_URL)
    except Exception as exc:  # 联网失败：若有旧缓存则降级使用
        if use_cache and os.path.isfile(cache):
            with open(cache, "r", encoding="utf-8") as f:
                return json.load(f)
        raise ManifestError(f"获取版本清单失败：{exc}") from exc
    try:
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
    except OSError:
        pass
    return manifest


def list_versions(manifest, include_snapshots=True):
    """返回 [(版本号, 类型), ...]：发布版在前、快照在后，各自按时间倒序。"""
    releases = [(v["id"], "release") for v in manifest["versions"] if v["type"] == "release"]
    snapshots = [(v["id"], "snapshot") for v in manifest["versions"] if v["type"] != "release"]
    if include_snapshots:
        return releases + snapshots
    return releases


def latest_release(manifest):
    """当前最新发布版版本号。"""
    return manifest["latest"]["release"]


def resolve_download(manifest, version_id, kind):
    """解析指定版本、指定类型（server / client）的 jar 下载信息，返回 (url, sha1, size)。"""
    if kind not in ("server", "client"):
        raise ValueError(f"不支持的下载类型：{kind}")
    url = None
    for v in manifest["versions"]:
        if v["id"] == version_id:
            url = v["url"]
            break
    if not url:
        raise ManifestError(f"清单中不存在版本：{version_id}")
    version_json = _http_json(url)
    info = version_json.get("downloads", {}).get(kind)
    if not info or "url" not in info:
        raise ManifestError(f"版本 {version_id} 未提供 {kind} jar 下载（快照/预览版可能缺失）")
    return info["url"], info.get("sha1"), info.get("size")
