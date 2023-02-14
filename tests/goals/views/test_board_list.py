from typing import Any

import pytest
from apiclient import APIClient
from django.urls import reverse
from faker import factory
from rest_framework import status

from tests.utils import BaseTestCase
from todolist.goals.serializers import BoardSerializer


@pytest.mark.django_db()
class TestBoardListView(BaseTestCase):
    url = reverse('goals:board-list')

    def test_auth_required(self, client: APIClient) -> None:
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_not_board_participant(self, auth_client: APIClient, board: BoardSerializer, user: Any,
                                        board_factory: factory) -> None:
        assert not board.participants.count()
        another_board = board_factory.create(with_owner=user)
        assert another_board.participants.count() == 1

        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'id': another_board.id,
                'created': self.datetime_to_str(another_board.created),
                'updated': self.datetime_to_str(another_board.updated),
                'title': another_board.title,
                'is_deleted': False
            }
        ]

    def test_sort_boards_by_title(self, auth_client: APIClient, board_factory: factory, user: Any) -> None:
        for title in ['t2', 't1', 't4', 't3']:
            board_factory.create(title=title, with_owner=user)

        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert [board['title'] for board in response.json()] == ['t1', 't2', 't3', 't4']

    def test_board_pagination(self, auth_client: APIClient, board_factory: factory, user: Any) -> None:
        board_factory.create_batch(size=10, with_owner=user)

        limit_response = auth_client.get(self.url, {'limit': 3})
        assert limit_response.status_code == status.HTTP_200_OK
        assert limit_response.json()['count'] == 10
        assert len(limit_response.json()['results']) == 3

        offset_response = auth_client.get(self.url, {'limit': 100, 'offset': 8})
        assert offset_response.status_code == status.HTTP_200_OK
        assert offset_response.json()['count'] == 10
        assert len(offset_response.json()['results']) == 2
