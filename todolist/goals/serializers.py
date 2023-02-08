from typing import Type

from django.db import transaction
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError, PermissionDenied

from todolist.core.models import User
from todolist.core.serializers import ProfileSerializer
from todolist.goals.models import Goal, GoalCategory, GoalComment, Board, BoardParticipant


class BoardCreateSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора для создания новой доски"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = Board
        read_only_fields = ('id', 'created', 'updated', 'is_deleted')
        fields = '__all__'

    def create(self, validated_data):
        """Метод для валидации данных и создания доски"""
        user = validated_data.pop('user')
        board = Board.objects.create(**validated_data)
        BoardParticipant.objects.create(user=user, board=board, role=BoardParticipant.Role.owner)
        return board


class BoardParticipantSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора участников доски"""
    role = serializers.ChoiceField(required=True, choices=BoardParticipant.Role.choices[1:])
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = BoardParticipant
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'board')


class BoardSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора доски"""
    participants = BoardParticipantSerializer(many=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = Board
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated')

    def update(self, instance, validated_data):
        """Метод для редактирования и добавления участников доски"""
        owner = validated_data.pop('user')
        new_participants = validated_data.pop('participants')
        new_by_id = {part['user'].id: part for part in new_participants}

        old_participants = instance.participants.exclude(user=owner)
        with transaction.atomic():
            for old_participant in old_participants:
                if old_participant.user_id not in new_by_id:
                    old_participant.delete()
                else:
                    if old_participant.role != new_by_id[old_participant.user_id]['role']:
                        old_participant.role = new_by_id[old_participant.user_id]['role']
                        old_participant.save()
                    new_by_id.pop(old_participant.user_id)
            for new_part in new_by_id.values():
                BoardParticipant.objects.create(board=instance, user=new_part['user'], role=new_part['role'])

            if title := validated_data.get('title'):
                instance.title = title
                instance.save()

        return instance


class BoardListSerializer(serializers.ModelSerializer):
    """Класс модели для сериализации списка досок"""

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = Board
        fields = '__all__'


class GoalCategoryCreateSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора для создания категории целей"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = GoalCategory
        read_only_fields = ('id', 'created', 'updated', 'user', 'is_deleted')
        fields = '__all__'


class GoalCategorySerializer(serializers.ModelSerializer):
    """Класс модели сериализатора категории целей"""
    user = ProfileSerializer(read_only=True)

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = GoalCategory
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user', 'board')

    def validated_board(self, value: Board):
        """
        Метод для валидации данных доски. Метод проверяет не удалена ли доска
        и является ли пользователь участником с ролью owner или writer
        """
        if value.is_deleted:
            raise serializers.ValidationError('Not allowed to delete category')
        if not BoardParticipant.objects.filter(
                board=value,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                user_id=self.context['request'].user.id
        ).exists():
            raise serializers.ValidationError('You must be owner or writer')
        return value


class GoalCreateSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора для создания цели"""
    category = serializers.PrimaryKeyRelatedField(queryset=GoalCategory.objects.filter(is_deleted=False))
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = Goal
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validated_category(self, value: GoalCategory):
        """
        Метод для валидации данных категории целей. Метод проверяет, является ли
        пользователь создателем категории, или является ли он участником доски с этой
        категорией в роли writer
        """
        if not BoardParticipant.objects.filter(
                board_is=value.board_id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                user_id=self.context['request'].user.id,
        ).exists():
            raise exceptions.PermissionDenied
        return value


class GoalSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора цели"""
    category = serializers.PrimaryKeyRelatedField(queryset=GoalCategory.objects.filter(is_deleted=False))

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = Goal
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validated_category(self, value: Type[GoalCategory]):
        """
        Метод для валидации данных категории целей.
        Метод проверяет, является ли пользователь создателем категории целей
        """
        if self.context['request'].user != value.user:
            raise PermissionDenied
        return value


class GoalCommentCreateSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора для создания комментария"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = GoalComment
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validate_goal(self, value: Goal):
        if not BoardParticipant.objects.filter(
                board=value.category.board_id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                user_id=self.context['request'].user.id
        ):
            raise PermissionDenied
        return value


class GoalCommentSerializer(serializers.ModelSerializer):
    """Класс модели сериализатора комментария"""
    user = ProfileSerializer(read_only=True)

    class Meta:
        """Мета-класс для указания модели для сериализатора, полей модели сериализатора, и не изменяемых полей"""
        model = GoalComment
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user', 'goal')