import pytest
from objects import objects
from rest_framework.test import APIClient

pytest_plugins = 'tests.factories'


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


@pytest.fixture()
def auth_client(client: APIClient, user: {objects}) -> APIClient:
    client.force_login(user)
    return client