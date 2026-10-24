# -*- coding: utf-8 -*-
"""生成 AMD 程序图标：16x16 像素画草方块 → 256x256 PNG → assets/icon.ico + icon.png（纯标准库）。"""

import os
import struct
import zlib

# 调色板（低饱和，贴合原版 MC 质感）
PALETTE = {
    "G": (111, 158, 79),    # 草面
    "g": (143, 191, 109),   # 草面亮斑
    "d": (90, 138, 63),     # 草面暗斑
    "D": (138, 98, 56),     # 泥土
    "x": (110, 76, 43),     # 泥土暗斑
    "L": (165, 116, 74),    # 泥土亮斑
}

# 16x16 草方块侧面像素画（上草下泥，边界呈锯齿状）
ROWS = [
    "GGGGGGGGGGGGGGGG",
    "GgGGgGGGGgGGGgGG",
    "GGGGGgGGGGGGGgGG",
    "gGGGgGGGGGgGGGGG",
    "GgDGGGGDgGGGDgGG",
    "DDDxDDxDDDDxDDxD",
    "DDDDDDDxDDDDDDDD",
    "LDDDxDDDDDDLDDDD",
    "DDDDDDDDDxDDDDxD",
    "xDDLDDDDDDDDDDDD",
    "DDDDxDDDDxLDDDDD",
    "DDxDDDDDDDDDDDxD",
    "DDDDDLDDxDDDDDDD",
    "xDDDDDDDDDDxDDDD",
    "DDDDxDDDDDDLDDxD",
    "DDDDDDDDDxDxDDDD",
]

SIZE = 16
SCALE = 16  # 16 -> 256


def _png(width, height, rgba_rows):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in rgba_rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def build_icon():
    px = [[PALETTE[c] + (255,) for c in row] for row in ROWS]
    # 最近邻放大
    big = []
    for row in px:
        for _ in range(SCALE):
            big.append([p for p in row for _ in range(SCALE)])
    png = _png(SIZE * SCALE, SIZE * SCALE, big)
    ico = struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22) + png
    return ico


def main():
    assets = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(assets, exist_ok=True)
    data = build_icon()
    ico_path = os.path.join(assets, "icon.ico")
    png_path = os.path.join(assets, "icon.png")
    with open(ico_path, "wb") as f:
        f.write(data)
    # 窗口图标：ICO 内的 PNG 数据直接另存一份（tk.PhotoImage 原生支持 PNG）
    with open(png_path, "wb") as f:
        f.write(data[22:])
    print(f"icon.ico 已生成：{len(data):,} 字节 → {ico_path}")
    print(f"icon.png 已生成：{os.path.getsize(png_path):,} 字节 → {png_path}")
    # 回读校验
    with open(ico_path, "rb") as f:
        head = f.read(22)
    res, count, _ = struct.unpack("<HHH", head[:6])
    _, _, _, _, planes, bpp, size, offset = struct.unpack("<BBBBHHII", head[6:22])
    assert res == 0 and count == 1 and planes == 1 and bpp == 32 and size == len(data) - 22, "ICO 头校验失败"
    with open(png_path, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n", "PNG 魔数校验失败"
    print("回读校验通过：1 幅 256x256 RGBA 图标（ICO + PNG）")


if __name__ == "__main__":
    main()
