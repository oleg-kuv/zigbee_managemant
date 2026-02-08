from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from .models import Location


class LocationAdmin(admin.ModelAdmin):
    """Админка для модели Location"""
    
    list_display = ('name', 'parent_link', 'description_short', 'order', 'depth', 'created_at')
    list_display_links = ('name',)
    list_editable = ('order',)
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    readonly_fields = ('created_at', 'updated_at', 'full_path_display')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'parent', 'full_path_display', 'description')
        }),
        (_('Настройки'), {
            'fields': ('order',),
            'classes': ('collapse',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        queryset = super().get_queryset(request)
        return queryset.select_related('parent')
    
    def parent_link(self, obj):
        """Ссылка на родительское местоположение"""
        if obj.parent:
            url = reverse('admin:locations_location_change', args=[obj.parent.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent.name)
        return _("Корневой")
    parent_link.short_description = _("Родитель")
    parent_link.admin_order_field = 'parent__name'
    
    def description_short(self, obj):
        """Короткое описание"""
        if obj.description:
            truncated = obj.description[:50]
            if len(obj.description) > 50:
                truncated += '...'
            return truncated
        return '-'
    description_short.short_description = _("Описание")
    
    def depth(self, obj):
        """Отображение глубины с цветовой индикацией"""
        depth_value = obj.get_depth()
        if depth_value == 1:
            color = 'green'
        elif depth_value <= 3:
            color = 'blue'
        elif depth_value == 4:
            color = 'orange'
        else:  # depth == 5
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/5</span>',
            color, depth_value
        )
    depth.short_description = _("Глубина")
    
    def full_path_display(self, obj):
        """Отображение полного пути в форме"""
        return format_html(
            '<div style="padding: 8px; background: #f5f5f5; border-radius: 4px;">'
            '<strong>{}</strong>'
            '</div>',
            obj.get_full_path(' → ')
        )
    full_path_display.short_description = _("Полный путь")
    
    def response_add(self, request, obj, post_url_continue=None):
        """Кастомизация ответа после добавления"""
        msg = _('Местоположение "%(name)s" успешно создано.') % {'name': obj.name}
        messages.success(request, msg)
        return super().response_add(request, obj, post_url_continue)
    
    def response_change(self, request, obj):
        """Кастомизация ответа после изменения"""
        msg = _('Местоположение "%(name)s" успешно изменено.') % {'name': obj.name}
        messages.success(request, msg)
        return super().response_change(request, obj)


# Регистрируем модель в админке
admin.site.register(Location, LocationAdmin)
