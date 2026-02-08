from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Location


class LocationForm(forms.ModelForm):
    """Форма для создания/редактирования Location"""
    
    class Meta:
        model = Location
        fields = ['name', 'parent', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'vTextField',
                'placeholder': _('Введите название местоположения')
            }),
            'parent': forms.Select(attrs={
                'class': 'vSelect'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 3,
                'placeholder': _('Опциональное описание')
            }),
            'order': forms.NumberInput(attrs={
                'class': 'vIntegerField',
                'min': 0,
                'max': 1000
            }),
        }
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        
        # Проверка глубины вложенности
        parent = cleaned_data.get('parent')
        if parent:
            # Создаем временный объект для проверки глубины
            temp_location = Location(
                parent=parent,
                name=cleaned_data.get('name', '')
            )
            try:
                temp_location.clean()
            except ValidationError as e:
                raise ValidationError({'parent': e})
        
        return cleaned_data


class LocationAdminForm(LocationForm):
    """Форма для админки с дополнительными функциями"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор parent только допустимыми вариантами
        if self.instance and self.instance.pk:
            # Исключаем текущий элемент и его потомков из выбора родителя
            from django.db.models import Q
            
            # Получаем ID всех потомков
            descendants_ids = []
            stack = [self.instance]
            while stack:
                current = stack.pop()
                descendants_ids.append(current.id)
                stack.extend(current.children.all())
            
            self.fields['parent'].queryset = Location.objects.exclude(
                id__in=descendants_ids
            ).order_by('order', 'name')
        else:
            self.fields['parent'].queryset = Location.objects.all().order_by('order', 'name')
