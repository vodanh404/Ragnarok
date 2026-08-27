"""
Tools package – Feature implementations (CLI port từ 2026DHKTMT01-01 + qxresearch).
"""

from .camera import feature_camera, feature_qr_scan
from .qr import feature_qr
from .barcode_tool import feature_barcode
from .weather import feature_weather
from .pokemon import feature_pokemon
from .element import feature_element
from .ai_waifu import feature_ai_waifu
from .tts import feature_tts
from .downloader import feature_downloader
from .password import feature_password
from .wiki import feature_wiki
from .media_player import feature_media_player
from .link_tool import feature_link_tool
from .pdf_tools import feature_pdf_merge, feature_pdf_protect
from .audio_extract import feature_audio_extract
from .screenshot import feature_screenshot
from .voice_recorder import feature_voice_recorder
from .audiobook import feature_audiobook
from .system_monitor import feature_system_monitor
from .terminal_image import feature_terminal_image
from .time_center import feature_time_center

__all__ = [
    "feature_camera",
    "feature_qr_scan",
    "feature_qr",
    "feature_barcode",
    "feature_weather",
    "feature_pokemon",
    "feature_element",
    "feature_ai_waifu",
    "feature_tts",
    "feature_downloader",
    "feature_password",
    "feature_wiki",
    "feature_media_player",
    "feature_link_tool",
    "feature_pdf_merge",
    "feature_pdf_protect",
    "feature_audio_extract",
    "feature_screenshot",
    "feature_voice_recorder",
    "feature_audiobook",
    "feature_system_monitor",
    "feature_terminal_image",
    "feature_time_center",
]
