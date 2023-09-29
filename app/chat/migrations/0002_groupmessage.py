# Generated by Django 4.2.2 on 2023-09-29 12:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.CharField(max_length=512)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_messages', to='chat.conversation')),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='messages_from_user', to=settings.AUTH_USER_MODEL)),
                ('read', models.ManyToManyField(blank=True, related_name='read_users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
