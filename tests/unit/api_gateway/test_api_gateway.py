import pytest
from services.api_gateway.core import router

@pytest.mark.unit
def test_routes_exist():
    routes = [route.path for route in router.routes]
    assert '/auth/login' in routes
    assert '/auth/register' in routes
