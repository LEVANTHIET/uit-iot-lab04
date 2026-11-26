# UIT IoT Lab 04 — Dashboard ThingsBoard CE & 2x ESP32

Dự án thực hành môn **Công nghệ Internet of Things Hiện đại (UIT — Lab 04)** triển khai nền tảng mã nguồn mở **ThingsBoard Community Edition** nội bộ bằng Docker, kết nối 2 mạch nhúng **ESP32** qua giao thức **MQTT**.

## Kiến trúc hệ thống

- **IoT Platform (Local Docker):** `thingsboard/tb-postgres:3.8.1` tích hợp sẵn Web Dashboard + REST API (`8080`), MQTT Broker (`1883`) và PostgreSQL.
- **ESP32 #1 (`ESP32-Node1-Light-LED`):** Đọc cảm biến ánh sáng `BH1750` (`illuminance`) và điều khiển **2 đèn LED** (`GPIO 18`, `GPIO 19`) qua MQTT Server-side RPC (`setLed1`, `setLed2`).
- **ESP32 #2 (`ESP32-Node2-Temp-Humid`):** Đọc cảm biến `DHT22/DHT11` gửi nhiệt độ (`temperature`) và độ ẩm (`humidity`).
- **Dashboard & Logs Nâng cao:** Đóng gói thuần bên trong ThingsBoard CE, gồm 4 khu vực: Trạng thái thiết bị, Giá trị tức thời + 2 công tắc LED, 3 Biểu đồ thời gian thực, và Custom Widget Logs 5 cột kèm bộ lọc + xuất `CSV`/`Excel`.

## Cấu trúc thư mục

- `docker/`: File `docker-compose.yml` tinh giản tài nguyên cho Laptop.
- `common/`: Hằng số MQTT topics, tên thiết bị, token và tên lệnh RPC.
- `core/`: Logic chuẩn hóa telemetry, chuyển đổi Logs 5 cột, lọc và xuất `.csv` / `.xlsx`.
- `dashboard/`: Custom Widget (HTML/CSS/JS) và script đóng gói Dashboard JSON cho ThingsBoard.
- `cloud/`: Script tự động khởi tạo thiết bị, nạp Widget Bundle, Dashboard qua REST API và CLI xuất file.
- `edge/`: Trình giả lập MQTT 2 mạch ESP32 (`edge/simulator/`) và mã nguồn Arduino thật (`edge/firmware/`).
- `docs/`: Hướng dẫn danh sách linh kiện cần mượn và sơ đồ đấu dây GPIO.
- `tests/`: Bộ kiểm thử đơn vị và Property-based Testing (`unittest` + `hypothesis`).

## Hướng dẫn chạy nhanh

1. **Cài đặt thư viện Python:**
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. **Khởi chạy ThingsBoard Docker:**
   ```powershell
   docker compose -f docker/docker-compose.yml up -d
   ```
3. **Nạp tự động 2 thiết bị, Custom Widget và Dashboard:**
   ```powershell
   python -m cloud.provision --url http://localhost:8080
   ```
4. **Chạy trình giả lập 2 mạch ESP32 (hoặc nạp code trong `edge/firmware/` lên mạch thật):**
   ```powershell
   python -m edge.simulator.esp32_sim --host localhost --port 1883
   ```
5. **Chạy chốt kiểm định chất lượng và test:**
   ```powershell
   ./verify.ps1
   ```
