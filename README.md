⚔️ Ragnarok Control Center
Bộ công cụ cá nhân chạy trên terminal (Python & Rich), tập hợp nhiều tiện ích vào một giao diện điều khiển duy nhất.
Phiên bản: 1.1.1

✨ Điểm nổi bật
Giao diện terminal trực quan, menu phân nhóm dễ sử dụng.

Quản lý thời gian, xử lý đa phương tiện (ảnh, QR, âm thanh, video, PDF) và giám sát hệ thống (CPU, RAM, GPU, mạng).

Dọn sạch màn hình khi thoát tính năng, tránh chồng nội dung.

Lưu tệp đầu ra gọn gàng theo từng nhóm trong thư mục output/.

💻 Yêu cầu hệ thống
Python: 3.10 trở lên (tối ưu tốt nhất trên Windows).

Phần cứng/Dịch vụ bổ sung: Webcam (cho Camera), Micro (ghi âm), API OpenWeather (thời tiết), và mã Gemini (trò chuyện AI).

📦 Cài đặt

1. Tải mã nguồn

git clone [https://github.com/vodanh404/Ragnarok.git](https://github.com/vodanh404/Ragnarok.git)
cd Ragnarok

2. Tạo môi trường ảo

python -m venv .venv

Kích hoạt trên Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Kích hoạt trên Windows CMD:

.venv\Scripts\activate.bat

3. Cài đặt thư viện

python -m pip install --upgrade pip
pip install -r requirements.txt

4. Khởi chạy

python main.py

🔐 Cấu hình dịch vụ trực tuyến

Thời tiết

Có thể sử dụng biến môi trường:

$env:OPENWEATHER_API_KEY="MA_TRUY_CAP_CUA_BAN"

Hoặc cấu hình trong config.ini theo hướng dẫn trực tiếp của ứng dụng.

Gemini

Có thể sử dụng:

$env:GEMINI_API_KEY="MA_TRUY_CAP_CUA_BAN"

hoặc:

$env:GOOGLE_API_KEY="MA_TRUY_CAP_CUA_BAN"

Không đưa mã truy cập vào GitHub. Nên dùng biến môi trường hoặc tệp cấu hình nằm ngoài phạm vi phiên bản công khai.

🐛 Báo lỗi

Khi báo lỗi, hãy cung cấp:

Phiên bản Python.

Hệ điều hành.

Chức năng gây lỗi.

Toàn bộ thông báo lỗi trong terminal.

Các bước để tái hiện lỗi.

Ví dụ:

Python: 3.12.x
Hệ điều hành: Windows 11
Chức năng: Đồng hồ cà chua
Lỗi: ...
Các bước tái hiện: ...

🤝 Đóng góp

Pull Request và Issue được hoan nghênh.

Khi đóng góp mã nguồn, nên ưu tiên:

Không phá vỡ menu hiện tại.

Không tạo module trùng chức năng.

Giữ giao diện nhất quán.

Xử lý lỗi rõ ràng thay vì để chương trình thoát đột ngột.

Không đưa mã truy cập hoặc thông tin cá nhân vào mã nguồn.

📄 Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem tệp [LICENSE](LICENSE) để biết thêm chi tiết.
Ragnarok Control Center — một menu, nhiều công cụ.
