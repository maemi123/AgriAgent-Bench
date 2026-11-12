"""生成项目仓库二维码（答辩 PPT 用）。

用法：
    python make_qr.py
输出：
    assets/repo_qr.png   —— 纯黑白、带静默区，直接插进 PPT 不会糊
"""

import os

import qrcode
from qrcode.constants import ERROR_CORRECT_M

URL = "https://github.com/maemi123/AgriAgent-Bench"
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "assets", "repo_qr.png")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=16,
        border=4,          # 静默区，扫描识别率的关键（规范建议 4 个模块）
    )
    qr.add_data(URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(OUT)
    print(f"{URL}\n-> {OUT}  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
