from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from library.models import Borrow

@receiver(post_save, sender=Borrow)
def notify_member_on_borrow_status_change(sender, instance, created, **kwargs):
    if created:
        return

    if instance.status == 'closed':
        member_email = instance.member.email
        send_mail(
            subject="Ваша задача в библиотеке закрыта",
            message=f"Здравствуйте, {instance.member.username}! Книга '{instance.book.name}' успешно возвращена.",
            from_email='library@example.com',
            recipient_list=[member_email],
            fail_silently=False,
        )