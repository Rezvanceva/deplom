from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from todolist.bot.models import TgUser
from todolist.bot.serializers import TgUserSerializer
from todolist.bot.tg.client import TgClient


class VerificationView(GenericAPIView):
    """Ручка для указания кода верификации бота"""
    model = TgUser
    permission_classes = [IsAuthenticated]
    serializer_class = TgUserSerializer

    def patch(self, request, *args, **kwargs):
        """Метод для редактирования поля verification_code пользователя"""
        serializer: TgUserSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tg_user: TgUser = serializer.validated_data['tg_user']
        tg_user.user = self.request.user
        tg_user.save(update_fields=('user',))

        instance_serializer: TgUserSerializer = self.get_serializer(tg_user)
        TgClient(settings.BOT_TOKEN).send_message(tg_user.chat_id, '[verification_completed]')
        return Response(instance_serializer.data)