from typing import Any

from objects import objects
from rest_framework import permissions
from rest_framework.templatetags.rest_framework import data

from todolist.goals.models import Board, BoardParticipant, Goal, GoalCategory, GoalComment


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request: {data}, view: Any, obj: {objects}) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class BoardPermissions(permissions.IsAuthenticated):
    def has_object_permission(self, request: {data}, view: Any, obj: Board) -> Any:
        _filters: dict = {'user': request.user, 'board': obj}
        if request.method not in permissions.SAFE_METHODS:
            _filters['role'] = BoardParticipant.Role.owner

        return BoardParticipant.objects.filter(**_filters).exists()


class GoalCategoryPermissions(permissions.IsAuthenticated):
    def has_object_permission(self, request: {data}, view: Any, obj: GoalCategory) -> Any:
        _filters: dict = {'user_id': request.user.id, 'board_id': obj.board_id}
        if request.method not in permissions.SAFE_METHODS:
            _filters['role__in'] = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]

        return BoardParticipant.objects.filter(**_filters).exists()


class GoalPermissions(permissions.IsAuthenticated):
    def has_object_permission(self, request: {data}, view: Any, obj: Goal) -> Any:
        _filters: dict = {'user_id': request.user.id, 'board_id': obj.category.board_id}
        if request.method not in permissions.SAFE_METHODS:
            _filters['role__in'] = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]

        return BoardParticipant.objects.filter(**_filters).exists()


class CommentsPermissions(permissions.IsAuthenticated):
    def has_object_permission(self, request: {data}, view: Any, obj: GoalComment) -> bool:
        return any((
            request.method in permissions.SAFE_METHODS,
            obj.user.id == request.user.id
        ))