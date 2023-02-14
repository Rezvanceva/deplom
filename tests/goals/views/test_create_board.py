from typing import Any

import pytest
from apiclient import APIClient
from django.urls import reverse
from factory import Faker
from rest_framework import status

from tests.utils import BaseTestCase
from todolist.goals.models import Board, BoardParticipant


@pytest.mark.django_db()
class TestCreateBoardView(BaseTestCase):
    url = reverse('goals:create-board')

    def test_auth_required(self, client: APIClient, faker: Faker) -> None:
        response = client.post(self.url, data=faker.pydict(1))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_failed_to_create_deleted_board(self, auth_client: APIClient, faker: Faker) -> None:
        response = auth_client.post(self.url, data={
            'title': faker.sentence(),
            'is_deleted': True
        })
        assert response.status_code == status.HTTP_201_CREATED
        new_board = Board.objects.last()
        assert not new_board.is_deleted

    def test_creates_board_participant(self, auth_client: APIClient, user: Any, faker: Faker) -> None:
        response = auth_client.post(self.url, data={
            'title': faker.sentence(),
        })
        assert response.status_code == status.HTTP_201_CREATED
        new_board = Board.objects.last()
        participants = new_board.participants.all()
        assert len(participants) == 1
        assert participants[0].user == user
        assert participants[0].role == BoardParticipant.Role.owner

    def test_success(self, auth_client: APIClient) -> None:
        response = auth_client.post(self.url, data={
            'title': 'Board Title',
        })
        assert response.status_code == status.HTTP_201_CREATED
        new_board = Board.objects.last()
        assert response.json() == {
            'id': new_board.id,
            'created': self.datetime_to_str(new_board.created),
            'updated': self.datetime_to_str(new_board.updated),
            'title': 'Board Title',
            'is_deleted': False
        }