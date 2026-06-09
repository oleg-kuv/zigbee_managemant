echo "Привет. Жду ответы на русском. Высылаю исходный код со структурой папок. Изучи все это, дай краткое резюме и жди вопросов."
echo "Мои устройства: Координатор - ZBDongle-P Zigbee3.0 USB Шлюз, Zigbee CC2652P USB Dongle (Информация на корпусе - zg-808z)
Устройство - zg-227z (температура и влажность) (на чипе написано: TLSR8253 F512AT32 ZHBN2534 EW4005)"

function show_file() {
    file="$1"
    if [[ -s $file ]]; then
        filename=$(basename "$file")
        name_without_ext="${filename%.*}"
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
            "ini") type="ini";;
            "env") type="env";;
            "js") type="javascript";;
            "vue") type="vue";;
            "ts") type="typescript";;
            "gitignore") type="gitignore";;
            *)
                case "$name_without_ext" in
                    "Dockerfile") type="dockerfile";;
                    "Makefile") type="makefile";;
                    *) type=""
                esac
            ;;
        esac

        filecontent="$(cat $file)"
        filecontent="${filecontent//piklema/tdfgrp}"
        filecontent="${filecontent//Piklema/TDFgrp}"

        file="${file//piklema/tdfgrp}"
        file="${file//Piklema/TDFgrp}"

        echo "$file:"
        echo '`````'$type
        echo "$filecontent"
        echo -e '\n'
        echo -e '`````\n'
    else
        echo "$file пуст."
    fi
}

# Получение списка файлов
files=$(
    find ./ -type d \
        -name "__pycache__" -prune \
        -o -path ".pytest_cache/" -prune \
        -o -path "./tests/*" -prune \
        -o -path "./alembic/versions/*" -prune \
        -o -path "./postgres/data" -prune \
        -o -path "./postgres/data*" -prune \
        -o -path "./kafka/data" -prune \
        -o -path "./django/static" -prune \
        -o -path "./zigbee2mqtt/log" -prune \
        -o -path "./zookeeper" -prune \
        -o -path "*/alembic/versions" -prune \
        -o -type d -name ".venv" -prune \
        -o -type d -name ".kilo" -prune \
        -o -type d -name "node_modules" -prune \
        -o -type d -name ".vscode" -prune \
        -o -type d -name "*.egg-info" -prune \
        -o -type d -name ".pytest_cache" -prune \
        -o -type d -name ".trunk" -prune \
        -o -type d -name ".git" -prune \
        -o -type f -name "__init__.py" -prune \
        -o -type f -name "context_generator.bash" -prune \
        -o -type f -name "prompt.md" -prune \
        -o -type f -name "*.log" -prune \
        -o -type f -name "*.tar.gz" -prune \
        -o -type f -name "*.mo" -prune \
        -o -type f -name "*.xlsx" -prune \
        -o -type f -name "docker_ovpn.conf" -prune \
        -o -type f -name "bash_history" -prune \
        -o -type f -name "1_install_lib.sh" -prune \
        -o -type f -name "0_setup_vpn.sh" -prune \
        -o -type f -name "cansniffer-piklema_arm64" -prune \
        -o -type f -name "database.boltdb" -prune \
        -o -type f -name "database.db" -prune \
        -o -type f -name "uv.lock" -prune \
        -o -type f -name "*.sql" -prune \
        -o -type f -print
)
echo "# Структура проекта"
echo '`````'
for file in $files; do
    echo "$(echo $file) ($(cat $file | wc -l | awk '{print $1}') строк)"
done
echo '`````'

# Итоговый вывод
echo "# Содержимое файлов проекта:"
for file in $files; do
    mime=$(file -bI "$file" 2>/dev/null)
    if [[ $mime != text/* ]]; then
        echo "Пропускаем нетекстовый файл: $file ($mime)"
        continue
    fi
    show_file $file
done

echo "При добавлении устройства - оно добавляется в топик zigbee2mqtt/ (пример zigbee2mqtt/0xa4c138e53b478e15)"
echo 'Вот пример содержимого топика устройства zigbee2mqtt/0xa4c138e53b478e15 {"battery":100,"humidity":24,"humidity_calibration":0,"linkquality":218,"temperature":23.9,"temperature_calibration":0,"temperature_unit":"celsius"}'
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
