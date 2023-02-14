from typing import Any

import factory
from django.utils import timezone
from pytest_factoryboy import register

from todolist.goals.models import BoardParticipant


@register
class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    password = factory.Faker('password')
    email = ''

    class Meta:
        model = 'core.User'

    @classmethod
    def _create(cls, model_class: type, *args: tuple, **kwargs: dict) -> Any:
        return cls._get_manager(model_class).create_user(*args, **kwargs)


class DatesFactoryMixin(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True

    created = factory.LazyFunction(timezone.now)
    updated = factory.LazyFunction(timezone.now)


@register
class BoardFactory(DatesFactoryMixin):
    title = factory.Faker('sentence')

    class Meta:
        model = 'goals.Board'

    @factory.post_generation
    def with_owner(self, create: Any, owner: Any, **kwargs: Any) -> Any:
        if owner:
            BoardParticipant.objects.create(board=self, user=owner, role=BoardParticipant.Role.owner)


@register
class BoardParticipantFactory(DatesFactoryMixin):
    board = factory.SubFactory(BoardFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = 'goals.BoardParticipant'


@register
class GoalCategoryFactory(DatesFactoryMixin):
    board = factory.SubFactory(BoardFactory)
    title = factory.Faker('sentence')
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = 'goals.GoalCategory'


@register
class GoalFactory(DatesFactoryMixin):
    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(GoalCategoryFactory)
    title = factory.Faker('sentence')

    class Meta:
        model = 'goals.Goal'


@register
class GoalCommentFactory(DatesFactoryMixin):
    user = factory.SubFactory(UserFactory)
    goal = factory.SubFactory(GoalFactory)
    text = factory.Faker('text')

    class Meta:
        model = 'goals.GoalComment'