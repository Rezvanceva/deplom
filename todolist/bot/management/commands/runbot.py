import logging
import os
from datetime import datetime
from enum import Enum, auto
from typing import Any

from django.conf import settings
from django.core.management import BaseCommand
from pydantic import BaseModel

from todolist.bot.models import TgUser
from todolist.bot.tg.client import TgClient
from todolist.bot.tg.fsm.memory_storage import MemoryStorage

from todolist.bot.tg.dc import Message
from todolist.goals.models import Goal, GoalCategory, BoardParticipant

logger = logging.getLogger(__name__)


class StateEnum(Enum):
    """Класс для выбора состояния:
    - до выбора категории
    - после выбора категории"""
    CREATE_CATEGORY_SELECT = auto()
    CHOSEN_CATEGORY = auto()


class NewGoal(BaseModel):
    """Класс модели для создания новой цели"""
    category_id: int | None = None
    goal_title: str | None = None

    @property
    def is_completed(self) -> bool:
        """Метод проверяющий заполненность полей category_id и goal_title,
        для создания новой цели"""
        return None not in [self.category_id, self.goal_title]


class Command(BaseCommand):
    """Базовый класс для запуска и управления ботом"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.tg_client = TgClient(settings.BOT_TOKEN)
        self.storage = MemoryStorage()

    @staticmethod
    def _generate_verification_code() -> str:
        """Защищенный метод для генерации кода верификации"""
        return os.urandom(12).hex()

    def handle_unverified_user(self, msg: Message, tg_user: TgUser) -> None:
        """Ручка для работы с не идентифицированными пользователями: генерация кода верификации
        и отправка его пользователю"""
        code: str = self._generate_verification_code()
        tg_user.verification_code = code
        tg_user.save(update_fields=('verification_code',))
        self.tg_client.send_message(
            chat_id=msg.chat.id, text=f'[verification code] {tg_user.verification_code}')

    def handle_goals_list(self, msg: Message, tg_user: TgUser) -> None:
        """Ручка для получения и вывода списка целей"""
        resp_goals: list[str] = [
            f'№{goal.id} {goal.title}'
            for goal in Goal.objects.filter(user_id=tg_user.user_id,
                                            status__in=(1, 2, 3)
                                            ).order_by('created')
        ]
        if resp_goals:
            self.tg_client.send_message(msg.chat.id, '\n'.join(resp_goals))
        else:
            self.tg_client.send_message(msg.chat.id, '[You have no goals]')

    def handle_goal_categories_list(self, msg: Message, tg_user: TgUser) -> None:
        """Ручка для получения и вывода списка категорий целей"""
        resp_categories: list[str] = [
            f'#{category.id} {category.title}'
            for category in GoalCategory.objects.filter(
                board__participants__user_id=tg_user.user_id, is_deleted=False)
        ]
        if resp_categories:
            self.tg_client.send_message(msg.chat.id, 'Select category\n' + '\n'.join(resp_categories))
        else:
            self.tg_client.send_message(msg.chat.id, '[You have no categories]')

    def handle_save_selected_category(self, msg: Message, tg_user: TgUser)  -> None:
        """Ручка для выбора и валидации выбранной категорий для создания новой цели"""
        if msg.text.isdigit():
            category_id = int(msg.text)
            if GoalCategory.objects.filter(
                    board__participants__user_id=tg_user.user_id,
                    board__participants__role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                    is_deleted=False,
                    id=category_id
            ).exists():
                self.storage.update_data(chat_id=msg.chat.id, category_id=category_id)
                self.tg_client.send_message(msg.chat.id, '[set title]')
                self.storage.set_state(msg.chat.id, state=StateEnum.CHOSEN_CATEGORY)
            else:
                self.tg_client.send_message(msg.chat.id, '[category not found]')
        else:
            self.tg_client.send_message(msg.chat.id, '[Invalid category id]')

    def handle_save_new_category(self, msg: Message, tg_user: TgUser) -> None:
        """Ручка для создания новой цели"""
        goal = NewGoal(**self.storage.get_data(tg_user.chat_id))
        goal.goal_title = msg.text
        if goal.is_completed:
            Goal.objects.create(
                title=goal.goal_title,
                category_id=goal.category_id,
                user_id=tg_user.user_id,
                due_date=datetime.now()
            )
            self.tg_client.send_message(msg.chat.id, '[new goal created]')
        else:
            self.tg_client.send_message(msg.chat.id, '[something went wrong]')
        self.storage.reset(tg_user.chat_id)

    def handle_verified_user(self, msg: Message, tg_user: TgUser)  -> None:
        """Ручка для работы с верифицированным пользователем.
        Принимает и обрабатывает следующие командыЖ
        - /goals -> выводит список целей
        - /create -> позволяет создавать новые цели
        - /cancel -> позволяет отменить создание цели (только на этапе создания)"""
        if msg.text == '/goals':
            self.handle_goals_list(msg, tg_user)
        elif msg.text == '/create':
            self.handle_goal_categories_list(msg=msg, tg_user=tg_user)
            self.storage.set_state(msg.chat.id, state=StateEnum.CREATE_CATEGORY_SELECT)
            self.storage.set_data(msg.chat.id, data=NewGoal().dict())

        elif msg.text == '/cancel' and self.storage.get_state(tg_user.chat_id):
            self.storage.reset(tg_user.chat_id)
            self.tg_client.send_message(msg.chat.id, '[canceled]')
        elif msg.text.startswith('/'):
            self.tg_client.send_message(msg.chat.id, '[unknown command]')

        elif state := self.storage.get_state(tg_user.chat_id):
            match state:
                case StateEnum.CREATE_CATEGORY_SELECT:
                    self.handle_save_selected_category(msg, tg_user)
                case StateEnum.CHOSEN_CATEGORY:
                    self.handle_save_new_category(msg, tg_user)
                case _:
                    logger.warning('invalid state: %s', state)

    def handle_message(self, msg: Message) -> None:
        """Ручка определяющая верифицирован пользователь или нет
        верифицированных пользователей отправляет на ручку -> handle_verified_user
        не верифицированных -> handle_unverified_user, для получения кода верификации"""
        tg_user, _ = TgUser.objects.select_related('user').get_or_create(
            chat_id=msg.chat.id,
            defaults={
                'username': msg.from_.username,
            }
        )
        if tg_user.user:
            self.handle_verified_user(msg=msg, tg_user=tg_user)
        else:
            self.handle_unverified_user(msg=msg, tg_user=tg_user)

    def handle(self, *args: Any, **options: Any) -> None:
        """Ручка проверяет обновления чата. При получении новых сообщений от пользователей
        отправляет их на ручку -> handle_message"""
        offset = 0
        while True:
            res = self.tg_client.get_updates(offset=offset)
            for item in res.result:
                offset = item.update_id + 1
                self.handle_message(msg=item.message)