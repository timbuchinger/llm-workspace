# Generated by Django 5.1.4 on 2024-12-30 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_chatsession_is_deleted_chatsession_unique_key_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Message',
            new_name='ChatMessage',
        ),
    ]
