echo "Структура проекта"
echo '```'
tree -I "__pycache__|htmlcov|logs|__init__.py|prompt.md|context_generator.bash|data" ./
echo -e '```\n'

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

files=$(
    find ./ -type d \
        -name "__pycache__" -prune \
        -o -path "./postgres/data" -prune \
        -o -path "./kafka/data" -prune \
        -o -type d -name ".git" -prune \
        -o -type f -name "__init__.py" -prune \
        -o -type f -name "context_generator.bash" -prune \
        -o -type f -name "prompt.md" -prune \
        -o -type f -print
)

echo "Содержимое файлов проекта:"
for file in $files; do
    show_file $file
done
