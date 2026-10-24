# Andrew Minecraft Downloader（AMD · 阿曼达）

下载 Minecraft 原版 **服务端 / 客户端 jar** 的小工具：图形界面、可选保存路径、带速度与剩余时间的进度显示、下载后按官方 sha1 校验。纯 Python 标准库实现，零第三方依赖，可打包为免 Python 环境的单文件 exe。

## 功能

- 支持下载原版服务端 jar（server）与客户端 jar（client），界面内一键切换
- 版本列表实时取自 Mojang 官方接口，默认最新发布版，发布版 / 快照均可选
- 保存路径可选：系统文件夹选择框或手动输入（默认 `~/Downloads/Minecraft`）
- 后台线程下载，进度条 + 速度显示，不卡界面
- 下载完成自动按官方 sha1 逐字节校验，失败明确提示并清理残留
- 版本清单本地缓存 1 小时，断网时自动降级使用旧缓存

## 运行（源码）

```bash
python main.py
```

需要 Python 3.8+，无需安装任何第三方包。

## 自检

```bash
python selftest.py
```

联网拉取版本清单 → 下载最新发布版服务端 jar → sha1 校验，全部通过输出 `✓`。

## 打包 exe

本地（Windows）：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AndrewMinecraftDownloader --icon assets/icon.ico main.py
```

产物在 `dist/AndrewMinecraftDownloader.exe`，目标电脑无需安装 Python。

## GitHub Actions 自动构建

推送到 `main` 分支后自动在 Windows 上完成上述打包，产物可在 Actions 页面下载；推送 `v*` 标签（如 `v1.0.0`）时会自动生成 Release 并附带 exe。

## 图标

`assets/icon.ico` 由 `tools/make_icon.py` 生成（16x16 草方块像素画放大到 256x256，纯标准库），可自行修改后重新生成；CI 打包时也会自动生成。

## 许可

MIT License，见 [LICENSE](LICENSE)。
