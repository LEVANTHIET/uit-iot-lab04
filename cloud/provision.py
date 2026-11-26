"""Script tự động khởi tạo thiết bị, Custom Widget và Dashboard trên ThingsBoard."""

import argparse
import json
from pathlib import Path
import time

import requests

from cloud.tb_client import ThingsBoardClient
from common.constants import NODE1_SPEC, NODE2_SPEC
from dashboard.builder import (
    build_custom_widget_payload,
    build_dashboard_payload,
    build_widget_bundle_payload,
    resolve_widget_fqns,
)


def wait_for_thingsboard(base_url: str, timeout_sec: int = 300) -> None:
    """Chờ API ThingsBoard phản hồi JSON hợp lệ trước khi nạp cấu hình."""
    deadline = time.monotonic() + timeout_sec
    url = f"{base_url.rstrip('/')}/api/noauth/userPasswordPolicy"
    while time.monotonic() < deadline:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                resp.json()
                return
        except (requests.RequestException, ValueError):
            pass
        time.sleep(3)
    raise TimeoutError(f"ThingsBoard không sẵn sàng sau {timeout_sec} giây tại {base_url}")


def provision_all(
    client: ThingsBoardClient,
    username: str,
    password: str,
    save_dir: Path | None = None,
) -> tuple[str, str, str]:
    """Thực thi nạp trọn bộ 2 ESP32, Custom Widget và Dashboard lên ThingsBoard."""
    client.login(username, password)
    dev1 = client.ensure_device(NODE1_SPEC.name, NODE1_SPEC.label, NODE1_SPEC.access_token)
    dev2 = client.ensure_device(NODE2_SPEC.name, NODE2_SPEC.label, NODE2_SPEC.access_token)
    node1_id = str(dev1["id"]["id"])
    node2_id = str(dev2["id"]["id"])

    bundle_payload = build_widget_bundle_payload()
    widget_payload = build_custom_widget_payload()
    client.ensure_widgets_bundle(bundle_payload)
    saved_widget = client.ensure_widget_type(widget_payload)

    widget_infos = client.list_widget_types()
    fqns = resolve_widget_fqns(widget_infos)
    if saved_widget and saved_widget.get("fqn"):
        fqns["logs_custom"] = str(saved_widget["fqn"])
    dash_payload = build_dashboard_payload(node1_id, node2_id, widget_fqns=fqns)
    saved_dash = client.ensure_dashboard(dash_payload)

    target_dir = save_dir or (Path(__file__).resolve().parents[1] / "dashboard")
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "thingsboard_dashboard.json").write_text(
        json.dumps(dash_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return node1_id, node2_id, str(saved_dash["id"]["id"])


def main() -> None:
    """Điểm vào dòng lệnh tự động cấu hình ThingsBoard cho Lab 04."""
    parser = argparse.ArgumentParser(description="Khởi tạo tự động ThingsBoard Lab 04")
    parser.add_argument("--url", default="http://localhost:9090")
    parser.add_argument("--user", default="tenant@thingsboard.org")
    parser.add_argument("--password", default="tenant")
    parser.add_argument("--wait", type=int, default=300)
    args = parser.parse_args()

    wait_for_thingsboard(args.url, timeout_sec=args.wait)
    client = ThingsBoardClient(base_url=args.url)
    node1_id, node2_id, dash_id = provision_all(client, args.user, args.password)
    print(f"Đã tạo thiết bị Node1={node1_id}, Node2={node2_id}, Dashboard={dash_id}")


if __name__ == "__main__":
    main()
