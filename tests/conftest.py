import pytest

from src.core.metrics import reset_metrics
from src.core.rate_limiter import reset_rate_limiter


@pytest.fixture(autouse=True)
def reset_observability_state():
    reset_metrics()
    reset_rate_limiter()
    yield
    reset_metrics()
    reset_rate_limiter()
