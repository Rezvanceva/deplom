from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from todolist.goals.filters import GoalDateFilter
from todolist.goals.models import Goal, GoalCategory, GoalComment, BoardParticipant, Board
from todolist.goals.permissions import IsOwnerOrReadOnly, BoardPermissions, GoalCategoryPermissions, GoalPermissions, \
    CommentsPermissions
from todolist.goals.serializers import (
    GoalCategoryCreateSerializer, GoalCategorySerializer, GoalCommentCreateSerializer, GoalCommentSerializer,
    GoalCreateSerializer, GoalSerializer, BoardCreateSerializer, BoardListSerializer, BoardSerializer,
)


class BoardCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardCreateSerializer

    def perform_create(self, serializer):
        """ Делаем текущего пользователя владельцем доски. """
        BoardParticipant.objects.create(user=self.request.user, board=serializer.save())


class BoardListView(generics.ListAPIView):
    model = Board
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']

    def get_queryset(self):
        return Board.objects.prefetch_related('participants').filter(
            participants__user_id=self.request.user.id,
            is_deleted=False
        )


class BoardView(generics.RetrieveUpdateDestroyAPIView):
    model = Board
    permission_classes = [BoardPermissions]
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.filter(is_deleted=False)

    def perform_destroy(self, instance: Board):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(status=Goal.Status.archived)
        return instance

class GoalCategoryCreateView(generics.CreateAPIView):
    permission_classes = [GoalCategoryPermissions]
    serializer_class = GoalCategoryCreateSerializer


class GoalCategoryListView(generics.ListAPIView):
    model = GoalCategory
    permission_classes = [GoalCategoryPermissions]
    serializer_class = GoalCategorySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['board']
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title']

    def get_queryset(self):
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )


class GoalCategoryView(generics.RetrieveUpdateDestroyAPIView):
    model = GoalCategory
    serializer_class = GoalCategorySerializer
    permission_classes = [GoalCategoryPermissions, IsOwnerOrReadOnly]

    def get_queryset(self):
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance: GoalCategory):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            instance.goals.update(status=Goal.Status.archived)
        return instance


class GoalCreateView(generics.CreateAPIView):
    serializer_class = GoalCreateSerializer
    permission_classes = [GoalPermissions]


class GoalListView(generics.ListAPIView):
    model = Goal
    permission_classes = [GoalPermissions]
    serializer_class = GoalSerializer
    filterset_class = GoalDateFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Goal.objects.filter(
            Q(category__board__participants__user_id=self.request.user.id) & ~Q(status=Goal.Status.archived) & Q(
                category__is_deleted=False)
        )


class GoalView(generics.RetrieveUpdateAPIView):
    model = Goal
    permission_classes = [GoalPermissions, IsOwnerOrReadOnly]
    serializer_class = GoalSerializer

    def get_queryset(self):
        return Goal.objects.filter(~Q(status=Goal.Status.archived) & Q(category__is_deleted=False))


class GoalCommentCreateView(generics.CreateAPIView):
    serializer_class = GoalCommentCreateSerializer
    permission_classes = [CommentsPermissions]


class GoalCommentListView(generics.ListAPIView):
    model = GoalComment
    permission_classes = [CommentsPermissions]
    serializer_class = GoalCommentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['goal']
    ordering = ['-created']

    def get_queryset(self):
        return GoalComment.objects.filter(
            goal__category__board__participants__user_id=self.request.user.id,
        )


class GoalCommentView(generics.RetrieveUpdateDestroyAPIView):
    model = GoalComment
    permission_classes = [CommentsPermissions, IsOwnerOrReadOnly]
    serializer_class = GoalCommentSerializer

    def get_queryset(self):
        return GoalComment.objects.filter(user_id=self.request.user.id)
