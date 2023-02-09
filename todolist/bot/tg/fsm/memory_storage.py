from enum import Enum
from pydantic import BaseModel
from todolist.bot.tg.fsm.base import Storage


class StorageData(BaseModel):
    """Класс модели бота"""
    state: Enum | None = None
    data: dict = {}


class MemoryStorage(Storage):
    """Класс для работы с данными бота"""

    def __init__(self):
        self.data: dict[int, StorageData] = {}

    def _resolve_chat(self, chat_id: int):
        """Защищенный метод проверяющий, если ли в памяти чат с указанным id,
        если нет создается новая запись"""
        if chat_id not in self.data:
            self.data[chat_id] = StorageData()
        return self.data[chat_id]

    def get_state(self, chat_id: int) -> StorageData | None:
        """Метод получения состояния чата"""
        return self._resolve_chat(chat_id).state

    def get_data(self, chat_id: int) -> dict:
        """Метод получения id чата из памяти при создании новой цели"""
        return self._resolve_chat(chat_id).data

    def set_state(self, chat_id, state: Enum) -> None:
        """Метод для установки состояния чата"""
        self._resolve_chat(chat_id).state = state

    def set_data(self, chat_id: int, data: dict) -> None:
        """Метод для отправки в память данных chat_id и новой цели"""
        self._resolve_chat(chat_id).data = data

    def reset(self, chat_id: int) -> bool:
        """Метод для очистки данных о чате из памяти"""
        return bool(self.data.pop(chat_id, None))

    def update_data(self, chat_id: int, **kwargs) -> None:
        """Метод для обновления данных уже существующего чата"""
        self._resolve_chat(chat_id).data.update(**kwargs)