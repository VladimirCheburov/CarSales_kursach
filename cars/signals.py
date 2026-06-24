from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from cars.models import Profile, Message


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=Message)
def notify_message_via_telegram(sender, instance, created, **kwargs):
    if created:
        from cars.tasks import notify_telegram_new_message
        notify_telegram_new_message.delay(instance.id)
