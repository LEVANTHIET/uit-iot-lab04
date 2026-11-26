# Hướng Dẫn Mượn Thiết Bị & Đấu Nối Phần Cứng (2x ESP32)

Tài liệu này mô tả danh sách phần cứng cần mượn và sơ đồ nối dây chuẩn khớp với hai firmware trong `edge/firmware/`.

## 1. Danh sách thiết bị & phụ kiện cần mượn

- **02 mạch ESP32** (DevKit v1 hoặc tương đương; kiểm tra cổng Micro-USB hay Type-C).
- **01 cảm biến ánh sáng BH1750 (GY-302)** đã hàn sẵn hàng chân cắm.
- **01 cảm biến nhiệt độ, độ ẩm DHT22 hoặc DHT11** (ưu tiên module 3 chân có sẵn điện trở kéo lên; nếu dùng loại 4 chân rời cần thêm 01 điện trở `4.7kΩ` hoặc `10kΩ`).
- **02 đèn LED đơn 5mm** (khác màu để dễ phân biệt LED 1 và LED 2).
- **02 điện trở `220Ω` hoặc `330Ω`** mắc nối tiếp bảo vệ LED.
- **01–02 Breadboard** (400 hoặc 830 lỗ) và **~20 sợi dây Jumper** (Đực–Đực, Đực–Cái, Cái–Cái).
- **02 cáp USB truyền dữ liệu** (không dùng cáp chỉ sạc).

## 2. Sơ đồ đấu nối ESP32 #1 (`ESP32-Node1-Light-LED`)

Thiết bị đảm nhiệm đọc cường độ ánh sáng (`BH1750`) và điều khiển thời gian thực **2 đèn LED** qua MQTT RPC.

| Linh kiện | Chân linh kiện | Chân ESP32 #1 | Ghi chú |
| :--- | :--- | :--- | :--- |
| **BH1750 (I2C)** | `VCC` | `3V3` | Nguồn 3.3V (không cắm 5V) |
| **BH1750 (I2C)** | `GND` | `GND` | Chung mass |
| **BH1750 (I2C)** | `SDA` | `GPIO 21` | Dữ liệu I2C mặc định ESP32 |
| **BH1750 (I2C)** | `SCL` | `GPIO 22` | Xung nhịp I2C mặc định ESP32 |
| **BH1750 (I2C)** | `ADDR` | `GND` (hoặc bỏ trống) | Địa chỉ I2C `0x23` |
| **LED 1** | Cực dương (Anode, chân dài) | `GPIO 18` | Nối nối tiếp qua điện trở `220Ω` |
| **LED 1** | Cực âm (Cathode, chân ngắn) | `GND` | Về mass chung |
| **LED 2** | Cực dương (Anode, chân dài) | `GPIO 19` | Nối nối tiếp qua điện trở `220Ω` |
| **LED 2** | Cực âm (Cathode, chân ngắn) | `GND` | Về mass chung |

## 3. Sơ đồ đấu nối ESP32 #2 (`ESP32-Node2-Temp-Humid`)

Thiết bị đảm nhiệm đọc nhiệt độ và độ ẩm (`DHT22` hoặc `DHT11`).

| Linh kiện | Chân linh kiện | Chân ESP32 #2 | Ghi chú |
| :--- | :--- | :--- | :--- |
| **DHT22 / DHT11** | `VCC` (`+`) | `3V3` | Nguồn 3.3V |
| **DHT22 / DHT11** | `DATA` (`OUT`) | `GPIO 4` | Nếu dùng cảm biến 4 chân rời, mắc điện trở kéo lên `10kΩ` giữa `DATA` và `3V3` |
| **DHT22 / DHT11** | `GND` (`-`) | `GND` | Chung mass |

## 4. Lưu ý trước khi nạp Firmware

1. Đảm bảo Laptop chạy Docker ThingsBoard và 2 mạch ESP32 **kết nối chung mạng Wi-Fi 2.4GHz** (ESP32 không hỗ trợ Wi-Fi 5GHz).
2. Mở Firewall Windows cho cổng `1883` (MQTT) hoặc đặt mạng Wi-Fi ở chế độ **Private Network** để ESP32 kết nối được vào Broker trên Laptop.
3. Trong code `.ino`, điền đúng `WIFI_SSID`, `WIFI_PASSWORD` và địa chỉ IP LAN của Laptop vào `TB_SERVER_IP`.
