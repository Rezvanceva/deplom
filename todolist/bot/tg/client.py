import requests

from todolist.bot.tg.dc import GetUpdatesResponse, SendMessagesResponse


class TgClient:
    """Класс для подключения и взаимодействия с ботом"""

    def __init__(self, token: str):
        self.token = token

    def get_url(self, method: str) -> str:
        """Метод подключения к боту через url с токеном"""
        return f'https://api.telegram.org/bot{self.token}/{method}'

    def get_updates(self, offset: int = 0, timeout: int = 60) -> GetUpdatesResponse:
        """Метод для получения обновлений из чата бота"""
        url = self.get_url('getUpdates')
        response = requests.get(url, params={'offset': offset, 'timeout': timeout})
        return GetUpdatesResponse(**response.json())

    def send_message(self, chat_id: int, text: str) -> SendMessagesResponse:
        """Метод для отправки сообщений в чат бота"""
        url = self.get_url('sendMessage')
        response = requests.post(url, json={'chat_id': chat_id, 'text': text})
        return SendMessagesResponse(**response.json())
