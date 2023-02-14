import pytest
from apiclient import APIClient
from django.urls import reverse
from faker import Faker, factory
from rest_framework import status

from tests.utils import BaseTestCase


@pytest.mark.django_db()
class TestUpdatePasswordView(BaseTestCase):
    url = reverse('core:update-password')

    def test_auth_required(self, client: APIClient) -> None:
        response = client.patch(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_old_password(self, auth_client: APIClient, faker: Faker) -> APIClient:
        response = auth_client.patch(self.url, data={
            'old_password': faker.password(),
            'new_password': faker.password(),
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
        assert response.json() == {'old_password': ['Password is incorrect']}

    def test_weak_new_password(self, client: APIClient, user_factory: factory, faker: Faker,
                               invalid_password: str) -> None:
        password = faker.password()
        user = user_factory.create(password=password)

        client.force_login(user)
        response = client.patch(self.url, data={
            'old_password': password,
            'new_password': invalid_password,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success(self, client: APIClient, faker: Faker, user_factory: factory) -> None:
        old_password = faker.password()
        user = user_factory.create(password=old_password)

        new_password = faker.password()
        client.force_login(user)
        response = client.patch(self.url, data={
            'old_password': old_password,
            'new_password': new_password,
        })
        assert response.status_code == status.HTTP_200_OK
        assert not response.json()
        user.refresh_from_db(fields=('password',))
        assert user.check_password(new_password)
