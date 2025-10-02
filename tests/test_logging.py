import json

import pytest

from Urban_Amenities2.logging_utils import configure_logging, get_logger, request_context


def test_configure_logging_sanitises_sensitive_fields(tmp_path) -> None:
    log_file = tmp_path / "logs" / "aucs.log"
    configure_logging(level="INFO", log_file=log_file)
    logger = get_logger("test")
    with request_context("req-123"):
        logger.info(
            "example",
            api_key="super-secret",
            latitude=39.7392358,
            coords=[(1.23456, 2.34567)],
            user_id="tester",
        )
    record = json.loads(log_file.read_text().splitlines()[-1])
    assert record["api_key"] == "***"
    assert pytest.approx(record["latitude"], rel=0, abs=1e-3) == 39.739
    assert pytest.approx(record["coords"][0][0], rel=0, abs=1e-3) == 1.235
    assert record["user_id"] != "tester"
    assert record["request_id"] == "req-123"
