from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from apps.locations.models import Location


class Command(BaseCommand):
    help = _('Создание тестовой иерархии местоположений')
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help=_('Очистить все существующие местоположения перед созданием')
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(_('Очищаем существующие местоположения...'))
            count, _ = Location.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(_('Удалено местоположений: %(count)d') % {'count': count})
            )
        
        self.stdout.write(_('Создаем тестовую иерархию местоположений...'))
        
        # Создаем иерархию
        house = Location.objects.create(name=_("Дом"), order=1)
        
        floor1 = Location.objects.create(name=_("Этаж 1"), parent=house, order=1)
        floor2 = Location.objects.create(name=_("Этаж 2"), parent=house, order=2)
        
        # Этаж 1
        living_room = Location.objects.create(name=_("Гостиная"), parent=floor1, order=1)
        kitchen = Location.objects.create(name=_("Кухня"), parent=floor1, order=2)
        bedroom1 = Location.objects.create(name=_("Спальня 1"), parent=floor1, order=3)
        
        # Углы в гостиной
        Location.objects.create(name=_("Угол у окна"), parent=living_room, order=1)
        Location.objects.create(name=_("Угол у двери"), parent=living_room, order=2)
        
        # Этаж 2
        bedroom2 = Location.objects.create(name=_("Спальня 2"), parent=floor2, order=1)
        office = Location.objects.create(name=_("Кабинет"), parent=floor2, order=2)
        
        # Балансировка
        bathroom = Location.objects.create(name=_("Ванная комната"), parent=floor1, order=4)
        hallway = Location.objects.create(name=_("Коридор"), parent=floor1, order=5)
        
        self.stdout.write(
            self.style.SUCCESS(_('✅ Тестовая иерархия создана!'))
        )
        
        # Выводим статистику
        total = Location.objects.count()
        roots = Location.objects.filter(parent__isnull=True).count()
        max_depth = max(loc.get_depth() for loc in Location.objects.all())
        
        self.stdout.write(_('\n📊 Статистика:'))
        self.stdout.write(_('  Всего местоположений: %(total)d') % {'total': total})
        self.stdout.write(_('  Корневых элементов: %(roots)d') % {'roots': roots})
        self.stdout.write(_('  Максимальная глубина: %(depth)d/5') % {'depth': max_depth})
        
        # Выводим дерево
        self.stdout.write(_('\n�� Структура дерева:'))
        for root in Location.objects.filter(parent__isnull=True).order_by('order', 'name'):
            self.print_tree(root)
    
    def print_tree(self, location, depth=0):
        """Рекурсивный вывод дерева"""
        indent = "  " * depth
        arrow = "└─ " if depth > 0 else "🌳 "
        
        # Добавляем индикаторы
        indicators = []
        if location.is_root:
            indicators.append("🏠")
        if location.is_leaf:
            indicators.append("🍃")
        
        indicator_str = " " + " ".join(indicators) if indicators else ""
        
        self.stdout.write(f"{indent}{arrow}{location.name} (ID: {location.id}){indicator_str}")
        for child in location.children.all().order_by('order', 'name'):
            self.print_tree(child, depth + 1)
