from typing import Optional

from pydantic import BaseModel, Field


class MessageFrom(BaseModel):
    """Модель пользователя бота"""
    id: int
    first_name: str
    last_name: str | None = None
    username: Optional[str] | None = None


class Chat(BaseModel):
    """Модель чата бота"""
    id: int
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    title: str | None = None


class Message(BaseModel):
    """Модель сообщения бота"""
    message_id: int
    from_: MessageFrom = Field(..., alias='from')
    chat: Chat
    text: str | None = None

    class Config:
        allow_population_by_field_name = True


class UpdateObj(BaseModel):
    """Модель бота полученных сообщений"""
    update_id: int
    message: Message


class GetUpdatesResponse(BaseModel):
    """Модель бота для получения сообщений от пользователя"""
    ok: bool
    result: list[UpdateObj] = []


class SendMessagesResponse(BaseModel):
    """Модель бота для отправки сообщения"""
    ok: bool
    result: Message