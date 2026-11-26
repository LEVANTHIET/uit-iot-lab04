"""Kiểm thử hạ tầng Docker và tài liệu nền móng của Lab 04."""

from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]


class TestInfraSetup(unittest.TestCase):
    """Kiểm tra cấu hình Docker ThingsBoard và tài liệu đấu nối."""

    def test_docker_compose_contains_required_ports_and_image(self) -> None:
        """Xác nhận docker-compose dùng tb-postgres và mở cổng 8080, 1883."""
        compose_path = ROOT_DIR / "docker" / "docker-compose.yml"
        self.assertTrue(compose_path.is_file())
        content = compose_path.read_text(encoding="utf-8")
        self.assertIn("thingsboard/tb-postgres", content)
        self.assertIn("8080:9090", content)
        self.assertIn("1883:1883", content)

    def test_docs_and_feature_map_exist(self) -> None:
        """Xác nhận bản đồ tính năng và sơ đồ phần cứng đầy đủ."""
        feature_map = (ROOT_DIR / "FEATURE_MAP.md").read_text(encoding="utf-8")
        wiring_doc = (ROOT_DIR / "docs" / "HARDWARE_WIRING.md").read_text(encoding="utf-8")
        self.assertIn("FLOW-06", feature_map)
        self.assertIn("BH1750", wiring_doc)
        self.assertIn("GPIO 18", wiring_doc)
        self.assertIn("GPIO 19", wiring_doc)
        self.assertIn("GPIO 4", wiring_doc)


if __name__ == "__main__":
    unittest.main()
