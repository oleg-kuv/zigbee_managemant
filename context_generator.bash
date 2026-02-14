echo "Привет. Жду ответы на русском. Высылаю исходный код со структурой папок. Изучи все это, дай краткое резюме и жди вопросов."
echo "Мои устройства: Координатор - ZBDongle-P Zigbee3.0 USB Шлюз, Zigbee CC2652P USB Dongle (Информация на корпусе - zg-808z)
Устройство - zg-227z (температура и влажность) (на чипе написано: TLSR8253 F512AT32 ZHBN2534 EW4005)"
echo "Структура проекта"
echo '```'
tree -I ".venv|__pycache__|htmlcov|logs|__init__.py|prompt.md|context_generator.bash|data|log|static" ./
echo -e '```\n'

# Функция вывода файла
function show_file() {
    file=$1
    if [[ -s $file ]]; then
        filename=$(basename "$file")
        extension="${filename##*.}"
        case "$extension" in
            "py") type="python";;
            "yml") type="yaml";;
            "yaml") type="yaml";;
            "json") type="json";;
            "toml") type="toml";;
            "bash") type="shell";;
            "sh") type="shell";;
            "txt") type="text";;
            *) type="";;
        esac
        echo "$file:"
        echo '```'$type
        cat $file
        echo -e '```\n'
    else
        echo "$file пуст."
    fi
}

# Получение списка файлов
files=$(
    find ./ -type d \
        -name "__pycache__" -prune \
        -o -path "./postgres/data" -prune \
        -o -path "./kafka/data" -prune \
        -o -path "./django/static" -prune \
        -o -path "./zigbee2mqtt/log" -prune \
        -o -path "./zookeeper" -prune \
        -o -type d -name ".venv" -prune \
        -o -type d -name ".git" -prune \
        -o -type f -name "__init__.py" -prune \
        -o -type f -name "context_generator.bash" -prune \
        -o -type f -name "prompt.md" -prune \
        -o -type f -print
)

# Итоговый вывод
echo "Содержимое файлов проекта:"
for file in $files; do
    show_file $file
done
echo "При добавлении устройства - оно добавляется в топик zigbee2mqtt/ (пример zigbee2mqtt/0xa4c138e53b478e15)"
echo 'Вот пример содержимого топика устройства zigbee2mqtt/0xa4c138e53b478e15 {"battery":100,"humidity":24,"humidity_calibration":0,"linkquality":218,"temperature":23.9,"temperature_calibration":0,"temperature_unit":"celsius"}'

echo 'Вот топик 
```zigbee2mqtt/bridge/devices: [
  {
    "disabled": false,
    "endpoints": {
      "1": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "2": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "3": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "4": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "5": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "6": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "8": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "10": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "11": {
        "bindings": [],
        "clusters": {
          "input": [
            "ssIasAce",
            "genTime"
          ],
          "output": [
            "ssIasZone",
            "ssIasWd"
          ]
        },
        "configured_reportings": [],
        "scenes": []
      },
      "12": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "13": {
        "bindings": [],
        "clusters": {
          "input": [
            "genOta"
          ],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "47": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "110": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "239": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      },
      "242": {
        "bindings": [],
        "clusters": {
          "input": [],
          "output": []
        },
        "configured_reportings": [],
        "scenes": []
      }
    },
    "friendly_name": "Coordinator",
    "ieee_address": "0x00124b0030dd66b3",
    "interview_completed": true,
    "interview_state": "SUCCESSFUL",
    "interviewing": false,
    "network_address": 0,
    "supported": true,
    "type": "Coordinator"
  },
  {
    "date_code": "30122025",
    "definition": {
      "description": "Temperature & humidity LCD sensor",
      "exposes": [
        {
          "access": 1,
          "description": "Measured temperature value",
          "label": "Temperature",
          "name": "temperature",
          "property": "temperature",
          "type": "numeric",
          "unit": "°C"
        },
        {
          "access": 1,
          "description": "Measured relative humidity",
          "label": "Humidity",
          "name": "humidity",
          "property": "humidity",
          "type": "numeric",
          "unit": "%"
        },
        {
          "access": 3,
          "description": "Temperature unit",
          "label": "Temperature unit",
          "name": "temperature_unit",
          "property": "temperature_unit",
          "type": "enum",
          "values": [
            "celsius",
            "fahrenheit"
          ]
        },
        {
          "access": 3,
          "description": "Temperature calibration",
          "label": "Temperature calibration",
          "name": "temperature_calibration",
          "property": "temperature_calibration",
          "type": "numeric",
          "unit": "°C",
          "value_max": 2,
          "value_min": -2,
          "value_step": 0.1
        },
        {
          "access": 3,
          "description": "Humidity calibration",
          "label": "Humidity calibration",
          "name": "humidity_calibration",
          "property": "humidity_calibration",
          "type": "numeric",
          "unit": "%",
          "value_max": 30,
          "value_min": -30,
          "value_step": 1
        },
        {
          "access": 1,
          "category": "diagnostic",
          "description": "Remaining battery in %, can take up to 24 hours before reported",
          "label": "Battery",
          "name": "battery",
          "property": "battery",
          "type": "numeric",
          "unit": "%",
          "value_max": 100,
          "value_min": 0
        },
        {
          "access": 1,
          "category": "diagnostic",
          "description": "Link quality (signal strength)",
          "label": "Linkquality",
          "name": "linkquality",
          "property": "linkquality",
          "type": "numeric",
          "unit": "lqi",
          "value_max": 255,
          "value_min": 0
        }
      ],
      "model": "ZG-227ZL",
      "options": [
        {
          "access": 2,
          "description": "Calibrates the temperature value (absolute offset), takes into effect on next report of device.",
          "label": "Temperature calibration",
          "name": "temperature_calibration",
          "property": "temperature_calibration",
          "type": "numeric",
          "value_step": 0.1
        },
        {
          "access": 2,
          "description": "Number of digits after decimal point for temperature, takes into effect on next report of device. This option can only decrease the precision, not increase it.",
          "label": "Temperature precision",
          "name": "temperature_precision",
          "property": "temperature_precision",
          "type": "numeric",
          "value_max": 3,
          "value_min": 0
        },
        {
          "access": 2,
          "description": "Calibrates the humidity value (absolute offset), takes into effect on next report of device.",
          "label": "Humidity calibration",
          "name": "humidity_calibration",
          "property": "humidity_calibration",
          "type": "numeric",
          "value_step": 0.1
        },
        {
          "access": 2,
          "description": "Number of digits after decimal point for humidity, takes into effect on next report of device. This option can only decrease the precision, not increase it.",
          "label": "Humidity precision",
          "name": "humidity_precision",
          "property": "humidity_precision",
          "type": "numeric",
          "value_max": 3,
          "value_min": 0
        }
      ],
      "source": "native",
      "supports_ota": false,
      "vendor": "Tuya"
    },
    "disabled": false,
    "endpoints": {
      "1": {
        "bindings": [],
        "clusters": {
          "input": [
            "genBasic",
            "genIdentify",
            "manuSpecificTuya",
            "msTemperatureMeasurement",
            "msRelativeHumidity",
            "genPowerCfg"
          ],
          "output": [
            "genIdentify"
          ]
        },
        "configured_reportings": [],
        "scenes": []
      }
    },
    "friendly_name": "0xa4c13851d88beb21",
    "ieee_address": "0xa4c13851d88beb21",
    "interview_completed": true,
    "interview_state": "SUCCESSFUL",
    "interviewing": false,
    "manufacturer": "HOBEIAN",
    "model_id": "ZG-227Z",
    "network_address": 4168,
    "power_source": "Battery",
    "software_build_id": "0130122025",
    "supported": true,
    "type": "EndDevice"
  },
  {
    "date_code": "30122025",
    "definition": {
      "description": "Temperature & humidity LCD sensor",
      "exposes": [
        {
          "access": 1,
          "description": "Measured temperature value",
          "label": "Temperature",
          "name": "temperature",
          "property": "temperature",
          "type": "numeric",
          "unit": "°C"
        },
        {
          "access": 1,
          "description": "Measured relative humidity",
          "label": "Humidity",
          "name": "humidity",
          "property": "humidity",
          "type": "numeric",
          "unit": "%"
        },
        {
          "access": 3,
          "description": "Temperature unit",
          "label": "Temperature unit",
          "name": "temperature_unit",
          "property": "temperature_unit",
          "type": "enum",
          "values": [
            "celsius",
            "fahrenheit"
          ]
        },
        {
          "access": 3,
          "description": "Temperature calibration",
          "label": "Temperature calibration",
          "name": "temperature_calibration",
          "property": "temperature_calibration",
          "type": "numeric",
          "unit": "°C",
          "value_max": 2,
          "value_min": -2,
          "value_step": 0.1
        },
        {
          "access": 3,
          "description": "Humidity calibration",
          "label": "Humidity calibration",
          "name": "humidity_calibration",
          "property": "humidity_calibration",
          "type": "numeric",
          "unit": "%",
          "value_max": 30,
          "value_min": -30,
          "value_step": 1
        },
        {
          "access": 1,
          "category": "diagnostic",
          "description": "Remaining battery in %, can take up to 24 hours before reported",
          "label": "Battery",
          "name": "battery",
          "property": "battery",
          "type": "numeric",
          "unit": "%",
          "value_max": 100,
          "value_min": 0
        },
        {
          "access": 1,
          "category": "diagnostic",
          "description": "Link quality (signal strength)",
          "label": "Linkquality",
          "name": "linkquality",
          "property": "linkquality",
          "type": "numeric",
          "unit": "lqi",
          "value_max": 255,
          "value_min": 0
        }
      ],
      "model": "ZG-227ZL",
      "options": [
        {
          "access": 2,
          "description": "Calibrates the temperature value (absolute offset), takes into effect on next report of device.",
          "label": "Temperature calibration",
          "name": "temperature_calibration",
          "property": "temperature_calibration",
          "type": "numeric",
          "value_step": 0.1
        },
        {
          "access": 2,
          "description": "Number of digits after decimal point for temperature, takes into effect on next report of device. This option can only decrease the precision, not increase it.",
          "label": "Temperature precision",
          "name": "temperature_precision",
          "property": "temperature_precision",
          "type": "numeric",
          "value_max": 3,
          "value_min": 0
        },
        {
          "access": 2,
          "description": "Calibrates the humidity value (absolute offset), takes into effect on next report of device.",
          "label": "Humidity calibration",
          "name": "humidity_calibration",
          "property": "humidity_calibration",
          "type": "numeric",
          "value_step": 0.1
        },
        {
          "access": 2,
          "description": "Number of digits after decimal point for humidity, takes into effect on next report of device. This option can only decrease the precision, not increase it.",
          "label": "Humidity precision",
          "name": "humidity_precision",
          "property": "humidity_precision",
          "type": "numeric",
          "value_max": 3,
          "value_min": 0
        }
      ],
      "source": "native",
      "supports_ota": false,
      "vendor": "Tuya"
    },
    "disabled": false,
    "endpoints": {
      "1": {
        "bindings": [],
        "clusters": {
          "input": [
            "genBasic",
            "genIdentify",
            "manuSpecificTuya",
            "msTemperatureMeasurement",
            "msRelativeHumidity",
            "genPowerCfg"
          ],
          "output": [
            "genIdentify"
          ]
        },
        "configured_reportings": [],
        "scenes": []
      }
    },
    "friendly_name": "0xa4c138e53b478e15",
    "ieee_address": "0xa4c138e53b478e15",
    "interview_completed": true,
    "interview_state": "SUCCESSFUL",
    "interviewing": false,
    "manufacturer": "HOBEIAN",
    "model_id": "ZG-227Z",
    "network_address": 14950,
    "power_source": "Battery",
    "software_build_id": "0130122025",
    "supported": true,
    "type": "EndDevice"
  }
]
```'


echo 'Примеры поля data таблицы `sensor_measurements`:'
echo '
```
{"battery": 100, "voltage": 3000, "humidity": 40.52, "linkquality": 174, "temperature": 27.89}                                                                                                       
{"battery": 100, "humidity": 38, "linkquality": 178, "temperature": 24, "temperature_unit": "fahrenheit", "humidity_calibration": 0, "temperature_calibration": 0}                                   
{"battery": 100, "rainwater": "none", "illuminance": 0, "linkquality": 112, "sensitivity": 5, "illuminance_sampling": 2}                                                                             
{"battery": 100, "humidity": 51, "linkquality": 54, "temperature": 19.9, "temperature_unit": "fahrenheit", "humidity_calibration": 0, "temperature_calibration": 0}                                  
{"tamper": false, "battery": 90, "voltage": 2900, "water_leak": false, "battery_low": false, "linkquality": 185}                                                                                     
{"battery": 100, "humidity": 42, "linkquality": 21, "temperature": 22.9, "temperature_unit": "celsius", "humidity_calibration": 0, "temperature_calibration": 0}                                     
```
'

echo 'Я веду разработку на macos'
echo "Требования к коду: Не использовать относительные импорты. Оставлять фалйы __init__.py пустыми. Все импорты указывать только вначале файла. Использовать gettext_lazy"
echo "Отвечай на русском языке. Отвечай кратко."
