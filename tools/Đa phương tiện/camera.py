"""
Camera OpenCV – chụp ảnh / xem live + quét QR.
Có fallback backend cho Windows (DirectShow -> MSMF -> mặc định),
và tự kiểm tra camera khả dụng để tránh lỗi "không mở được camera".
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import time
import webbrowser

from rich.panel import Panel
from rich.prompt import Prompt
from ui.console import console
from output_paths import output_dir


def _open_camera(cv2, camera_index: int):
    """Mở camera với các backend phù hợp, đặc biệt ổn định hơn trên Windows."""
    attempts = []
    if hasattr(cv2, "CAP_DSHOW"):
        attempts.append((cv2.CAP_DSHOW, "DirectShow"))
    if hasattr(cv2, "CAP_MSMF"):
        attempts.append((cv2.CAP_MSMF, "Media Foundation"))
    attempts.append((cv2.CAP_ANY, "Auto"))

    for backend, name in attempts:
        cap = None
        try:
            cap = cv2.VideoCapture(camera_index, backend)
            if cap is not None and cap.isOpened():
                # Một số webcam Windows mở được nhưng chưa trả frame ngay.
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                for _ in range(8):
                    ret, frame = cap.read()
                    if ret and frame is not None and getattr(frame, "size", 0) > 0:
                        return cap, name, frame
                    time.sleep(0.08)
            if cap is not None:
                cap.release()
        except Exception:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
    return None, None, None


def _choose_camera(cv2) -> Tuple[Optional[int], Optional[object], Optional[str], Optional[object]]:
    """Cho phép chọn camera; nếu index không hợp lệ thì tự dò 0..4."""
    raw = Prompt.ask("[bold]Camera index[/bold] (Enter = tự tìm)", default="").strip()
    if raw:
        try:
            indices = [max(0, int(raw))]
        except ValueError:
            console.print("[yellow]Index không hợp lệ, sẽ tự tìm camera.[/yellow]")
            indices = list(range(5))
    else:
        indices = list(range(5))

    console.print("[dim]Đang tìm camera...[/dim]")
    for idx in indices:
        cap, backend, frame = _open_camera(cv2, idx)
        if cap is not None:
            return idx, cap, backend, frame
    return None, None, None, None


def feature_camera() -> None:
    """Mở camera, hiển thị preview, cho phép chụp ảnh."""
    console.print("[bold cyan]═══ CAMERA OPENCV ═══[/bold cyan]\n")
    console.print(
        "[dim]Phím trong cửa sổ camera:[/dim]\n"
        "  [yellow]s[/yellow] – Chụp ảnh\n"
        "  [yellow]q[/yellow] – Thoát\n"
    )

    try:
        import cv2
    except ImportError:
        console.print("[red]Thiếu OpenCV.[/red] Cài bằng: [yellow]pip install opencv-python[/yellow]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    camera_index, cap, backend, first_frame = _choose_camera(cv2)
    if cap is None:
        console.print(
            "[red]Không thể mở camera.[/red]\n"
            "[dim]Đã thử camera 0–4 và các backend Windows. Hãy kiểm tra quyền Camera, "
            "đóng Zoom/Teams/OBS và thử lại.[/dim]"
        )
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    save_dir = output_dir("camera")
    console.print(f"[green]✓ Camera {camera_index} đã mở ({backend}).[/green]")
    console.print(f"[green]Ảnh lưu tại:[/green] {save_dir.resolve()}")

    try:
        frame = first_frame
        while True:
            if frame is None:
                ret, frame = cap.read()
                if not ret or frame is None:
                    console.print("[red]Không đọc được frame từ camera.[/red]")
                    break

            cv2.imshow("RAGNAROK Camera (s=chup, q=thoat)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("s"):
                filename = save_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                if cv2.imwrite(str(filename), frame):
                    console.print(f"[bold green]✓ Đã chụp:[/bold green] {filename}")
                else:
                    console.print("[red]Không ghi được ảnh.[/red]")
            ret, frame = cap.read()
            if not ret:
                console.print("[red]Camera ngừng trả frame.[/red]")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        try:
            cv2.waitKey(1)
        except Exception:
            pass

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


def _is_url(text: str) -> bool:
    t = text.strip().lower()
    return t.startswith("http://") or t.startswith("https://")


def feature_qr_scan() -> None:
    """Quét QR realtime bằng camera OpenCV."""
    console.print("[bold cyan]═══ QUÉT MÃ QR (CAMERA) ═══[/bold cyan]\n")
    console.print("[dim]Phím trong cửa sổ camera: q/ESC – Thoát[/dim]\n")

    try:
        import cv2
    except ImportError:
        console.print("[red]Thiếu OpenCV.[/red] Cài bằng: [yellow]pip install opencv-python[/yellow]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    camera_index, cap, backend, first_frame = _choose_camera(cv2)
    if cap is None:
        console.print("[red]Không thể mở camera để quét QR.[/red]")
        Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")
        return

    detector = cv2.QRCodeDetector()
    last_data: Optional[str] = None
    console.print(f"[green]✓ Camera {camera_index} đã mở ({backend}). Đưa mã QR vào khung hình...[/green]")

    try:
        frame = first_frame
        while True:
            if frame is None:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

            data, points, _ = detector.detectAndDecode(frame)
            if points is not None and len(points) > 0:
                pts = points.astype(int)
                for i in range(len(pts[0])):
                    cv2.line(frame, tuple(pts[0][i]), tuple(pts[0][(i + 1) % len(pts[0])]), (0, 255, 0), 2)

            if data and data != last_data:
                last_data = data
                console.print(Panel(f"[bold]{data}[/bold]", title="✓ QR phát hiện", border_style="green"))
                cv2.putText(frame, "QR OK - xem terminal", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("RAGNAROK QR Scanner (q=thoat)", frame)
                cv2.waitKey(300)

                if _is_url(data):
                    open_url = Prompt.ask("Mở URL trong trình duyệt?", choices=["y", "n"], default="n")
                    if open_url == "y":
                        try:
                            webbrowser.open(data)
                        except Exception as exc:
                            console.print(f"[red]Không mở được URL:[/red] {exc}")
                else:
                    console.print("[dim]Nội dung text đã được hiển thị ở trên.[/dim]")

                cont = Prompt.ask("Tiếp tục quét?", choices=["y", "n"], default="y")
                if cont == "n":
                    break
                last_data = None

            cv2.imshow("RAGNAROK QR Scanner (q=thoat)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            ret, frame = cap.read()
            if not ret:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        try:
            cv2.waitKey(1)
        except Exception:
            pass

    Prompt.ask("\n[dim]Nhấn Enter để quay lại...[/dim]")


def run() -> None:
    """Entry point chuẩn cho tool_loader: cho chọn giữa Camera và Quét QR."""
    console.print("[bold cyan]═══ CAMERA / QR ═══[/bold cyan]\n")
    choice = Prompt.ask(
        "[bold]1[/bold] = Camera (chụp ảnh)   [bold]2[/bold] = Quét mã QR bằng camera",
        choices=["1", "2"],
        default="1",
    )
    if choice == "1":
        feature_camera()
    else:
        feature_qr_scan()
