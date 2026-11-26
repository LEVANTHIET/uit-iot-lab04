"""Xử lý bảng Logs 5 trường, lọc dữ liệu và xuất CSV/Excel chuẩn UTF-8."""

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import io
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font


LOG_HEADERS_VI: tuple[str, ...] = (
    "ID thiết bị",
    "Tên thiết bị",
    "Tên giá trị",
    "Giá trị cảm biến",
    "Thời gian nhận dữ liệu",
)


@dataclass(frozen=True)
class SystemLogRecord:
    """Bản ghi nhật ký chuẩn gồm 5 trường bắt buộc của Lab 04."""

    device_id: str
    device_name: str
    sensor_key: str
    sensor_value: str
    received_at: str
    timestamp_ms: int

    def as_row(self) -> list[str]:
        """Trả về danh sách 5 cột phục vụ hiển thị bảng và xuất tệp."""
        return [
            self.device_id,
            self.device_name,
            self.sensor_key,
            self.sensor_value,
            self.received_at,
        ]


def format_timestamp_ms(ts_ms: int) -> str:
    """Định dạng mốc thời gian mili-giây sang chuỗi UTC+7 dễ đọc."""
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _extract_point(point: Any) -> tuple[int, str]:
    """Tách cặp (timestamp_ms, value_str) từ cấu trúc REST hoặc WebSocket."""
    if isinstance(point, dict):
        return int(point["ts"]), str(point["value"])
    if isinstance(point, (list, tuple)) and len(point) >= 2:
        return int(point[0]), str(point[1])
    raise ValueError(f"Định dạng điểm dữ liệu timeseries không hợp lệ: {point!r}")


def flatten_tb_timeseries(
    device_id: str,
    device_name: str,
    timeseries_map: dict[str, list[Any]],
) -> list[SystemLogRecord]:
    """Chuyển dữ liệu chuỗi thời gian ThingsBoard thành danh sách bản ghi 5 trường."""
    records: list[SystemLogRecord] = []
    for sensor_key, points in timeseries_map.items():
        for point in points:
            ts_ms, val_str = _extract_point(point)
            records.append(
                SystemLogRecord(
                    device_id=device_id,
                    device_name=device_name,
                    sensor_key=sensor_key,
                    sensor_value=val_str,
                    received_at=format_timestamp_ms(ts_ms),
                    timestamp_ms=ts_ms,
                )
            )
    records.sort(key=lambda item: (-item.timestamp_ms, item.device_name, item.sensor_key))
    return records


def _matches_record(
    record: SystemLogRecord,
    query_lower: str,
    sensor_key: str | None,
    start_ts_ms: int | None,
    end_ts_ms: int | None,
) -> bool:
    """Kiểm tra một bản ghi nhật ký có thỏa mãn mọi điều kiện lọc."""
    if query_lower:
        haystack = f"{record.device_id} {record.device_name}".lower()
        if query_lower not in haystack:
            return False
    if sensor_key and record.sensor_key != sensor_key:
        return False
    if start_ts_ms is not None and record.timestamp_ms < start_ts_ms:
        return False
    if end_ts_ms is not None and record.timestamp_ms > end_ts_ms:
        return False
    return True


def filter_log_records(
    records: list[SystemLogRecord],
    device_query: str | None = None,
    sensor_key: str | None = None,
    start_ts_ms: int | None = None,
    end_ts_ms: int | None = None,
) -> list[SystemLogRecord]:
    """Lọc danh sách nhật ký theo thiết bị, tên giá trị hoặc khoảng thời gian."""
    query_lower = device_query.strip().lower() if device_query else ""
    return [
        item
        for item in records
        if _matches_record(item, query_lower, sensor_key, start_ts_ms, end_ts_ms)
    ]


def export_logs_to_csv_bytes(records: list[SystemLogRecord]) -> bytes:
    """Xuất danh sách bản ghi nhật ký ra byte CSV chuẩn UTF-8 kèm BOM."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(LOG_HEADERS_VI)
    for item in records:
        writer.writerow(item.as_row())
    return buffer.getvalue().encode("utf-8-sig")


def export_logs_to_xlsx_bytes(records: list[SystemLogRecord]) -> bytes:
    """Xuất danh sách bản ghi nhật ký ra tệp Excel (.xlsx) với tiêu đề định dạng rõ."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "IoT_System_Logs"
    sheet.append(list(LOG_HEADERS_VI))
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for item in records:
        sheet.append(item.as_row())
    widths = (38, 28, 18, 18, 22)
    for idx, width in enumerate(widths, start=1):
        col_letter = chr(64 + idx)
        sheet.column_dimensions[col_letter].width = width
    out = io.BytesIO()
    workbook.save(out)
    return out.getvalue()
