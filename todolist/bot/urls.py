from django.urls import path

from todolist.bot.views import VerificationView

urlpatterns = [
    path('verify', VerificationView.as_view(), name='verify-user'),

]