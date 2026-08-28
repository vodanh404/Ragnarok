from __future__ import annotations

import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from rich.prompt import Confirm, Prompt
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

# --- Đồng bộ với kiến trúc RAGNAROK (không tạo Console() riêng) ---
# ui.console.console chính là rich.get_console(); mọi Prompt/Confirm không
# truyền console= sẽ dùng cùng instance → theme đồng bộ toàn app.
try:
    from output_paths import output_dir
except ImportError:  # chạy standalone ngoài project
    def output_dir(name: str) -> Path:
        base = Path(__file__).resolve().parents[2] / "output"
        if not base.exists():
            base = Path.cwd() / "output"
        base.mkdir(parents=True, exist_ok=True)
        path = base / name
        path.mkdir(parents=True, exist_ok=True)
        return path

try:
    from ui.console import console
except ImportError:
    import rich

    console = rich.get_console()

# Metadata cho tool_loader (menu động).
TOOL_NAME = "Tải video / nhạc (Universal Media Downloader)"
CATEGORY = "Mạng"

SUPPORTED_DIRECT_EXTS = {
    ".mp4",
    ".m4v",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
    ".ts",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".wav",
    ".ogg",
    ".opus",
}
STREAM_EXTS = {".m3u8", ".mpd"}
MEDIA_QUERY_KEYS = ("format", "mime", "type", "ext", "video", "audio", "manifest")

INVALID_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
MULTISPACE_RE = re.compile(r"\s+")


@dataclass
class BrowserMedia:
    url: str
    kind: str  # stream / direct
    content_type: str = ""


@dataclass
class DownloadConfig:
    url: str
    mode: str  # video / audio
    quality: str
    output_dir: Path
    playlist: bool = False
    cookies_browser: Optional[str] = None
    subtitles: bool = False
    thumbnail: bool = False
    embed_subtitles: bool = False
    browser_fallback: bool = True
    referer: Optional[str] = None


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def _is_plausible_url(url: str) -> bool:
    try:
        p = urlparse(url.strip())
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def _looks_like_stream(url: str) -> bool:
    path = unquote(urlparse(url).path).lower()
    return any(path.endswith(ext) for ext in STREAM_EXTS)


def _looks_like_direct_media(url: str) -> bool:
    path = unquote(urlparse(url).path).lower()
    return any(path.endswith(ext) for ext in SUPPORTED_DIRECT_EXTS)


def _sanitize_filename(name: str, fallback: str = "media") -> str:
    name = unquote(name or "").strip()
    name = INVALID_FILENAME_RE.sub("_", name)
    name = name.replace("\n", " ").replace("\r", " ")
    name = MULTISPACE_RE.sub(" ", name).strip(" .")
    # Windows reserved device names.
    stem_upper = name.split(".", 1)[0].upper()
    if (
        stem_upper in {"CON", "PRN", "AUX", "NUL"}
        or re.fullmatch(r"COM[1-9]", stem_upper)
        or re.fullmatch(r"LPT[1-9]", stem_upper)
    ):
        name = f"_{name}"
    return (name or fallback)[:180].rstrip(" .")


def _safe_subdir(root: Path, requested: str) -> Path:
    """Chỉ cho phép thư mục con bên trong root; chặn path traversal."""
    requested = (requested or "").strip()
    if not requested:
        return root
    clean = requested.replace("\\", "/").strip("/")
    parts = [p for p in clean.split("/") if p not in {"", ".", ".."}]
    if not parts:
        return root
    safe_parts = [_sanitize_filename(p, "downloads") for p in parts]
    result = root.joinpath(*safe_parts)
    try:
        result.resolve().relative_to(root.resolve())
    except ValueError:
        return root
    return result


def _import_ytdlp():
    try:
        import yt_dlp  # type: ignore

        return yt_dlp
    except ImportError:
        return None


def _extract_filename_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    candidate = Path(path).name
    candidate = candidate.rsplit("?", 1)[0]
    if candidate:
        return _sanitize_filename(Path(candidate).stem, "media")
    return "media"


def _guess_extension(content_type: str, url: str, default: str = ".bin") -> str:
    path_ext = Path(unquote(urlparse(url).path)).suffix.lower()
    if path_ext in SUPPORTED_DIRECT_EXTS:
        return path_ext
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    mapping = {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
        "video/x-matroska": ".mkv",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
        "audio/ogg": ".ogg",
        "audio/opus": ".opus",
        "audio/wav": ".wav",
    }
    return mapping.get(ctype, default)


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for i in range(1, 10000):
        candidate = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError("Không thể tạo tên file duy nhất.")


def _print_dependencies() -> None:
    console.print(
        "[dim]Phụ thuộc: yt-dlp; FFmpeg cho ghép/chuyển đổi; Playwright tùy chọn cho fallback.[/dim]"
    )
    if not _ffmpeg_available():
        console.print("[yellow]⚠ FFmpeg chưa có trong PATH.[/yellow]")


def _browser_cookie_supported(browser: str) -> bool:
    return browser.lower() in {
        "chrome",
        "chromium",
        "edge",
        "firefox",
        "brave",
        "opera",
        "vivaldi",
        "safari",
    }


def _build_headers(referer: Optional[str] = None) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _direct_download(url: str, out_dir: Path, referer: Optional[str] = None) -> Path:
    """Download a direct media URL (không Range)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = _build_headers(referer)
    probe_name = _extract_filename_from_url(url)
    req = Request(url, headers=headers, method="GET")

    with urlopen(req, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        total = int(response.headers.get("Content-Length") or 0)
        ext = _guess_extension(content_type, url)
        target = _unique_path(out_dir / f"{probe_name}{ext}")
        tmp = target.with_suffix(target.suffix + ".part")
        existing = tmp.stat().st_size if tmp.exists() else 0
        mode = "wb"
        if existing:
            console.print(
                "[yellow]Máy chủ không xác nhận resume; tải lại phần file dang dở.[/yellow]"
            )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Đang tải", total=total or None)
            with tmp.open(mode) as f:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
        tmp.replace(target)
        return target


def _direct_resume_download(
    url: str,
    out_dir: Path,
    referer: Optional[str] = None,
    retries: int = 3,
) -> Path:
    """Direct download có HTTP Range + retry."""
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = _build_headers(referer)
    base = _extract_filename_from_url(url)
    temp_base = out_dir / f".{base}.download.part"

    for attempt in range(1, retries + 1):
        try:
            existing = temp_base.stat().st_size if temp_base.exists() else 0
            req_headers = dict(headers)
            if existing:
                req_headers["Range"] = f"bytes={existing}-"
            req = Request(url, headers=req_headers, method="GET")
            with urlopen(req, timeout=30) as response:
                status = getattr(response, "status", 200)
                content_type = response.headers.get("Content-Type", "")
                content_length = int(response.headers.get("Content-Length") or 0)
                is_partial = status == 206 and existing > 0
                total = existing + content_length if is_partial else content_length
                if existing and not is_partial:
                    existing = 0
                    temp_base.unlink(missing_ok=True)

                ext = _guess_extension(content_type, url)
                target = _unique_path(out_dir / f"{base}{ext}")
                written = existing
                open_mode = "ab" if is_partial else "wb"

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        f"Đang tải {base}",
                        total=total or None,
                        completed=written,
                    )
                    with temp_base.open(open_mode) as f:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)
                            written += len(chunk)
                            progress.update(task, completed=written)

                temp_base.replace(target)
                return target
        except Exception as exc:
            console.print(f"[yellow]Lần thử {attempt}/{retries} thất bại: {exc}[/yellow]")
            if attempt < retries:
                time.sleep(1.5 * attempt)

    raise RuntimeError("Tải trực tiếp thất bại sau nhiều lần thử.")


def _safe_format_selector(quality: str, mode: str, ffmpeg: bool) -> str:
    if mode == "audio":
        return "bestaudio/best"
    if quality == "best":
        return "bv*+ba/b" if ffmpeg else "best[ext=mp4]/best"
    if quality == "balanced":
        return (
            "bv*[height<=1080]+ba/b[height<=1080]"
            if ffmpeg
            else "best[height<=1080][ext=mp4]/best[height<=1080]/best"
        )
    if quality.isdigit():
        h = int(quality)
        return (
            f"bv*[height<={h}]+ba/b[height<={h}]"
            if ffmpeg
            else f"best[height<={h}][ext=mp4]/best[height<={h}]/best"
        )
    return "bv*+ba/b" if ffmpeg else "best[ext=mp4]/best"


def _make_ydl_opts(cfg: DownloadConfig, ytdlp: Any, for_stream: bool = False) -> dict[str, Any]:
    ffmpeg = _ffmpeg_available()
    opts: dict[str, Any] = {
        "outtmpl": str(cfg.output_dir / "%(title).180B.%(ext)s"),
        "noplaylist": not cfg.playlist,
        "continuedl": True,
        "retries": 5,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 4,
        "file_access_retries": 3,
        "socket_timeout": 20,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_yt_progress_hook],
        "http_headers": _build_headers(cfg.referer),
    }

    if cfg.cookies_browser and _browser_cookie_supported(cfg.cookies_browser):
        opts["cookiesfrombrowser"] = (cfg.cookies_browser.lower(),)

    if cfg.mode == "video":
        opts["format"] = _safe_format_selector(cfg.quality, "video", ffmpeg)
        if ffmpeg:
            opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bestaudio/best"
        if ffmpeg:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

    if cfg.subtitles:
        opts.update(
            {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["vi", "en", "*"],
                "subtitlesformat": "vtt/srt/best",
            }
        )
    if cfg.thumbnail:
        opts["writethumbnail"] = True
    if cfg.embed_subtitles and ffmpeg and cfg.mode == "video":
        opts["embedsubtitles"] = True

    if for_stream:
        opts["noplaylist"] = True
        opts["extract_flat"] = False
    return opts


def _yt_progress_hook(data: dict[str, Any]) -> None:
    status = data.get("status")
    if status == "finished":
        filename = data.get("filename") or ""
        if filename:
            console.print(f"[green]✓ Stream hoàn tất:[/green] {Path(filename).name}")
    elif status == "error":
        console.print("[red]✗ yt-dlp báo lỗi ở một stream.[/red]")


def _ydlp_download(cfg: DownloadConfig, url: str, stream_mode: bool = False) -> bool:
    ytdlp = _import_ytdlp()
    if ytdlp is None:
        return False
    opts = _make_ydl_opts(cfg, ytdlp, for_stream=stream_mode)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with ytdlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return False
            ydl.download([url])
        return True
    except Exception as exc:
        console.print(f"[yellow]yt-dlp không xử lý được nguồn này: {exc}[/yellow]")
        return False


def _sniff_media_url(page_url: str) -> list[BrowserMedia]:
    """Bắt media public từ network của trang (fallback, không bypass DRM)."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        console.print("[yellow]Playwright chưa cài; bỏ qua browser fallback.[/yellow]")
        return []

    found: dict[str, BrowserMedia] = {}
    console.print("[cyan]Đang quét player bằng trình duyệt để tìm media public...[/cyan]")

    def handle_response(response: Any) -> None:
        try:
            url = response.url
            lower = url.lower()
            ctype = (response.headers.get("content-type") or "").lower()
            if (
                any(ext in lower for ext in (".m3u8", ".mpd"))
                or "mpegurl" in ctype
                or "dash+xml" in ctype
            ):
                found[url] = BrowserMedia(url, "stream", ctype)
            elif (
                any(ext in urlparse(lower).path for ext in (".mp4", ".webm", ".m4v", ".mov"))
                or ctype.startswith("video/")
            ):
                found[url] = BrowserMedia(url, "direct", ctype)
            elif ctype.startswith("audio/") and any(k in lower for k in MEDIA_QUERY_KEYS):
                found[url] = BrowserMedia(url, "direct", ctype)
        except Exception:
            pass

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=_build_headers()["User-Agent"],
                java_script_enabled=True,
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.on("response", handle_response)
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            candidates = [
                "video",
                "button[aria-label*='Play' i]",
                "button[title*='Play' i]",
                "[class*='play' i]",
                "[id*='play' i]",
            ]
            for selector in candidates:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=500):
                        loc.click(timeout=800)
                        page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

            page.wait_for_timeout(2500)
            context.close()
            browser.close()
    except Exception as exc:
        console.print(f"[yellow]Browser fallback không thành công: {exc}[/yellow]")

    items = list(found.values())
    manifests = [m for m in items if m.kind == "stream"]
    direct = [m for m in items if m.kind == "direct"]
    return manifests + direct


def _cookie_browser_menu() -> Optional[str]:
    choices = [
        "none",
        "chrome",
        "edge",
        "firefox",
        "brave",
        "opera",
        "vivaldi",
        "chromium",
        "safari",
    ]
    value = Prompt.ask(
        "Cookie trình duyệt (hỗ trợ trang yêu cầu phiên đăng nhập)",
        choices=choices,
        default="none",
    )
    return None if value == "none" else value


def _ask_quality(mode: str) -> str:
    if mode == "audio":
        return "audio"
    console.print(
        "[dim]Chất lượng: best | balanced | 2160 | 1440 | 1080 | 720 | 480 | 360[/dim]"
    )
    return Prompt.ask("Chất lượng tối đa", default="best").strip().lower()


def _playwright_available() -> bool:
    try:
        import playwright  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def _show_system_info() -> None:
    console.print(
        f"[dim]Python: {sys.version.split()[0]} | "
        f"FFmpeg: {'✓' if _ffmpeg_available() else '✗'} | "
        f"yt-dlp: {'✓' if _import_ytdlp() else '✗'} | "
        f"Playwright: {'✓' if _playwright_available() else '✗'}[/dim]"
    )


def _post_download_summary(out_dir: Path) -> None:
    console.print(f"[bold green]✓ Hoàn tất[/bold green] → {out_dir.resolve()}")
    try:
        files = sorted(out_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        media = [p for p in files if p.is_file()][:8]
        if media:
            console.print("[dim]File gần nhất:[/dim]")
            for p in media:
                try:
                    size_mb = p.stat().st_size / (1024 * 1024)
                    console.print(f"  • {p.name} ({size_mb:.1f} MB)")
                except OSError:
                    console.print(f"  • {p.name}")
    except OSError:
        pass


def feature_downloader() -> None:
    """Interactive Universal Media Downloader – entry UI."""
    console.print("[bold cyan]╔════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║        UNIVERSAL MEDIA DOWNLOADER          ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════════════╝[/bold cyan]\n")
    _show_system_info()

    raw_url = Prompt.ask("[bold]URL media[/bold]").strip()
    if not raw_url:
        console.print("[red]URL trống. Hủy.[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return
    if not _is_plausible_url(raw_url):
        console.print("[red]URL không hợp lệ. Cần http:// hoặc https://[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    mode = Prompt.ask(
        "[bold]Loại media[/bold] ([cyan]1[/cyan]=Video, [cyan]2[/cyan]=Audio)",
        choices=["1", "2"],
        default="1",
    )
    mode_name = "video" if mode == "1" else "audio"
    quality = _ask_quality(mode_name)

    root = output_dir("downloads")
    requested_dir = Prompt.ask("[bold]Thư mục con[/bold]", default="").strip()
    out_dir = _safe_subdir(root, requested_dir)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        console.print(f"[red]Không tạo được thư mục:[/red] {exc}")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    playlist = Confirm.ask("Cho phép playlist nếu URL hỗ trợ playlist?", default=False)
    cookies_browser = _cookie_browser_menu()
    subtitles = False
    thumbnail = False
    embed_subtitles = False
    if mode_name == "video":
        subtitles = Confirm.ask("Tải subtitle nếu nguồn hỗ trợ?", default=False)
        thumbnail = Confirm.ask("Tải thumbnail nếu nguồn hỗ trợ?", default=False)
        embed_subtitles = subtitles and Confirm.ask(
            "Nhúng subtitle vào video? (cần FFmpeg)", default=False
        )

    browser_fallback = Confirm.ask(
        "Cho phép Playwright fallback khi yt-dlp thất bại?", default=True
    )

    cfg = DownloadConfig(
        url=raw_url,
        mode=mode_name,
        quality=quality,
        output_dir=out_dir,
        playlist=playlist,
        cookies_browser=cookies_browser,
        subtitles=subtitles,
        thumbnail=thumbnail,
        embed_subtitles=embed_subtitles,
        browser_fallback=browser_fallback,
        referer=raw_url,
    )

    console.print(f"\n[dim]Lưu tại:[/dim] {out_dir.resolve()}")
    console.print("[cyan]Đang phân tích nguồn...[/cyan]")

    # 1) yt-dlp
    ytdlp = _import_ytdlp()
    if ytdlp is None:
        console.print("[yellow]yt-dlp chưa được cài. Thử backend direct/browser.[/yellow]")
    else:
        console.print("[cyan]① Thử yt-dlp extractor...[/cyan]")
        if _ydlp_download(cfg, raw_url):
            _post_download_summary(out_dir)
            Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
            return

    # 2) Direct media URL
    if _looks_like_direct_media(raw_url):
        console.print("[cyan]② Phát hiện direct media URL...[/cyan]")
        try:
            path = _direct_resume_download(raw_url, out_dir, cfg.referer)
            console.print(f"[green]✓ Đã lưu:[/green] {path}")
            Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
            return
        except Exception as exc:
            console.print(f"[yellow]Direct download thất bại: {exc}[/yellow]")

    # 3) Browser network fallback
    if cfg.browser_fallback:
        console.print("[cyan]③ Thử browser network fallback...[/cyan]")
        media = _sniff_media_url(raw_url)
        if media:
            for item in media:
                if item.kind == "stream" and ytdlp is not None:
                    console.print(f"[cyan]Đang thử stream:[/cyan] {item.url[:100]}...")
                    stream_cfg = DownloadConfig(
                        **{**cfg.__dict__, "playlist": False, "referer": raw_url}
                    )
                    if _ydlp_download(stream_cfg, item.url, stream_mode=True):
                        _post_download_summary(out_dir)
                        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
                        return

            for item in media:
                if item.kind == "direct":
                    console.print(f"[cyan]Đang thử direct stream:[/cyan] {item.url[:100]}...")
                    try:
                        path = _direct_resume_download(item.url, out_dir, raw_url)
                        console.print(f"[green]✓ Đã lưu:[/green] {path}")
                        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
                        return
                    except Exception as exc:
                        console.print(f"[yellow]Stream thất bại: {exc}[/yellow]")

    console.print(
        "\n[bold red]✗ Không thể tải nguồn này bằng các backend hiện có.[/bold red]"
    )
    console.print(
        "[dim]Nguyên nhân có thể là DRM, CAPTCHA, yêu cầu đăng nhập, player riêng, "
        "token hết hạn hoặc website chưa được yt-dlp hỗ trợ.[/dim]"
    )
    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


# Entry point chuẩn cho tool_loader (xem tool_loader.py).
run = feature_downloader


if __name__ == "__main__":
    feature_downloader()
