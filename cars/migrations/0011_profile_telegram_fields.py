from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0010_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='telegram_chat_id',
            field=models.BigIntegerField(blank=True, null=True, unique=True, verbose_name='Telegram chat ID'),
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_link_token',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
