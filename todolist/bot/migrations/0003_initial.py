# Generated by Django 4.1.5 on 2023-02-09 13:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bot', '0002_delete_tguser'),
    ]

    operations = [
        migrations.CreateModel(
            name='TgUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.BigIntegerField(unique=True, verbose_name='Chat ID')),
                ('username', models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='Username')),
                ('verification_code', models.CharField(blank=True, default=None, max_length=32, null=True)),
                ('user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]