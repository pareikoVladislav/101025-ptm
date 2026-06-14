from django.db import models
from django.utils import timezone

class SoftDeletionQuerySet(models.QuerySet):
    def delete(self):
        return super().update(
            is_deleted=True,
            deleted_at=timezone.now()
        )

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeletionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            # Менеджер по умолчанию возвращает только НЕ удаленные записи (Задание 2)
            return SoftDeletionQuerySet(self.model, using=self._db).filter(is_deleted=False)
        return SoftDeletionQuerySet(self.model, using=self._db)


class SoftDeletionModel(models.Model):
    # Поля мягкого удаления согласно требованиям ТЗ (Задание 2)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    # Переопределяем менеджеров: objects выдает только живых
    objects = SoftDeletionManager(alive_only=True)
    all_objects = SoftDeletionManager(alive_only=False)

    # Переопределяем стандартный метод удаления экземпляра (Задание 2)
    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])