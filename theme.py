"""
Theme engine cho RAGNAROK CONTROL CENTER.

Cho phép người dùng tùy chỉnh:
  - Màu chữ (fg_color)
  - Kiểu chữ: đậm / nghiêng / gạch chân / mờ ... (font_style)
  - Màu nền (bg_color)

của toàn bộ giao diện console, áp dụng ngay lập tức và lưu lại vào
config/theme.json để tự động dùng lại ở những lần chạy sau.

Quy tắc: màu chữ và màu nền KHÔNG được trùng nhau (xem `_validate`).

Cách hoạt động (xem thêm ui/console.py):
  Theme.console_base_style() build một style string kiểu Rich (vd:
  "bold red on black") rồi được gán thẳng vào `console.style`. Rich sẽ áp
  style này làm "nền" cho MỌI dòng in ra, kể cả những dòng không gắn thẻ màu
  cụ thể -- trong khi các thẻ màu ngữ nghĩa có sẵn trong project (đỏ = lỗi,
  vàng = cảnh báo, xanh lá = thành công, cyan = tiêu đề mục...) vẫn được giữ
  nguyên vì Rich chỉ ghi đè đúng thuộc tính mà thẻ đó chỉ định, phần còn lại
  (kiểu chữ, màu nền) vẫn kế thừa từ theme.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

CONFIG_DIR = Path(__file__).resolve().parent / "config"
THEME_FILE = CONFIG_DIR / "theme.json"

# Bảng màu chữ / màu nền cho phép chọn: value (tên màu Rich) -> nhãn tiếng Việt
COLOR_CHOICES: Dict[str, str] = {
    "red": "Đỏ",
    "bright_red": "Đỏ tươi",
    "green": "Xanh lá",
    "bright_green": "Xanh lá tươi",
    "yellow": "Vàng",
    "bright_yellow": "Vàng tươi",
    "blue": "Xanh dương",
    "bright_blue": "Xanh dương tươi",
    "magenta": "Tím hồng (magenta)",
    "bright_magenta": "Tím hồng tươi",
    "cyan": "Xanh ngọc (cyan)",
    "bright_cyan": "Xanh ngọc tươi",
    "white": "Trắng",
    "bright_white": "Trắng sáng",
    "black": "Đen",
    "bright_black": "Xám đậm",
    "orange1": "Cam",
    "gold1": "Vàng gold",
    "deep_pink2": "Hồng đậm",
    "spring_green2": "Xanh lá non",
    "dodger_blue1": "Xanh dương neon",
    "turquoise2": "Ngọc lam",
    "violet": "Tím violet",
    "grey62": "Xám nhạt",
}

# Màu nền: giống bảng màu chữ, cộng thêm lựa chọn "mặc định" (không ép nền,
# giữ nguyên nền của terminal).
BACKGROUND_CHOICES: Dict[str, str] = {
    "default": "Mặc định (theo terminal)",
    **COLOR_CHOICES,
}

# Kiểu chữ cho phép chọn: value (style string của Rich) -> nhãn tiếng Việt
FONT_STYLE_CHOICES: Dict[str, str] = {
    "normal": "Thường",
    "bold": "Đậm (bold)",
    "italic": "Nghiêng (italic)",
    "underline": "Gạch chân (underline)",
    "dim": "Mờ (dim)",
    "bold italic": "Đậm + nghiêng",
    "bold underline": "Đậm + gạch chân",
    "italic underline": "Nghiêng + gạch chân",
    "bold italic underline": "Đậm + nghiêng + gạch chân",
}

DEFAULT_FG = "red"
DEFAULT_FONT_STYLE = "bold"
DEFAULT_BG = "default"


@dataclass
class Theme:
    """Một bộ giao diện: màu chữ + kiểu chữ + màu nền."""

    fg_color: str = DEFAULT_FG
    font_style: str = DEFAULT_FONT_STYLE
    bg_color: str = DEFAULT_BG

    def primary_style(self) -> str:
        """Style chính: dùng cho banner, tiêu đề, viền bảng/panel."""
        style = self.font_style if self.font_style != "normal" else ""
        return f"{style} {self.fg_color}".strip()

    def accent_style(self) -> str:
        """Style phụ (luôn đậm) dùng cho header bảng, nhãn phiên bản..."""
        base = self.font_style if "bold" in self.font_style else "bold"
        return f"{base} {self.fg_color}".strip()

    def console_base_style(self) -> str:
        """
        Style áp thẳng lên `console.style`: quyết định màu chữ / kiểu chữ /
        màu nền mặc định cho MỌI dòng in ra trong toàn bộ chương trình.
        """
        parts = []
        if self.font_style and self.font_style != "normal":
            parts.append(self.font_style)
        parts.append(self.fg_color)
        if self.bg_color != "default":
            parts.append(f"on {self.bg_color}")
        return " ".join(parts)

    def as_dict(self) -> dict:
        return asdict(self)


def _validate(fg_color: str, bg_color: str) -> None:
    """Chặn trường hợp màu chữ và màu nền trùng nhau."""
    if bg_color != "default" and fg_color.lower() == bg_color.lower():
        raise ValueError("Màu chữ và màu nền không được trùng nhau.")


def load_theme() -> Theme:
    """Đọc theme đã lưu từ config/theme.json. Trả về theme mặc định nếu
    chưa từng lưu, file hỏng, hoặc dữ liệu không hợp lệ."""
    if THEME_FILE.exists():
        try:
            data = json.loads(THEME_FILE.read_text(encoding="utf-8"))
            fg = str(data.get("fg_color", DEFAULT_FG))
            font_style = str(data.get("font_style", DEFAULT_FONT_STYLE))
            bg = str(data.get("bg_color", DEFAULT_BG))
            _validate(fg, bg)
            if fg not in COLOR_CHOICES or bg not in BACKGROUND_CHOICES:
                raise ValueError("Màu không hợp lệ trong file cấu hình.")
            if font_style not in FONT_STYLE_CHOICES:
                raise ValueError("Kiểu chữ không hợp lệ trong file cấu hình.")
            return Theme(fg_color=fg, font_style=font_style, bg_color=bg)
        except Exception:
            # File cấu hình hỏng/không hợp lệ -> dùng mặc định, không crash app.
            return Theme()
    return Theme()


def save_theme(theme: Theme) -> None:
    """Lưu theme xuống config/theme.json (tự tạo thư mục config/ nếu chưa có)."""
    _validate(theme.fg_color, theme.bg_color)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    THEME_FILE.write_text(
        json.dumps(theme.as_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
