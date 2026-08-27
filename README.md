⚔️ Ragnarok Control Center

Ragnarok Control Center là một ứng dụng tiện ích chạy trên terminal, được xây dựng bằng Python và Rich, tập hợp nhiều công cụ thường dùng vào một giao diện điều khiển duy nhất.

Phiên bản hiện tại: 1.1.1

Mục tiêu của dự án là tạo ra một "bộ công cụ cá nhân" gọn gàng, dễ chạy, có giao diện terminal đẹp và có thể mở rộng thêm tính năng mà không làm rối menu chính.

✨ Điểm nổi bật

Giao diện terminal sử dụng Rich với bảng, khung, thanh tiến trình và màn hình động.

Hệ thống menu phân nhóm, dễ tìm chức năng.

Mỗi tính năng được mở trên một màn hình riêng và được dọn sạch khi thoát để hạn chế hiện tượng chồng nội dung.

Trung tâm thời gian gồm đồng hồ, lịch, đếm ngược và đồng hồ cà chua.

Nhiều công cụ xử lý hình ảnh, mã QR, mã vạch, âm thanh, video, PDF và dữ liệu trực tuyến.

Hỗ trợ giám sát CPU, RAM, GPU, ổ đĩa và mạng.

Các tệp đầu ra được gom vào thư mục output/ theo từng nhóm chức năng.

Có thể chạy hoàn toàn từ dòng lệnh, không yêu cầu giao diện cửa sổ riêng.


💻 Yêu cầu hệ thống

Python 3.10 trở lên

Windows được ưu tiên kiểm thử.

Một số chức năng cần phần cứng hoặc dịch vụ bổ sung:

Camera: cần webcam.

Ghi âm: cần micro và môi trường âm thanh hoạt động.

Thời tiết: cần API của OpenWeather.

Trò chuyện AI: cần mã truy cập Gemini.

Tải YouTube: cần kết nối Internet.

Wikipedia và dữ liệu trực tuyến: cần kết nối Internet.

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

🗂️ Thư mục đầu ra

Ragnarok tự tổ chức các tệp được tạo ra trong output/:

output/
├── audio/         # Tệp âm thanh
├── audiobook/     # Sách nói
├── barcode/      # Mã vạch
├── camera/       # Nội dung từ camera
├── downloads/    # Tệp tải xuống
├── pdf/           # Tệp PDF
├── qr/            # Mã QR
├── recordings/   # Bản ghi âm
└── screenshots/  # Ảnh chụp màn hình

Các đường dẫn đầu ra được tập trung qua output_paths.py để hạn chế việc ghi tệp ra ngoài các thư mục được phép.

⌨️ Điều khiển cơ bản

Trong menu chính, chọn số tương ứng với nhóm chức năng.

1  Thị giác và quét mã
2  Tra cứu và dữ liệu
3  Trung tâm thời gian
4  Trí tuệ nhân tạo và giọng nói
5  Đa phương tiện và tệp
6  Công cụ hệ thống
0  Thoát chương trình

Khi một chức năng đang chạy, có thể sử dụng các phím tắt được chức năng đó hiển thị trên màn hình. Với các màn hình động như đồng hồ hoặc đếm ngược, Ctrl+C được dùng để dừng.

⏱️ Trung tâm thời gian

Ragnarok 1.1.1 có riêng một trung tâm cho các công cụ thời gian:

Đồng hồ
Hiển thị giờ, ngày và múi giờ hệ thống theo thời gian thực.

Lịch
Xem lịch tháng, điều hướng tháng trước/tháng sau và đánh dấu ngày hiện tại.

Đếm ngược
Nhập thời lượng theo dạng:

00:05:00

hoặc:

300

Đồng hồ cà chua
Cho phép cấu hình:

Thời gian tập trung.

Nghỉ ngắn.

Nghỉ dài.

Số vòng.

🧹 Không tạo __pycache__

Ứng dụng chủ động đặt:

PYTHONDONTWRITEBYTECODE=1

ngay từ điểm khởi chạy để hạn chế việc Python tạo tệp bytecode .pyc trong quá trình chạy ứng dụng.

Tuy nhiên, nếu bạn chạy từng module riêng bằng Python hoặc sử dụng công cụ phát triển khác, môi trường đó vẫn có thể tạo bytecode. Khi phát hành mã nguồn, nên thêm vào .gitignore:

__pycache__/
*.py[cod]
*$py.class
.venv/
config.ini
output/*

🧪 Trạng thái dự án

Phiên bản: 1.1.1

Bản 1.1.1 tập trung vào:

Ổn định luồng chuyển màn hình.

Dọn màn hình khi vào/thoát chức năng.

Cải thiện các công cụ thời gian.

Ổn định ghi âm và trình phát.

Hạn chế nội dung giao diện bị lưu lại sau khi thoát màn hình động.

Tổ chức tệp đầu ra theo thư mục chức năng.

Dự án vẫn phụ thuộc vào các thư viện và dịch vụ bên ngoài đối với một số tính năng, vì vậy trải nghiệm thực tế có thể khác nhau tùy hệ điều hành, thiết bị, quyền truy cập phần cứng và khả năng kết nối mạng.

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

Dự án này được phân phối dưới giấy phép MIT. Xem tệp LICENSE để biết thêm chi tiết.
⭐ Ragnarok Control Center

Một bộ công cụ terminal nhỏ gọn cho những lúc bạn muốn có nhiều tiện ích trong một chương trình duy nhất.

Ragnarok Control Center — một menu, nhiều công cụ.
