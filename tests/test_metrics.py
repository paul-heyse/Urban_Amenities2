from Urban_Amenities2.monitoring.metrics import METRICS, MetricsCollector, track_operation


def test_metrics_collector_summary() -> None:
    collector = MetricsCollector()
    collector.record_timing("ingest", 1.0, count=100)
    collector.record_timing("ingest", 2.0, count=200)
    summary = collector.timing_summary("ingest")
    assert summary is not None
    assert summary.count == 2
    assert summary.total_duration == 3.0
    assert summary.throughput is not None
    assert summary.throughput > 50


def test_metrics_collector_service_summary() -> None:
    collector = MetricsCollector()
    collector.record_service_call("osrm", 0.4, success=True)
    collector.record_service_call("osrm", 0.6, success=False)
    summary = collector.service_summary("osrm")
    assert summary is not None
    assert summary["success"] == 1
    assert summary["failure"] == 1
    assert "p95" in summary


def test_track_operation_records_metrics() -> None:
    METRICS.clear()
    with track_operation("test-stage", metrics=METRICS, logger=None, items=5):
        pass
    summary = METRICS.timing_summary("test-stage")
    assert summary is not None
    assert summary.count == 1
    assert summary.throughput is None or summary.throughput >= 0
