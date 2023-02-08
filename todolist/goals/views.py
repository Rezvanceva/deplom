from django.db import transaction
from django.db.models import Q
from django_filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView

from todolist.goals.filters import GoalDateFilter
from todolist.goals.models import Goal, GoalCategory, GoalComment, Board
from todolist.goals.permissions import IsOwnerOrReadOnly, BoardPermission, GoalCategoryPermission, GoalPermission, CommentPermission
from todolist.goals.serializers import (
    GoalCategoryCreateSerializer, GoalCategorySerializer, GoalCommentCreateSerializer, GoalCommentSerializer,
    GoalCreateSerializer, GoalSerializer, BoardCreateSerializer, BoardListSerializer, BoardSerializer,
)


class BoardCreateView(CreateAPIView):
    """Ручка для создания доски"""
    permission_classes = [BoardPermission]
    serializer_class = BoardCreateSerializer


class BoardListView(ListAPIView):
    """Ручка для отображения списка досок"""
    model = Board
    permission_classes = [BoardPermission]
    serializer_class = BoardListSerializer
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title']

    def get_queryset(self):
        """Метод возвращает из базы queryset список досок"""
        return Board.objects.prefetch_related('participants').filter(
            participants__user__id=self.request.user.id, is_deleted=False
        )


class BoardView(RetrieveUpdateDestroyAPIView):
    """Ручка для отображения, редактирования и удаления доски"""
    model = Board
    permission_classes = [BoardPermission]
    serializer_class = BoardSerializer

    def get_queryset(self):
        """Метод возвращает из базы queryset доски"""
        return Board.objects.prefetch_related('participants').filter(
            participants__user__id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance):
        """
        Метод удаляет доску
        При удалении доски помечаем ее как is_deleted,
        "удаляем" категории, обновляем статус целей.
        """
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=['is_deleted'])
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(status=Goal.Status.archived)
        return instance


class GoalCategoryCreateView(CreateAPIView):
    """Ручка для создания категории"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategoryCreateSerializer


class GoalCategoryListView(ListAPIView):
    """Ручка для отображения списка категорий"""
    model = GoalCategory
    permission_classes = [GoalCategoryPermission]
    serializer_class = GoalCategorySerializer
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    filterset_fields = ['board']
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title']

    def get_queryset(self):
        """Метод возвращает из базы queryset списка категорий"""
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id, is_deleted=False
        )


class GoalCategoryView(RetrieveUpdateDestroyAPIView):
    """Ручка для отображения, редактирования и удаления категории"""
    model = GoalCategory
    serializer_class = GoalCategorySerializer
    permission_classes = [GoalCategoryPermission, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Метод возвращает из базы queryset категории"""
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id, is_deleted=False
        )

    def perform_destroy(self, instance: GoalCategory):
        """Метод удаляет категорию, а у всех целей в этой категории меняет статус на архивный"""
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            Goal.objects.filter(category=instance).update(status=Goal.Status.archived)
        return instance


class GoalCreateView(CreateAPIView):
    """Ручка для создания цели"""
    permission_classes = [GoalPermission]
    serializer_class = GoalCreateSerializer


class GoalListView(ListAPIView):
    """Ручка для отображения списка целей"""
    model = Goal
    permission_classes = [GoalPermission]
    serializer_class = GoalSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = GoalDateFilter
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title', 'description']

    def get_queryset(self):
        """Метод возвращает из базы queryset списка целей"""
        return Goal.objects.select_related('user', 'category__board').filter(
            Q(category__board__participants__user_id=self.request.user.id) & ~Q(status=Goal.Status.archived)
        )


class GoalView(RetrieveUpdateDestroyAPIView):
    """Ручка для отображения, редактирования и удаления цели"""
    model = Goal
    serializer_class = GoalSerializer
    permission_classes = [GoalPermission, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Метод возвращает из базы queryset цели"""
        return Goal.objects.select_related('user', 'category__board').filter(
            Q(category__board__participants__user_id=self.request.user.id) & ~Q(status=Goal.Status.archived)
        )

    def perform_destroy(self, instance: Goal):
        """Метод меняет статус цели как архивный"""
        instance.status = Goal.Status.archived
        instance.save(update_fields=('status',))
        return instance


class GoalCommentCreateView(CreateAPIView):
    """Ручка для создания комментария"""
    permission_classes = [CommentPermission]
    serializer_class = GoalCommentCreateSerializer


class GoalCommentListView(ListAPIView):
    """Ручка для отображения списка комментариев"""
    model = GoalComment
    permission_classes = [CommentPermission]
    serializer_class = GoalCommentSerializer
    filter_backends = [OrderingFilter]
    filterset_fields = ['goal']
    ordering = ['-created']

    def get_queryset(self):
        """Метод возвращает из базы queryset списка комментариев"""
        return GoalComment.objects.select_related('goal__category__board', 'user').filter(
            goal__category__board__participants__user_id=self.request.user.id
        )


class GoalCommentView(RetrieveUpdateDestroyAPIView):
    """Ручка для отображения, редактирования и удаления комментария"""
    model = GoalComment
    permission_classes = [CommentPermission, IsOwnerOrReadOnly]
    serializer_class = GoalCommentSerializer

    def get_queryset(self):
        """Метод возвращает из базы queryset комментарии"""
        return GoalComment.objects.select_related('goal__category__board', 'user').filter(
            goal__category__board__participants__user_id=self.request.user.id
        )
