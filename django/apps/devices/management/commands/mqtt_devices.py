import json

from apps.devices.mqtt_client import mqtt_client
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _


class Command(BaseCommand):
    """Команда для управления MQTT клиентом и получения информации об устройствах"""

    help = _(
        "Управление MQTT клиентом и получение информации об устройствах из координатора"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--start", action="store_true", help=_("Запустить MQTT клиент")
        )
        parser.add_argument(
            "--list", action="store_true", help=_("Показать список устройств из кэша")
        )
        parser.add_argument(
            "--device",
            type=str,
            help=_("Показать информацию о конкретном устройстве по IEEE адресу"),
        )
        parser.add_argument(
            "--request-update",
            action="store_true",
            help=_("Запросить обновление информации об устройствах"),
        )

    def handle(self, *args, **options):
        if options["start"]:
            self.stdout.write("Запускаем MQTT клиент...")
            mqtt_client.start()
            self.stdout.write(self.style.SUCCESS("MQTT клиент запущен"))

        elif options["list"]:
            devices = mqtt_client.get_all_devices()
            self.stdout.write(f"Устройств в кэше: {len(devices)}")
            self.stdout.write("-" * 80)

            for ieee, device in devices.items():
                friendly_name = device.get("friendly_name", "N/A")
                model = device.get("model_id", "N/A")
                manufacturer = device.get("manufacturer", "N/A")

                self.stdout.write(f"IEEE: {ieee}")
                self.stdout.write(f"  Имя: {friendly_name}")
                self.stdout.write(f"  Модель: {model}")
                self.stdout.write(f"  Производитель: {manufacturer}")
                self.stdout.write("-" * 40)

        elif options["device"]:
            device_info = mqtt_client.get_device_info(options["device"])
            if device_info:
                self.stdout.write(json.dumps(device_info, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Устройство {options['device']} не найдено в кэше"
                    )
                )

        elif options["request_update"]:
            self.stdout.write("Запрашиваем обновление информации об устройствах...")
            mqtt_client._request_device_update()
            self.stdout.write(self.style.SUCCESS("Запрос отправлен"))

        else:
            self.stdout.write("Используйте --help для просмотра доступных команд")
