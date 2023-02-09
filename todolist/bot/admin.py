from django.contrib import admin

from todolist.bot.models import TgUser


# Register your models here
@admin.register(TgUser)
class TgUserAdmin(admin.ModelAdmin):
    """Класс модели для корректного отображения полей бота в Админ панели"""
    list_display = ('chat_id', 'username', 'user')
    read_only_fields = ('chat_id', 'verification_code')