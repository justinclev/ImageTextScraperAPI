from collections import defaultdict
from threading import Lock
from typing import DefaultDict, Tuple

_REQUEST_TOTAL: DefaultDict[Tuple[str, str, int], int] = defaultdict(int)
_REQUEST_DURATION_SECONDS: DefaultDict[Tuple[str, str], float] = defaultdict(float)
_OCR_OUTCOME_TOTAL: DefaultDict[str, int] = defaultdict(int)
_LOCK = Lock()


def record_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    key = (method, path, status_code)
    duration_key = (method, path)

    with _LOCK:
        _REQUEST_TOTAL[key] += 1
        _REQUEST_DURATION_SECONDS[duration_key] += duration_seconds


def record_ocr_outcome(outcome: str) -> None:
    with _LOCK:
        _OCR_OUTCOME_TOTAL[outcome] += 1


def render_prometheus_metrics() -> str:
    lines = [
        "# HELP http_requests_total Total number of HTTP requests.",
        "# TYPE http_requests_total counter",
    ]

    with _LOCK:
        for (method, path, status_code), count in sorted(_REQUEST_TOTAL.items()):
            lines.append(
                "http_requests_total{"
                f'method="{method}",path="{path}",status="{status_code}"'
                f"}} {count}"
            )

        lines.extend(
            [
                "# HELP http_request_duration_seconds_sum Cumulative request duration in seconds.",
                "# TYPE http_request_duration_seconds_sum counter",
            ]
        )
        for (method, path), duration in sorted(_REQUEST_DURATION_SECONDS.items()):
            lines.append(
                "http_request_duration_seconds_sum{"
                f'method="{method}",path="{path}"'
                f"}} {duration:.6f}"
            )

        lines.extend(
            [
                "# HELP ocr_requests_total Total number of OCR request outcomes.",
                "# TYPE ocr_requests_total counter",
            ]
        )
        for outcome, count in sorted(_OCR_OUTCOME_TOTAL.items()):
            lines.append(f'ocr_requests_total{{outcome="{outcome}"}} {count}')

    return "\n".join(lines) + "\n"


def reset_metrics() -> None:
    with _LOCK:
        _REQUEST_TOTAL.clear()
        _REQUEST_DURATION_SECONDS.clear()
        _OCR_OUTCOME_TOTAL.clear()
