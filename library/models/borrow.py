from datetime import datetime
from django.db import models
from django.utils import timezone

class Borrow(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        CLOSED = 'closed', 'Закрыта'

    member = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='borrows',
    )
    book = models.ForeignKey(
        "Book",
        on_delete=models.PROTECT,
        related_name='borrows',
    )
    library = models.ForeignKey(
        "Library",
        on_delete=models.PROTECT,
        related_name='borrows',
    )
    issue_date = models.DateField(
        default=timezone.now,
    )
    return_plane_date = models.DateField(
        verbose_name='Планируемая дата возврата',
    )
    return_actual_date = models.DateField(
        verbose_name='Фактическая дата возврата',
        null=True,
        blank=True,
    )
    is_returned = models.BooleanField(
        verbose_name='Книгу вернули',
        default=False
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус задачи'
    )

    def save(self, *args, **kwargs):
        # Автоматически синхронизируем статус с флагом is_returned
        self.status = self.Status.CLOSED if self.is_returned else self.Status.ACTIVE
        super().save(*args, **kwargs)

    def check_date_is_returned(self):
        if self.is_returned and self.return_actual_date and self.return_actual_date > self.return_plane_date:
            return False
        return True

    def __str__(self):
        return f"{self.member} - {self.book.name} ({self.status})"