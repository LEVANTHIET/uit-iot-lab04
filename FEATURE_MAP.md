# Bản Đồ Tính Năng & Bất Biến Hệ Thống (Feature Map & Invariants)

> AI Agent BẮT BUỘC đọc và cập nhật tài liệu này ở Bước 3 (Brainstorming), Bước 4 (Lập kế hoạch) và Bước 5 (Xác minh).

## 1. Kiến trúc Phân tầng & Ranh giới Thư mục (Profile: `python-iot-ai`)
- **`common/`**: Hằng số dùng chung (tên thiết bị, token mẫu, MQTT topic, tên phương thức RPC).
- **`core/`**: Thuật toán chuẩn hóa dữ liệu cảm biến, chuyển đổi Telemetry thành bản ghi Logs 5 trường, lọc và xuất CSV/Excel. Cấm import từ `ui/`, `dashboard/`, `api/` hoặc `cloud/`.
- **`dashboard/`**: Bộ cấu hình ThingsBoard Dashboard JSON và Custom Widget (`dashboard/widgets/`) nhúng trực tiếp trong ThingsBoard CE.
- **`cloud/`**: Client gọi ThingsBoard REST API để tự động khởi tạo thiết bị, nạp Custom Widget, nạp Dashboard và hỗ trợ xuất dữ liệu từ CLI.
- **`edge/`**: Bộ giả lập 2 mạch ESP32 (`edge/simulator/`) và mã nguồn Arduino `.ino` (`edge/firmware/`). Cấm `edge/` import từ `cloud/` hoặc `dashboard/`.

## 2. Luồng Nghiệp Vụ Sống Còn (Critical User / System Flows)
| Mã luồng | Tên luồng tính năng | Điểm vào (Entry Point) | Kết quả kỳ vọng & Tiêu chí Runtime Verification |
| :--- | :--- | :--- | :--- |
| `FLOW-01` | Triển khai ThingsBoard CE nội bộ qua Docker | `docker/docker-compose.yml` | Khởi chạy `thingsboard/tb-postgres` cổng Web `9090` và MQTT `1883`, truy cập `http://localhost:9090` không lỗi. |
| `FLOW-02` | Thu thập & hiển thị trạng thái kết nối 2 thiết bị ESP32 | `cloud/provision.py`, `edge/simulator/esp32_sim.py` | Bảng thiết bị trên Dashboard ThingsBoard hiển thị đủ `ESP32-Node1-Light-LED` và `ESP32-Node2-Temp-Humid` kèm trạng thái hoạt động. |
| `FLOW-03` | Màn hình chính & điều khiển 2 đèn LED thời gian thực | `edge/simulator/rpc_handler.py`, ThingsBoard Switch RPC | Hiển thị giá trị tức thời của 3 cảm biến; bật/tắt 2 công tắc LED gửi RPC `setLed1`/`setLed2` và phản hồi trạng thái tức thì. |
| `FLOW-04` | Biểu đồ thời gian thực 3 thông số cảm biến | `dashboard/builder.py` | 3 biểu đồ đường thời gian thực cập nhật liên tục cho `temperature`, `humidity`, `illuminance`. |
| `FLOW-05` | Bảng Logs hệ thống 5 trường trong ThingsBoard | `dashboard/widgets/logs_export_widget.js` | Hiển thị đủ 5 cột: `ID thiết bị`, `Tên thiết bị`, `Tên giá trị`, `Giá trị cảm biến`, `Thời gian nhận dữ liệu`. |
| `FLOW-06` | Lọc dữ liệu & tải xuống CSV/Excel | `dashboard/widgets/logs_export_widget.js`, `core/logs_exporter.py` | Lọc theo thiết bị, tên giá trị, từ khóa thời gian và tải về file `.csv` / `.xls` (`.xlsx` qua CLI) mở được chuẩn UTF-8. |

## 3. Các Bất Biến Kỹ Thuật (System Invariants - Không bao giờ được vi phạm)
1. **Zero Local Hardcode**: Không có đường dẫn tuyệt đối máy cá nhân hoặc secret cứng bất hợp lệ trong mã nguồn.
2. **Local-Production Parity**: Mọi thư viện import đều phải được khóa phiên bản trong `requirements.txt`.
3. **Zero Code Debt**: Không file nào > 350 dòng, không hàm nào > 50 dòng hoặc độ phức tạp Cyclomatic > 10; không để lại code cũ bị comment-out; không dùng `# noqa` hay `# type: ignore`.
4. **100% Thuần ThingsBoard UI**: Toàn bộ giao diện Dashboard, biểu đồ, công tắc điều khiển LED và bảng Logs + Filter/Export chạy trực tiếp bên trong ThingsBoard CE.
