# Визуализатор графа зависимостей Maven-пакетов (вариант 14)

Практическая работа № 2 по дисциплине «Конфигурационное управление» (РТУ МИРЭА, ИКБО-10-25).
Готовы этапы 1 (минимальный прототип с конфигурацией) и 2 (сбор данных).

## 1. Общее описание

Консольная программа на Python. В итоге она будет строить граф зависимостей пакета Maven (Java) и рисовать его.
Готовые менеджеры пакетов и библиотеки для получения зависимостей не используются: описание пакета скачивается
стандартным модулем `urllib` и разбирается стандартным модулем `xml.etree`.

Что умеет программа сейчас:

- Все настройки берутся из конфигурационного файла YAML. В командной строке указывается только путь к нему
  (`--config`), по умолчанию это `config.yaml` в текущей папке.
- Настроек шесть: имя пакета, URL репозитория (или путь к файлу тестового репозитория), режим работы
  с тестовым репозиторием, версия пакета, имя файла с картинкой графа и подстрока для фильтрации пакетов.
- Каждая настройка проверяется. Если есть ошибки, программа печатает их все сразу и завершается с кодом 1.
- Программа скачивает из репозитория Maven описание пакета (POM-файл) заданной версии и печатает все его прямые
  зависимости.

Вывод всех настроек в виде `ключ: значение` был нужен только на этапе 1, поэтому с этапа 2 его нет. Файл с
картинкой и фильтр пока не используются: они понадобятся на следующих этапах. Режим тестового репозитория тоже
появится позже (этап 3): сейчас при `test_mode: true` программа сообщает, что он ещё не поддерживается.

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

Файл тестового репозитория — `examples/test_repo.txt`. Пока проверяется только, что он есть. Читать его
программа будет с этапа 3: в каждой строке пакет и через двоеточие его зависимости, например `A: B C`.

### Как программа получает прямые зависимости

В репозитории Maven описание каждой версии пакета лежит в POM-файле (XML). Его адрес строится из имени и версии:

```
<репозиторий>/<groupId, точки заменены на />/<artifactId>/<версия>/<artifactId>-<версия>.pom
https://repo1.maven.org/maven2/org/apache/commons/commons-text/1.12.0/commons-text-1.12.0.pom
```

Прямые зависимости — это элементы `<dependency>` из раздела `<dependencies>` внутри `<project>`. Зависимости
плагинов (внутри `<build>`) к ним не относятся. Часто версия зависимости не написана прямо, поэтому программа
делает так же, как Maven:

1. **Родительские POM.** Если в POM есть `<parent>`, программа скачивает POM родителя, потом его родителя и так
   далее. Свойства, правила `<dependencyManagement>` и зависимости родителя наследуются, значения пакета важнее.
2. **Свойства.** Вместо `${имя}` подставляется значение из `<properties>` (своих или родительских) или встроенное
   свойство: `project.groupId`, `project.artifactId`, `project.version`, `project.parent.groupId`,
   `project.parent.version`. Свойства могут ссылаться на другие свойства.
3. **dependencyManagement.** Если у зависимости нет версии (или `scope`), они берутся из правил этого раздела.
4. **Импорт BOM.** Правило с `<type>pom</type>` и `<scope>import</scope>` — это BOM: программа скачивает его
   и добавляет его правила. Правила, записанные прямо, важнее импортированных.

Каждый POM-файл скачивается один раз. Если версию узнать неоткуда, вместо неё печатается `?`.

Выводятся все прямые зависимости пакета, в том числе тестовые. У каждой в скобках указан `scope`
(`compile`, `runtime`, `test`, `provided`, ...), если не указан — `compile`. Для необязательных зависимостей
(`<optional>true</optional>`) добавляется `optional`:

```
Direct dependencies of org.apache.commons:commons-text:1.12.0:
  org.apache.commons:commons-lang3:3.14.0 (compile)
  org.junit.jupiter:junit-jupiter:5.10.2 (test)
```

Программа выходит в интернет через `urllib`; если заданы переменные окружения `http_proxy` / `https_proxy`,
запросы идут через прокси.

### Ошибки

Все ошибки печатаются в поток ошибок (stderr). Ошибки конфига печатаются все сразу, каждая на своей строке,
в виде `ключ: что не так`.

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
| Нет такого пакета или версии в репозитории (или родителя, BOM) | `Repository error: not found: адрес` | 1 |
| Сервер не отвечает, нет сети | `Repository error: cannot download адрес: причина` | 1 |
| Сервер вернул другую ошибку HTTP | `Repository error: HTTP error код: адрес` | 1 |
| Скачанный файл не XML или не POM | `Repository error: invalid XML in ...`, `not a POM file ...` | 1 |
| Родительские POM ссылаются друг на друга, неполный `<parent>` | `Repository error: parent POMs form a cycle ...` | 1 |
| Включён тестовый режим | `Error: the test repository mode is not supported yet` | 1 |
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

`src/maven.py` — получение прямых зависимостей из репозитория Maven:

| Функция | Что делает |
|---|---|
| `RepositoryError` | Исключение: не удалось скачать или разобрать POM-файл |
| `Dependency` | Зависимость: `group`, `artifact`, `version`, `scope`, `optional`; `name` — это `groupId:artifactId` |
| `download(url)` | Скачивает файл (`urllib`); 404 — `not found`, другие ошибки — `RepositoryError` |
| `parse_pom(data, url)` | Разбирает XML, убирает пространство имён Maven, проверяет, что это `<project>` |
| `child_text(element, tag)` | Текст дочернего элемента или `None` |
| `coordinates(element)` | Тройка `(groupId, artifactId, version)` из элемента |
| `interpolate(value, properties)` | Подставляет свойства `${...}` (в том числе вложенные) |
| `read_properties(root)` | Свойства из `<properties>` |
| `project_properties(root)` | Встроенные свойства `project.groupId`, `project.version` и другие |
| `read_dependencies(element)` | Зависимости из `<dependencies>` внутри элемента (список словарей) |
| `resolve(dependency, properties)` | Подставляет свойства во все поля зависимости |
| `dependency_name(dependency)` | Имя `groupId:artifactId` зависимости-словаря |
| `is_bom_import(dependency)` | Это импорт BOM (`type` = `pom`, `scope` = `import`) |
| `make_dependency(raw, managed)` | Готовая `Dependency`: недостающие версия и `scope` из `dependencyManagement` |
| `chain_id(root)`, `coordinates_of(dependency)` | Координаты POM и зависимости (для сообщений и BOM) |
| `MavenRepository(url)` | Репозиторий по адресу; скачанные POM хранятся в памяти |
| `MavenRepository.pom_url(group, artifact, version)` | Адрес POM-файла |
| `MavenRepository.load_pom(group, artifact, version)` | Скачивает и разбирает POM (каждый файл один раз) |
| `MavenRepository.pom_chain(group, artifact, version)` | POM пакета и всех его родителей; ловит циклы |
| `MavenRepository.model(package_id, seen)` | Свойства, правила и зависимости с учётом родителей |
| `MavenRepository.managed_versions(managed, seen)` | Правила `dependencyManagement` вместе с импортированными BOM |
| `MavenRepository.direct_dependencies(group, artifact, version)` | Список прямых зависимостей пакета |

`src/main.py` — точка входа:

| Функция | Что делает |
|---|---|
| `parse_args(argv)` | Разбирает командную строку (только `--config`) |
| `print_config_errors(error)` | Печатает все ошибки конфига в stderr |
| `print_dependencies(settings)` | Скачивает описание пакета и печатает его прямые зависимости |
| `main(argv)` | Точка входа; возвращает код завершения |

## 3. Сборка, запуск и тесты

Нужен Python 3.9 или новее и библиотека PyYAML для чтения YAML. Сборка не требуется. Для работы с настоящим
репозиторием нужен интернет.

```
pip install -r requirements.txt
```

Запуск на Windows (из папки проекта):

```
.\run.bat
.\run.bat --config examples/real.yaml
```

Запуск на Linux/macOS: `sh run.sh [параметры]`. Или напрямую: `python src/main.py [параметры]`.

Тесты (из папки проекта). Интернет для них не нужен: вместо настоящего репозитория тесты подставляют свои
POM-файлы.

```
python -m unittest -v
```

Скрипты для проверки (папка `scripts/`) запускают программу с разными конфигами и печатают код завершения:

| Скрипт | Что проверяет |
|---|---|
| `test_dependencies.bat` | Этап 2: прямые зависимости четырёх пакетов, ошибки репозитория, тестовый режим, `--help` |
| `test_errors.bat` | Ошибки в конфиге для каждого параметра (`examples/errors/`), нет файла, неизвестный параметр |

```
.\scripts\test_dependencies.bat
.\scripts\test_errors.bat
```

Примеры конфигов:

| Файл | Что в нём |
|---|---|
| `config.yaml` | Конфиг по умолчанию: `commons-text 1.12.0` из Maven Central |
| `examples/real.yaml` | `guava 33.3.1-jre`: версии части зависимостей берутся из родительского POM, есть фильтр |
| `examples/jackson.yaml` | `jackson-databind 2.17.2`: версии из свойств родителей и из импортированного BOM |
| `examples/codec.yaml` | `commons-codec 1.10`: версия `1.10` без кавычек и пустой фильтр |
| `examples/test_mode.yaml` | Тестовый режим: пакет `A`, файл `examples/test_repo.txt` (заработает на этапе 3) |
| `examples/errors/*.yaml` | Ошибки в конфиге: по одной на каждый параметр и `many_errors.yaml` с несколькими сразу |
| `examples/repo_errors/*.yaml` | Верные конфиги, но ошибка в репозитории: нет пакета, нет версии, нет сервера |

## 4. Примеры использования

Конфиг по умолчанию (`.\run.bat`), commons-text 1.12.0:

```
Direct dependencies of org.apache.commons:commons-text:1.12.0:
  org.apache.commons:commons-lang3:3.14.0 (compile)
  org.junit.jupiter:junit-jupiter:5.10.2 (test)
  net.bytebuddy:byte-buddy:1.14.13 (test)
  net.bytebuddy:byte-buddy-agent:1.14.13 (test)
  org.assertj:assertj-core:3.25.3 (test)
  commons-io:commons-io:2.16.1 (test)
  org.mockito:mockito-inline:4.11.0 (test)
  org.graalvm.js:js:22.0.0.2 (test)
  org.graalvm.js:js-scriptengine:22.0.0.2 (test)
  org.apache.commons:commons-rng-simple:1.5 (test)
  org.openjdk.jmh:jmh-core:1.37 (test)
  org.openjdk.jmh:jmh-generator-annprocess:1.37 (test)
```

Версия `junit-jupiter` не написана в POM пакета: она взята из BOM `junit-bom 5.10.2`, который импортирует
родительский POM `commons-parent 69`. Версия `byte-buddy` записана через свойство `${commons.bytebuddy.version}`.

guava 33.3.1-jre (`.\run.bat --config examples/real.yaml`): у `jsr305`, `checker-qual`, `error_prone_annotations`
и `j2objc-annotations` в POM пакета нет версий, они взяты из `dependencyManagement` родительского POM `guava-parent`:

```
Direct dependencies of com.google.guava:guava:33.3.1-jre:
  com.google.guava:failureaccess:1.0.2 (compile)
  com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava (compile)
  com.google.code.findbugs:jsr305:3.0.2 (compile)
  org.checkerframework:checker-qual:3.43.0 (compile)
  com.google.errorprone:error_prone_annotations:2.28.0 (compile)
  com.google.j2objc:j2objc-annotations:3.0.0 (compile)
```

jackson-databind 2.17.2 (`.\run.bat --config examples/jackson.yaml`): версии `jackson-core` и
`jackson-annotations` записаны через свойства из родительских POM, версии `junit-jupiter` и `junit-vintage-engine` —
из BOM `junit-bom`, который импортирует родитель `jackson-base`, а `junit` унаследован от `jackson-base`
(поэтому он идёт последним):

```
Direct dependencies of com.fasterxml.jackson.core:jackson-databind:2.17.2:
  com.fasterxml.jackson.core:jackson-annotations:2.17.2 (compile)
  com.fasterxml.jackson.core:jackson-core:2.17.2 (compile)
  org.junit.vintage:junit-vintage-engine:5.10.2 (test)
  org.junit.jupiter:junit-jupiter:5.10.2 (test)
  org.assertj:assertj-core:3.24.2 (test)
  com.google.guava:guava-testlib:31.1-jre (test)
  javax.measure:jsr-275:0.9.1 (test)
  org.openjdk.jol:jol-core:0.16 (test)
  org.mockito:mockito-core:4.11.0 (test)
  org.mockito:mockito-inline:4.11.0 (test)
  net.bytebuddy:byte-buddy:1.14.13 (test)
  junit:junit:4.13.2 (test)
```

Нет такой версии (`.\run.bat --config examples/repo_errors/version_not_found.yaml`), код завершения 1:

```
Repository error: not found: https://repo1.maven.org/maven2/org/apache/commons/commons-text/0.0.1/...
```

Нет такого сервера (`.\run.bat --config examples/repo_errors/bad_host.yaml`), код завершения 1:

```
Repository error: cannot download https://no-such-host.invalid/maven2/org/apache/commons/commons-text/1.12.0/...
```

Ошибка в конфиге (`.\run.bat --config examples/errors/many_errors.yaml`), код завершения 1:

```
Config error in 'examples/errors/many_errors.yaml':
  unknown key 'color'
  package: 'guava': must look like groupId:artifactId (e.g. org.slf4j:slf4j-api)
  repository: 'ftp://repo1.maven.org/maven2/' is not an http(s) URL
  version: '33 beta' is not a valid version
  output: 'no_such_folder/graph.png': folder 'no_such_folder' does not exist
  filter: must be a single value, not a list or a mapping
```

## Структура репозитория

```
src/main.py           точка входа
src/settings.py       чтение и проверка конфига
src/maven.py          скачивание POM-файлов и прямые зависимости
tests/                тесты (unittest, без интернета)
scripts/              скрипты Windows для проверки
examples/             примеры конфигов и тестовый репозиторий;
                      errors/ — ошибки в конфиге, repo_errors/ — ошибки репозитория
config.yaml           конфиг по умолчанию
requirements.txt      зависимости (PyYAML)
run.bat, run.sh       запуск (Windows / Linux, macOS)
```
