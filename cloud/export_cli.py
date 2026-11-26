"""Công cụ dòng lệnh tải nhật ký từ ThingsBoard API và xuất ra CSV/XLSX."""

import argparse
from pathlib import Path
import time

from cloud.tb_client import ThingsBoardClient
from common.constants import ALL_DEVICES
from core.logs_exporter import (
    SystemLogRecord,
    export_logs_to_csv_bytes,
    export_logs_to_xlsx_bytes,
    filter_log_records,
    flatten_tb_timeseries,
)


def collect_all_logs(
    client: ThingsBoardClient,
    start_ts_ms: int,
    end_ts_ms: int,
) -> list[SystemLogRecord]:
    """Thu thập toàn bộ nhật ký 5 trường của các thiết bị ESP32 từ ThingsBoard."""
    records: list[SystemLogRecord] = []
    for spec in ALL_DEVICES:
        device = client.get_device_by_name(spec.name)
        if device is None:
            continue
        dev_id = str(device["id"]["id"])
        ts_map = client.fetch_timeseries(dev_id, list(spec.telemetry_keys), start_ts_ms, end_ts_ms)
        records.extend(flatten_tb_timeseries(dev_id, spec.name, ts_map))
    records.sort(key=lambda item: (-item.timestamp_ms, item.device_name, item.sensor_key))
    return records


def export_logs_to_file(
    client: ThingsBoardClient,
    output_path: Path,
    fmt: str = "csv",
    device_query: str | None = None,
    sensor_key: str | None = None,
    hours_back: int = 24,
) -> int:
    """Truy vấn, lọc và lưu tệp nhật ký CSV hoặc Excel ra đĩa."""
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - hours_back * 3600 * 1000
    all_records = collect_all_logs(client, start_ms, end_ms)
    filtered = filter_log_records(all_records, device_query=device_query, sensor_key=sensor_key)
    payload = export_logs_to_xlsx_bytes(filtered) if fmt == "xlsx" else export_logs_to_csv_bytes(filtered)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    return len(filtered)


def main() -> None:
    """Điểm vào dòng lệnh xuất nhật ký IoT ra tệp CSV hoặc Excel."""
    parser = argparse.ArgumentParser(description="Xuất nhật ký telemetry từ ThingsBoard")
    parser.add_argument("--url", default="http://localhost:9090")
    parser.add_argument("--user", default="tenant@thingsboard.org")
    parser.add_argument("--password", default="tenant")
    parser.add_argument("--format", choices=["csv", "xlsx"], default="csv")
    parser.add_argument("--device", default=None)
    parser.add_argument("--key", default=None)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--out", default="exports/iot_logs.csv")
    args = parser.parse_args()

    client = ThingsBoardClient(base_url=args.url)
    client.login(args.user, args.password)
    count = export_logs_to_file(
        client,
        Path(args.out),
        fmt=args.format,
        device_query=args.device,
        sensor_key=args.key,
        hours_back=args.hours,
    )
    print(f"Đã xuất {count} bản ghi ra {args.out}")


if __name__ == "__main__":
    main()
