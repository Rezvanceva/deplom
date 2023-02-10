from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'OK'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('todolist.core.urls')),
    path('goals/', include('todolist.goals.urls')),
    path('bot/', include('todolist.bot.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls')),
    ]
