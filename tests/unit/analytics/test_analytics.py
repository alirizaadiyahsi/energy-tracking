import pytest
from services.analytics.core import analytics_utils

@pytest.mark.unit
def test_basic_statistical_summary():
    data = [1, 2, 3, 4, 5]
    summary = analytics_utils.basic_summary(data)
    assert summary['mean'] == 3
    assert summary['min'] == 1
    assert summary['max'] == 5
