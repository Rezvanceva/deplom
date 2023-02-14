from typing import Any

import pytest
from apiclient import APIClient
from django.urls import reverse
from factory import Faker, build
from faker import factory
from objects import objects
from rest_framework import status

from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestLoginView(BaseTestCase):
    url = reverse('core:login')

    def test_user_not_found(self, client: APIClient, user_factory: {factory}) -> None:
        user = user_factory.build()
        response = client.post(self.url, data={
            'username': user.username,
            'password': user.password,
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_credentials(self, client: APIClient, user: {factory}, faker: Faker) -> None:
        response = client.post(self.url, data={
            'username': user.username,
            'password': faker.password(),
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(('is_active', 'status_code'), [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_403_FORBIDDEN),
    ], ids=['active', 'inactive'])
    def test_inactive_user_login_denied(self, client: APIClient, user_factory: {factory}, faker: Faker, is_active: bool,
                                        status_code: int) -> None:
        password = faker.password()
        user = user_factory.create(password=password, is_active=is_active)
        response = client.post(self.url, data={
            'username': user.username,
            'password': password,
        })
        assert response.status_code == status_code

    def test_success(self, client: APIClient, faker: Faker, user_factory: {factory}) -> None:
        password = faker.password()
        user = user_factory.create(password=password)
        response = client.post(self.url, data={
            'username': user.username,
            'password': password,
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }
