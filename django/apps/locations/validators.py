from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_max_depth(value, max_depth=5):
    """
    Валидатор максимальной глубины вложенности.
    
    Args:
        value: Экземпляр Location
        max_depth (int): Максимальная допустимая глубина
        
    Raises:
        ValidationError: Если глубина превышает max_depth
    """
    if hasattr(value, 'get_depth'):
        depth = value.get_depth()
        if depth > max_depth:
            raise ValidationError(
                _("Максимальная глубина вложенности - %(max_depth)d уровней. "
                  "Текущая глубина: %(depth)d"),
                code='max_depth',
                params={'max_depth': max_depth, 'depth': depth}
            )


def validate_no_self_reference(value, instance):
    """
    Валидатор: нельзя ссылаться на самого себя.
    
    Args:
        value: Значение поля (например, parent)
        instance: Экземпляр модели, который сохраняется
        
    Raises:
        ValidationError: Если значение ссылается на сам экземпляр
    """
    if value and instance and value.pk == instance.pk:
        raise ValidationError(
            _("Нельзя ссылаться на самого себя"),
            code='self_reference'
        )


def validate_no_circular_dependency(value, instance):
    """
    Валидатор: проверка циклических зависимостей.
    
    Args:
        value: Значение поля (например, parent)
        instance: Экземпляр модели, который сохраняется
        
    Raises:
        ValidationError: Если обнаружена циклическая зависимость
    """
    if value and instance and instance.pk:
        # Получаем всех предков значения
        ancestors_ids = set()
        current = value
        while current:
            ancestors_ids.add(current.pk)
            if current.parent:
                current = current.parent
            else:
                break
        
        # Проверяем, не является ли instance предком value
        if instance.pk in ancestors_ids:
            raise ValidationError(
                _("Обнаружена циклическая зависимость. "
                  "Нельзя сделать потомка родителем его предка."),
                code='circular_dependency'
            )
