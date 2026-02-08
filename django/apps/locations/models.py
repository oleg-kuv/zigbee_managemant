from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    """
    Иерархия местоположений.
    Максимальная глубина вложенности: 5 уровней.
    Пример: Дом → Этаж 1 → Квартира 101 → Гостиная → Угол у окна
    """

    # Основные поля
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Например: 'Гостиная', 'Кухня', 'Этаж 1'"),
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Родительское местоположение"),
        related_name="children",
        help_text=_("Выберите родительское местоположение для создания иерархии"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Дополнительная информация о местоположении"),
    )

    order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок сортировки"),
        help_text=_("Чем меньше число, тем выше в списке (0 - самый верх)"),
    )

    # Автоматические поля
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата создания")
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))

    class Meta:
        verbose_name = _("Местоположение")
        verbose_name_plural = _("Местоположения")
        ordering = ["order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="unique_location_name_per_parent",
                violation_error_message=_(
                    "Местоположение с таким именем уже существует на этом уровне"
                ),
            )
        ]
        indexes = [
            models.Index(fields=["parent", "order", "name"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        """Строковое представление: имя"""
        return self.name

    def get_absolute_url(self):
        """URL для админки"""
        return reverse("admin:locations_location_change", args=[str(self.id)])

    def get_full_path(self, separator=" → "):
        """
        Полный путь местоположения в иерархии.

        Пример:
        Дом → Этаж 1 → Гостиная → Угол у окна
        """
        if self.parent:
            return f"{self.parent.get_full_path(separator)}{separator}{self.name}"
        return self.name

    def get_depth(self):
        """
        Получить глубину вложенности.

        Возвращает:
            int: Уровень вложенности (1 для корневых элементов)
        """
        depth = 1
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth

    def get_ancestors(self, include_self=False):
        """
        Получить всех предков местоположения.

        Args:
            include_self (bool): Включать текущее местоположение в результат

        Returns:
            list: Список предков от корня к текущему элементу
        """
        ancestors = []
        current = self

        if include_self:
            ancestors.append(current)

        while current.parent:
            ancestors.append(current.parent)
            current = current.parent

        # Возвращаем в порядке от корня к текущему элементу
        return list(reversed(ancestors))

    def clean(self):
        """
        Валидация модели.

        Проверяет:
        1. Максимальная глубина вложенности (5 уровней)
        2. Нельзя сделать родителем самого себя
        3. Нельзя создать циклическую зависимость
        """
        super().clean()

        # 1. Проверка максимальной глубины (5 уровней)
        if self.parent:
            depth = self.parent.get_depth() + 1
            if depth > 5:
                raise ValidationError(
                    {
                        "parent": ValidationError(
                            _(
                                "Максимальная глубина вложенности - 5 уровней. "
                                "Текущая глубина: %(depth)d"
                            ),
                            code="max_depth",
                            params={"depth": depth},
                        )
                    }
                )

        # 2. Нельзя сделать родителем самого себя
        if self.pk and self.parent and self.parent.pk == self.pk:
            raise ValidationError(
                {
                    "parent": ValidationError(
                        _("Нельзя сделать местоположение родителем самого себя"),
                        code="self_parent",
                    )
                }
            )

        # 3. Проверка циклической зависимости
        if self.pk and self.parent:
            ancestors = self.parent.get_ancestors(include_self=True)
            ancestor_ids = [anc.pk for anc in ancestors]
            if self.pk in ancestor_ids:
                raise ValidationError(
                    {
                        "parent": ValidationError(
                            _(
                                "Обнаружена циклическая зависимость. "
                                "Нельзя сделать потомка родителем его предка."
                            ),
                            code="circular_dependency",
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """
        Переопределение save с валидацией.
        """
        self.full_clean()  # Вызываем полную валидацию
        super().save(*args, **kwargs)

    @property
    def is_root(self):
        """Является ли местоположение корневым (без родителя)"""
        return self.parent is None

    @property
    def is_leaf(self):
        """Является ли местоположение листом (нет детей)"""
        return not self.children.exists()

    @classmethod
    def get_root_locations(cls):
        """Получить все корневые местоположения"""
        return cls.objects.filter(parent__isnull=True).order_by("order", "name")

    @classmethod
    def get_tree(cls):
        """
        Получить дерево местоположений в виде вложенного словаря.

        Returns:
            list: Дерево местоположений
        """

        def build_tree(parent_id=None):
            locations = cls.objects.filter(parent_id=parent_id).order_by(
                "order", "name"
            )
            tree = []
            for location in locations:
                tree.append(
                    {
                        "id": location.id,
                        "name": location.name,
                        "description": location.description,
                        "order": location.order,
                        "depth": location.get_depth(),
                        "is_root": location.is_root,
                        "is_leaf": location.is_leaf,
                        "children": build_tree(location.id),
                    }
                )
            return tree

        return build_tree()
