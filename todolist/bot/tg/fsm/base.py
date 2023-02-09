from abc import ABC, abstractmethod
from enum import Enum


class Storage(ABC):
    """Абстрактный класс для работы с данными бота"""

    @abstractmethod
    def get_state(self, chat_id: int) -> Enum | None:
        """Метод получения состояния чата"""
        raise NotImplementedError

    @abstractmethod
    def get_data(self, chat_id: int) -> dict:
        """Метод получения id чата из памяти при создании новой цели"""
        raise NotImplementedError

    @abstractmethod
    def set_state(self, chat_id: int, state: Enum) -> None:
        """Метод для установки состояния чата"""
        raise NotImplementedError

    @abstractmethod
    def set_data(self, chat_id: int, data: dict) -> None:
        """Метод для отправки в память данных chat_id и новой цели"""
        raise NotImplementedError

    @abstractmethod
    def reset(self, chat_id: int) -> bool:
        """Метод для очистки данных о чате из памяти"""
        raise NotImplementedError

    @abstractmethod
    def update_data(self, chat_id: int, **kwargs) -> None:
        """Метод для обновления данных уже существующего чата"""
        raise NotImplementedError