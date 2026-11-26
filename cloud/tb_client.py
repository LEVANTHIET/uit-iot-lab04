"""Client giao tiếp REST API của ThingsBoard CE."""

from typing import Any

import requests


class ThingsBoardClient:
    """Quản lý xác thực JWT, thiết bị, widget và dashboard trên ThingsBoard."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        session: requests.Session | None = None,
        timeout: int = 15,
    ) -> None:
        """Khởi tạo client kết nối tới máy chủ ThingsBoard cục bộ."""
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.token: str | None = None

    def _headers(self) -> dict[str, str]:
        """Tạo header xác thực Bearer JWT nếu đã đăng nhập."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Gửi HTTP request chuẩn hóa tới REST API ThingsBoard."""
        url = f"{self.base_url}{path}"
        resp = self.session.request(
            method,
            url,
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def login(self, username: str, password: str) -> str:
        """Đăng nhập tài khoản Tenant để lấy JWT token."""
        data = self._request(
            "POST",
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        self.token = str(data["token"])
        return self.token

    def get_device_by_name(self, name: str) -> dict[str, Any] | None:
        """Tìm thiết bị theo tên duy nhất của Tenant."""
        url = f"{self.base_url}/api/tenant/devices"
        resp = self.session.get(
            url,
            headers=self._headers(),
            params={"deviceName": name},
            timeout=self.timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def ensure_device(
        self,
        name: str,
        label: str,
        access_token: str,
        device_type: str = "default",
    ) -> dict[str, Any]:
        """Tạo mới hoặc cập nhật thiết bị kèm Access Token cố định."""
        device = self.get_device_by_name(name)
        if device is None:
            device = self._request(
                "POST",
                "/api/device",
                json={"name": name, "type": device_type, "label": label},
            )
        device_id = device["id"]["id"]
        creds = self._request("GET", f"/api/device/{device_id}/credentials")
        if creds.get("credentialsId") != access_token:
            creds["credentialsType"] = "ACCESS_TOKEN"
            creds["credentialsId"] = access_token
            self._request("POST", "/api/device/credentials", json=creds)
        return device

    def list_widget_types(self) -> list[dict[str, Any]]:
        """Lấy danh sách widgetTypesInfos để đối chiếu đúng tên FQN."""
        data = self._request("GET", "/api/widgetTypesInfos?pageSize=200&page=0")
        return list(data.get("data", [])) if isinstance(data, dict) else []

    def ensure_widgets_bundle(self, bundle_payload: dict[str, Any]) -> dict[str, Any]:
        """Tạo mới hoặc lấy lại Widgets Bundle theo alias."""
        alias = bundle_payload["alias"]
        existing = self._request("GET", "/api/widgetsBundles") or []
        for item in existing:
            if item.get("alias") == alias:
                return item
        return self._request("POST", "/api/widgetsBundle", json=bundle_payload)

    def ensure_widget_type(self, widget_payload: dict[str, Any]) -> dict[str, Any]:
        """Đăng ký mới hoặc cập nhật Custom Widget Type qua FQN."""
        fqn = widget_payload["fqn"]
        url = f"{self.base_url}/api/widgetType"
        resp = self.session.get(
            url,
            headers=self._headers(),
            params={"fqn": fqn},
            timeout=self.timeout,
        )
        payload = dict(widget_payload)
        if resp.status_code == 200 and resp.content:
            existing = resp.json()
            payload["id"] = existing["id"]
        return self._request("POST", "/api/widgetType", json=payload)

    def ensure_dashboard(self, dashboard_payload: dict[str, Any]) -> dict[str, Any]:
        """Tạo mới hoặc ghi đè Dashboard ThingsBoard theo tiêu đề."""
        title = dashboard_payload["title"]
        page = self._request(
            "GET",
            "/api/tenant/dashboards",
            params={"pageSize": 50, "page": 0, "textSearch": title},
        )
        payload = dict(dashboard_payload)
        for item in page.get("data", []):
            if item.get("title") == title:
                payload["id"] = item["id"]
                break
        return self._request("POST", "/api/dashboard", json=payload)

    def fetch_timeseries(
        self,
        device_id: str,
        keys: list[str],
        start_ts_ms: int,
        end_ts_ms: int,
        limit: int = 5000,
    ) -> dict[str, list[dict[str, Any]]]:
        """Truy vấn dữ liệu lịch sử telemetry của một thiết bị từ ThingsBoard."""
        params = {
            "keys": ",".join(keys),
            "startTs": start_ts_ms,
            "endTs": end_ts_ms,
            "limit": limit,
            "agg": "NONE",
        }
        data = self._request(
            "GET",
            f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
            params=params,
        )
        return data or {}
