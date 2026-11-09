# Визуализатор графа зависимостей Maven-пакетов (вариант 14)

Практическая работа № 2 по дисциплине «Конфигурационное управление» (РТУ МИРЭА, ИКБО-10-25).
Сейчас готов этап 1 — минимальный прототип с конфигурацией.

## 1. Общее описание

Консольная программа на Python. В итоге она будет строить граф зависимостей пакета Maven (Java) и рисовать его.
Готовые менеджеры пакетов и библиотеки для получения зависимостей не используются.

Что умеет программа сейчас (этап 1):

- Все настройки берутся из конфигурационного файла YAML. В командной строке указывается только путь к нему
  (`--config`), по умолчанию это `config.yaml` в текущей папке.
- Настроек шесть: имя пакета, URL репозитория (или путь к файлу тестового репозитория), режим работы
  с тестовым репозиторием, версия пакета, имя файла с картинкой графа и подстрока для фильтрации пакетов.
- Каждая настройка проверяется. Если есть ошибки, программа печатает их все сразу и завершается с кодом 1.
- Если ошибок нет, программа печатает все настройки в виде `ключ: значение`.

На этом этапе программа ничего не скачивает из сети и не создаёт файлов: она только читает конфиг (и проверяет,
что файл тестового репозитория существует).

## 2. Описание функций и настроек

### Параметры командной строки

| Параметр | Что задаёт |
|---|---|
| `-c ПУТЬ`, `--config ПУТЬ` | Путь к конфигурационному файлу YAML (по умолчанию `config.yaml`) |
| `-h`, `--help` | Справка |

### Конфигурационный файл (YAML)

Все шесть ключей обязательны.

| Ключ | Что задаёт |
|---|---|
| `package` | Имя анализируемого пакета |
| `repository` | URL репозитория или путь к файлу тестового репозитория |
| `test_mode` | Режим работы с тестовым репозиторием (`true` / `false`) |
| `version` | Версия пакета |
| `output` | Имя сгенерированного файла с изображением графа |
| `filter` | Подстрока для фильтрации пакетов (может быть пустой — тогда фильтра нет) |

Пример (это файл `config.yaml` из корня проекта):

```yaml
package: org.apache.commons:commons-text
repository: https://repo1.maven.org/maven2/
test_mode: false
version: 1.12.0
output: graph.png
filter: ""
```

Как проверяются значения:

- `package` — в обычном режиме имя пакета Maven в виде `groupId:artifactId` (буквы, цифры, `.`, `-`, `_`),
  например `org.slf4j:slf4j-api`. В тестовом режиме пакеты называются большими латинскими буквами: `A`, `B`, `ABC`.
- `repository` — в обычном режиме адрес, который начинается с `http://` или `https://` (например, Maven Central
  `https://repo1.maven.org/maven2/`). В тестовом режиме это путь к файлу, и файл должен существовать.
- `test_mode` — только `true` или `false` (регистр не важен).
- `version` — не пустая, из букв, цифр и знаков `.`, `-`, `_`, `+` (например `2.0.16`, `33.3.1-jre`).
- `output` — не пустое имя файла; это не должна быть папка, а папка, в которой будет файл, должна существовать.
- `filter` — одна строка (не список); пустая строка значит, что фильтра нет.

Ещё правила:

- Неизвестный ключ — ошибка (так ловятся опечатки, например `pakage` вместо `package`).
- Все значения читаются как текст, поэтому кавычки не нужны: `version: 1.10` так и остаётся `1.10`
  (обычный YAML прочитал бы это как число `1.1`).
- Относительные пути (`repository` в тестовом режиме, `output`) считаются от текущей папки.

Файл тестового репозитория — `examples/test_repo.txt`. На этапе 1 проверяется только, что он есть. Читать его
программа будет с этапа 3: в каждой строке пакет и через двоеточие его зависимости, например `A: B C`.

### Ошибки

Все ошибки печатаются в поток ошибок (stderr), каждая на своей строке, в виде `ключ: что не так`. Параметры при
ошибке не печатаются.

| Ситуация | Сообщение | Код завершения |
|---|---|---|
| Конфиг не найден или не читается | `cannot read the file: ...` | 1 |
| Файл не YAML | `invalid YAML: ...` | 1 |
| В файле не пары «ключ: значение» (например, список) | `the file must contain 'key: value' pairs` | 1 |
| Неизвестный ключ | `unknown key '...'` | 1 |
| Нет ключа | `ключ: the key is required` | 1 |
| Пустое значение | `ключ: the value is empty` | 1 |
| Список или словарь вместо одного значения | `ключ: must be a single value, not a list or a mapping` | 1 |
| Неверное имя пакета | `package: '...': must look like groupId:artifactId ...` или `... capital Latin letters` | 1 |
| Неверный URL | `repository: '...' is not an http(s) URL` | 1 |
| Нет файла тестового репозитория | `repository: test repository file '...' not found` | 1 |
| Режим не `true`/`false` | `test_mode: '...': must be true or false` | 1 |
| Неверные символы в версии | `version: '...' is not a valid version` | 1 |
| Имя картинки — это папка, или нет папки для файла | `output: '...' is a folder`, `... does not exist` | 1 |
| Неизвестный параметр командной строки | `usage: ...` и описание ошибки | 2 |

Если режим `test_mode` указан неверно (или его нет), имя пакета и репозиторий не проверяются: без режима
непонятно, по каким правилам их проверять.

### Функции

`src/settings.py` — чтение и проверка конфига:

| Функция | Что делает |
|---|---|
| `ConfigError` | Исключение: путь к конфигу и список всех ошибок |
| `read_yaml(path)` | Читает YAML-файл (все значения как текст), возвращает словарь; при ошибке — `ConfigError` |
| `parse_bool(value)` | `true`/`false` → `True`/`False`, иначе `None` |
| `text_error(value)` | Ошибка, если значение — список или словарь, или пустое |
| `check_test_mode(value)` | Проверяет режим работы с тестовым репозиторием |
| `check_package(value, test_mode)` | Проверяет имя пакета (зависит от режима) |
| `check_repository(value, test_mode)` | Проверяет URL или путь к тестовому репозиторию |
| `check_url(value)` | Адрес должен начинаться с `http://` или `https://` |
| `check_test_file(value)` | Файл тестового репозитория должен существовать |
| `check_version(value)` | Проверяет версию |
| `check_output(value)` | Проверяет имя файла с картинкой и папку для него |
| `check_filter(value)` | Проверяет подстроку для фильтрации |
| `find_errors(data)` | Проверяет все заданные параметры и собирает список ошибок |
| `load_settings(path)` | Читает и проверяет конфиг, возвращает словарь настроек или бросает `ConfigError` |
| `show_value(value)` | Значение для вывода: `true`/`false`, `""` для пустой строки |
| `settings_lines(settings)` | Строки `ключ: значение` для всех параметров |

`src/main.py` — точка входа:

| Функция | Что делает |
|---|---|
| `parse_args(argv)` | Разбирает командную строку (только `--config`) |
| `print_errors(error)` | Печатает все ошибки конфига в stderr |
| `main(argv)` | Читает конфиг, печатает параметры; возвращает код завершения |

## 3. Сборка, запуск и тесты

Нужен Python 3.9 или новее и библиотека PyYAML для чтения YAML. Сборка не требуется.

```
pip install -r requirements.txt
```

Запуск на Windows (из папки проекта):

```
.\run.bat
.\run.bat --config examples/real.yaml
```

Запуск на Linux/macOS: `sh run.sh [параметры]`. Или напрямую: `python src/main.py [параметры]`.

Тесты (из папки проекта):

```
python -m unittest -v
```

Скрипты для проверки (папка `scripts/`) запускают программу с разными конфигами и печатают код завершения:

| Скрипт | Что проверяет |
|---|---|
| `test_config.bat` | Правильные конфиги: по умолчанию, с фильтром, версия `1.10`, тестовый режим, `--help` |
| `test_errors.bat` | Ошибки для каждого параметра (конфиги из `examples/errors/`), нет файла, неизвестный параметр |

```
.\scripts\test_config.bat
.\scripts\test_errors.bat
```

Примеры конфигов:

| Файл | Что в нём |
|---|---|
| `config.yaml` | Конфиг по умолчанию: настоящий репозиторий Maven Central |
| `examples/real.yaml` | Настоящий репозиторий, с фильтром |
| `examples/codec.yaml` | Версия `1.10` без кавычек и пустой фильтр |
| `examples/test_mode.yaml` | Тестовый режим: пакет `A`, файл `examples/test_repo.txt` |
| `examples/errors/*.yaml` | По одной ошибке на каждый параметр и `many_errors.yaml` с несколькими ошибками сразу |

## 4. Примеры использования

Конфиг по умолчанию (`.\run.bat`):

```
Settings from 'config.yaml':
  package: org.apache.commons:commons-text
  repository: https://repo1.maven.org/maven2/
  test_mode: false
  version: 1.12.0
  output: graph.png
  filter: ""
```

Тестовый режим (`.\run.bat --config examples/test_mode.yaml`):

```
Settings from 'examples/test_mode.yaml':
  package: A
  repository: examples/test_repo.txt
  test_mode: true
  version: 1.0
  output: test_graph.png
  filter: D
```

Несколько ошибок сразу (`.\run.bat --config examples/errors/many_errors.yaml`), код завершения 1:

```
Config error in 'examples/errors/many_errors.yaml':
  unknown key 'color'
  package: 'guava': must look like groupId:artifactId (e.g. org.slf4j:slf4j-api)
  repository: 'ftp://repo1.maven.org/maven2/' is not an http(s) URL
  version: '33 beta' is not a valid version
  output: 'no_such_folder/graph.png': folder 'no_such_folder' does not exist
  filter: must be a single value, not a list or a mapping
```

Не хватает параметров (`.\run.bat --config examples/errors/missing_keys.yaml`), код завершения 1:

```
Config error in 'examples/errors/missing_keys.yaml':
  test_mode: the key is required
  version: the key is required
  output: the key is required
  filter: the key is required
```

Нет файла тестового репозитория (`.\run.bat --config examples/errors/no_test_repo.yaml`), код завершения 1:

```
Config error in 'examples/errors/no_test_repo.yaml':
  repository: test repository file 'examples/no_such_repo.txt' not found
```

## Структура репозитория

```
src/main.py           точка входа
src/settings.py       чтение и проверка конфига
tests/                тесты (unittest)
scripts/              скрипты Windows для проверки
examples/             примеры конфигов, тестовый репозиторий, конфиги с ошибками (папка errors/)
config.yaml           конфиг по умолчанию
requirements.txt      зависимости (PyYAML)
run.bat, run.sh       запуск (Windows / Linux, macOS)
```
