# Визуализатор графа зависимостей Maven-пакетов (вариант 14)

Практическая работа № 2 по дисциплине «Конфигурационное управление» (РТУ МИРЭА, ИКБО-10-25).
Готовы все пять этапов. Каждый этап сохранён в истории отдельным коммитом:

| Этап | Что сделано | Коммит |
|---|---|---|
| 1. Минимальный прототип с конфигурацией | Настройки из YAML-файла, их проверка и вывод | `4394fe5` |
| 2. Сбор данных | Прямые зависимости пакета из репозитория Maven | `2225b84` |
| 3. Основные операции | Граф зависимостей (DFS с рекурсией), фильтр, циклы, тестовый репозиторий | `808a7d0` |
| 4. Дополнительные операции | Обратные зависимости пакета | `8d97567` |
| 5. Визуализация | Текст графа на языке D2, картинка PNG, сравнение с Maven | последний коммит |

## 1. Общее описание

Консольная программа на Python. Она строит граф зависимостей пакета Maven (Java) и рисует его. Готовые
менеджеры пакетов и библиотеки для получения зависимостей не используются: описание пакета скачивается
стандартным модулем `urllib` и разбирается стандартным модулем `xml.etree`.

### Что сделано на каждом этапе

**Этап 1. Минимальный прототип с конфигурацией.**

- Все настройки берутся из конфигурационного файла YAML. В командной строке указывается только путь к нему
  (`--config`), по умолчанию это `config.yaml` в текущей папке.
- Настроек шесть: имя пакета, URL репозитория (или путь к файлу тестового репозитория), режим работы
  с тестовым репозиторием, версия пакета, имя файла с картинкой графа и подстрока для фильтрации пакетов.
- Каждая настройка проверяется. Если есть ошибки, программа печатает их все сразу и завершается с кодом 1.
- Если ошибок нет, программа печатала все настройки в виде `ключ: значение`. По заданию это нужно было только
  на этапе 1, поэтому с этапа 2 этого вывода нет.

**Этап 2. Сбор данных.**

- Программа скачивает из репозитория Maven описание пакета (POM-файл) заданной версии и находит все его прямые
  зависимости. Учитываются родительские POM, свойства `${...}`, `dependencyManagement` и импорт BOM.
- На этапе 2 программа печатала все прямые зависимости со `scope`. По заданию это нужно было только на этапе 2,
  поэтому с этапа 3 вместо них печатается граф.

**Этап 3. Основные операции.**

- По прямым зависимостям строится граф зависимостей с учётом транзитивности: зависимости зависимостей и так
  далее. Граф обходится в глубину (DFS) с рекурсией.
- Пакеты, имя которых содержит подстроку из `filter`, не учитываются.
- Циклические зависимости обрабатываются: каждый пакет посещается один раз, а найденные циклы печатаются.
- Режим тестирования: вместо настоящего репозитория можно указать файл с описанием графа, где пакеты называются
  большими латинскими буквами. Работа показана на разных случаях тестового репозитория.

**Этап 4. Дополнительные операции.**

- Режим вывода обратных зависимостей (параметр `reverse_mode`): пакеты, которые зависят от заданного пакета,
  напрямую или через другие пакеты. Использовался тот же обход в глубину, что и на этапе 3, по графу
  с развёрнутыми рёбрами. Работа показана на разных случаях тестового репозитория.
- По заданию этот режим нужен был только на этапе 4, поэтому на этапе 5 он убран (вместе с параметром
  `reverse_mode`). Его можно посмотреть в коммите `8d97567`.

**Этап 5. Визуализация.**

- Граф выводится на экран в виде текста на языке диаграмм D2, а его картинка сохраняется в файл PNG (имя
  файла — параметр `output`).
- Показаны примеры для трёх пакетов: `spring-context`, `okhttp` и `guava`.
- Результаты сравнены с выводом штатного инструмента Maven (`mvn dependency:tree`), расхождения объяснены.

## 2. Описание функций и настроек

### Параметры командной строки

| Параметр | Что задаёт |
|---|---|
| `-c ПУТЬ`, `--config ПУТЬ` | Путь к конфигурационному файлу YAML (по умолчанию `config.yaml`) |
| `-h`, `--help` | Справка |

### Этап 1. Конфигурационный файл (YAML)

Все шесть ключей обязательны.

| Ключ | Что задаёт |
|---|---|
| `package` | Имя анализируемого пакета |
| `repository` | URL репозитория или путь к файлу тестового репозитория |
| `test_mode` | Режим работы с тестовым репозиторием (`true` / `false`) |
| `version` | Версия пакета (в тестовом режиме не используется, у пакетов-букв версий нет) |
| `output` | Имя сгенерированного файла с изображением графа (картинка PNG) |
| `filter` | Подстрока для фильтрации пакетов (может быть пустой — тогда фильтра нет) |

На этапе 4 был седьмой ключ `reverse_mode` (`true` / `false`) — режим обратных зависимостей. На этапе 5 его
убрали вместе с режимом, теперь это неизвестный ключ.

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

### Этап 2. Как программа получает прямые зависимости пакета Maven

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

Каждый POM-файл скачивается один раз (скачанные файлы хранятся в памяти). Программа выходит в интернет через
`urllib`; если заданы переменные окружения `http_proxy` / `https_proxy`, запросы идут через прокси.

### Этап 3. Как строится граф

Вершина графа — пакет: в обычном режиме `groupId:artifactId:версия`, в тестовом — имя из букв. Ребро `X -> Y`
значит, что пакет X зависит от пакета Y.

**Какие зависимости Maven попадают в граф.** Только те, которые Maven действительно подтягивает вместе
с пакетом: со `scope` `compile` или `runtime` и без `<optional>true</optional>`. Зависимости `test` и `provided`
нужны только при сборке самого пакета, а `optional` нужно подключать явно, поэтому в граф они не попадают.
Например, у commons-text 12 прямых зависимостей, но 11 из них тестовые, поэтому в графе у него одна
зависимость — `commons-lang3`.

**Обход в глубину (DFS) с рекурсией.** Функция `visit(пакет)`:

1. добавляет пакет в граф и в текущий путь (путь — это цепочка пакетов от начального до текущего);
2. получает зависимости пакета из репозитория и убирает те, имя которых содержит подстроку фильтра;
3. для каждой зависимости добавляет ребро и:
   - если зависимость уже есть **на текущем пути** — найден цикл, дальше по ней не идём;
   - если зависимость уже **посещена раньше** (через другую ветку) — второй раз не идём;
   - иначе рекурсивно вызывает `visit(зависимость)`;
4. убирает пакет из текущего пути.

Так каждый пакет обрабатывается один раз, даже если от него зависят несколько пакетов (например, «ромб»
A → B → D, A → C → D), а циклы (A → B → C → A, A → A) не приводят к бесконечному обходу.

**Фильтр.** Подстрока ищется в имени пакета: в обычном режиме это `groupId:artifactId` без версии, в тестовом —
имя из букв. Отфильтрованный пакет не попадает в граф, и его зависимости тоже не анализируются (если до них нельзя
дойти другим путём). Сам анализируемый пакет фильтр не убирает. Регистр букв важен.

**Если зависимость получить не удалось** (нет POM-файла в репозитории, неизвестная версия, нет пакета в тестовом
файле), пакет остаётся в графе без зависимостей, а в конце печатается предупреждение (`Warning: ...`). Если не
удалось получить сам анализируемый пакет — это ошибка.

**Глубина.** Рекурсия в Python ограничена (около 1000 вызовов), поэтому граф глубже примерно 1000 уровней
построить нельзя: программа сообщает об этом и завершается с кодом 1. У настоящих пакетов глубина намного меньше.

Пакет Maven может встретиться в графе в разных версиях (две зависимости просят разные версии одного пакета).
Тогда это разные вершины: программа показывает версии, записанные в POM-файлах. Сам Maven выбирает одну
версию — это видно при сравнении с Maven на этапе 5 (раздел 4).

### Этап 3. Тестовый репозиторий

Текстовый файл: в каждой строке пакет, двоеточие и его зависимости через пробел. Пакет без зависимостей пишется
как `D:`. Пустые строки и строки, которые начинаются с `#`, пропускаются. Повтор зависимости в строке
записывается один раз.

```
# Diamond: B and C both depend on D, D is visited only once
A: B C
B: D
C: D E
D:
E:
```

Ошибки в файле: строка без двоеточия, имя не из больших латинских букв, пакет описан два раза. В сообщении
указан номер строки. Пакет, который упомянут как зависимость, но не описан, даёт предупреждение (как пакет,
которого нет в настоящем репозитории).

Примеры файлов в `examples/test_repos/` и конфиги к ним в `examples/test_mode/`:

| Конфиг | Файл | Что показывает |
|---|---|---|
| `simple.yaml` | `simple.txt` | «Ромб»: D — общая зависимость B и C, посещается один раз |
| `filter.yaml` | `simple.txt` | Фильтр `D`: пакет D не анализируется |
| `cycle.yaml` | `cycle.txt` | Цикл из трёх пакетов A → B → C → A |
| `cycle_filter.yaml` | `cycle.txt` | Фильтр `C` разрывает цикл |
| `self_loop.yaml` | `self_loop.txt` | Пакет зависит сам от себя (A → A) |
| `complex.yaml` | `complex.txt` | Два цикла, общие пакеты; пакет H недостижим из A и в граф не попадает |
| `complex_from_d.yaml` | `complex.txt` | Тот же граф, но анализ начинается с пакета D |
| `missing.yaml` | `missing.txt` | Зависимость X не описана в файле: предупреждение, граф строится |
| `no_root.yaml` | `simple.txt` | Пакета Z нет в файле: ошибка |
| `bad_name.yaml` | `bad_name.txt` | Имя `c` не из больших букв: ошибка с номером строки |
| `bad_line.yaml` | `bad_line.txt` | Строка без двоеточия: ошибка с номером строки |

### Этап 4. Обратные зависимости (режим убран на этапе 5)

Обратные зависимости пакета — это пакеты, которые от него зависят: напрямую или через другие пакеты. На этапе 4
режим включался ключом `reverse_mode: true`.

**Как они искались.** Использовался тот же обход в глубину с рекурсией, что и на этапе 3 (`GraphBuilder`), только
рёбра графа были развёрнуты: если в файле написано `A: B` (A зависит от B), то в развёрнутом графе из B идёт ребро
в A. Обход развёрнутого графа от заданного пакета посещает все пакеты, которые от него зависят. Фильтр и циклы
работали так же, как на этапе 3.

**Только для тестового репозитория.** Чтобы развернуть рёбра, нужно знать все пакеты репозитория и их
зависимости. Тестовый файл описывает весь граф целиком, а в репозитории Maven каждый POM-файл знает только свои
зависимости — списка «кто зависит от этого пакета» там нет. Пришлось бы скачать все пакеты Maven Central, поэтому
`reverse_mode: true` вместе с `test_mode: false` было ошибкой в конфиге.

Для режима были функции `TestRepository.names()`, `TestRepository.reversed()` и `dependents(graph)`, конфиги
в `examples/reverse/` и скрипт `scripts/test_reverse.bat`. Всё это есть в коммите `8d97567`.

### Этап 5. Визуализация

**Текст на языке D2.** [D2](https://d2lang.com) — язык описания диаграмм. Программа записывает граф так:
сначала все пакеты в порядке обхода, по одному на строке, потом все рёбра в виде `"A" -> "B"` (A зависит от B).
Имена пакетов берутся в двойные кавычки, потому что точка и двоеточие в D2 — служебные знаки (без кавычек
`org.slf4j:slf4j-api` D2 понял бы как вложенные фигуры с подписью). Пакеты перечисляются отдельно, чтобы на
картинке был и пакет без зависимостей. Отфильтрованных пакетов в тексте нет, а рёбра циклов — обычные рёбра.

**Картинка PNG.** Картинку по тексту D2 рисует программа `d2` (её нужно установить, см. раздел 3). Программа
запускает `d2 --stdout-format png - -`: текст D2 передаётся через стандартный ввод, а готовая картинка PNG
приходит через стандартный вывод и сохраняется в файл `output`. Поэтому файл всегда в формате PNG, даже если
имя заканчивается не на `.png`. Сами картинки в репозиторий не добавляются (это бинарные файлы, они
в `.gitignore`); их создаёт скрипт `scripts/test_d2.bat`.

**Сравнение с Maven.** Штатный инструмент Maven для просмотра зависимостей — команда `mvn dependency:tree`
(плагин `maven-dependency-plugin`). Она работает с проектом, поэтому для каждого из трёх пакетов в папке
`examples/maven/` лежит маленький проект `pom.xml` с одной зависимостью — этим пакетом. Результаты и объяснение
расхождений — в разделе 4.

### Вывод программы

На каждом этапе программа печатала своё:

| Этап | Что печатала программа |
|---|---|
| 1 | Все настройки в виде `ключ: значение` |
| 2 | Прямые зависимости пакета со `scope` |
| 3 | Граф: пакеты по порядку обхода, под каждым его зависимости (`-> B`), итог, отфильтрованные пакеты, циклы |
| 4 | То же, а в режиме `reverse_mode` — обратные зависимости (`<- B`) и список зависящих пакетов |
| 5 | Граф текстом на D2, итог, отфильтрованные пакеты, циклы и имя сохранённой картинки |

Сейчас (этап 5) вывод такой (`.\run.bat --config examples/test_mode/cycle.yaml`):

```
D2 code of the dependency graph of A:
"A"
"B"
"C"
"D"
"A" -> "B"
"B" -> "C"
"C" -> "A"
"C" -> "D"
Packages: 4, dependencies: 4
Cycle: A -> B -> C -> A
PNG image saved to test_graph.png
```

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
| Нет анализируемого пакета или его версии в репозитории | `Repository error: not found: адрес` | 1 |
| Сервер не отвечает, нет сети | `Repository error: cannot download адрес: причина` | 1 |
| Сервер вернул другую ошибку HTTP | `Repository error: HTTP error код: адрес` | 1 |
| Скачанный файл не XML или не POM | `Repository error: invalid XML in ...`, `not a POM file ...` | 1 |
| Родительские POM ссылаются друг на друга, неполный `<parent>` | `Repository error: parent POMs form a cycle ...` | 1 |
| Нет анализируемого пакета в тестовом файле | `Repository error: package 'Z' not found in '...'` | 1 |
| Ошибка в тестовом файле | `Repository error: 'файл', line N: ...` | 1 |
| Граф слишком глубокий для рекурсии | `Error: the dependency graph is too deep for recursive DFS` | 1 |
| Программа `d2` не установлена (текст D2 напечатан) | `Image error: the d2 program is not found ...` | 1 |
| Программа `d2` завершилась с ошибкой | `Image error: d2 failed: сообщение d2` | 1 |
| Файл картинки нельзя записать | `Image error: cannot write '...': причина` | 1 |
| Нет зависимостей одного из пакетов графа (граф печатается) | `Warning: cannot get dependencies of ...` | 0 |
| Неизвестный параметр командной строки | `usage: ...` и описание ошибки | 2 |

Если режим `test_mode` указан неверно (или его нет), имя пакета и репозиторий не проверяются: без режима
непонятно, по каким правилам их проверять. Ошибки `Repository error` появились на этапе 2, `Error: ... too deep`
и ошибки тестового файла — на этапе 3, `Image error` — на этапе 5.

### Функции

`src/settings.py` — чтение и проверка конфига (этап 1):

| Функция | Что делает |
|---|---|
| `ConfigError` | Исключение: путь к конфигу и список всех ошибок |
| `read_yaml(path)` | Читает YAML-файл (все значения как текст), возвращает словарь; при ошибке — `ConfigError` |
| `parse_bool(value)` | `true`/`false` → `True`/`False`, иначе `None` |
| `text_error(value)` | Ошибка, если значение — список или словарь, или пустое |
| `check_test_mode(value)` | Проверяет режим `test_mode`: `true` или `false` |
| `check_package(value, test_mode)` | Проверяет имя пакета (зависит от режима) |
| `check_repository(value, test_mode)` | Проверяет URL или путь к тестовому репозиторию |
| `check_url(value)` | Адрес должен начинаться с `http://` или `https://` |
| `check_test_file(value)` | Файл тестового репозитория должен существовать |
| `check_version(value)` | Проверяет версию |
| `check_output(value)` | Проверяет имя файла с картинкой и папку для него |
| `check_filter(value)` | Проверяет подстроку для фильтрации |
| `find_errors(data)` | Проверяет все заданные параметры, собирает ошибки |
| `load_settings(path)` | Читает и проверяет конфиг, возвращает словарь настроек или бросает `ConfigError` |

`src/maven.py` — получение зависимостей из репозитория Maven (этап 2):

| Функция | Что делает |
|---|---|
| `RepositoryError` | Исключение: не удалось получить данные из репозитория |
| `Dependency` | Зависимость: `group`, `artifact`, `version`, `scope`, `optional` |
| `Dependency.name`, `Dependency.node` | Имя `groupId:artifactId` и вершина графа `groupId:artifactId:версия` |
| `Dependency.is_transitive` | Попадает ли зависимость в граф: `compile` или `runtime`, не `optional` (этап 3) |
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
| `MavenRepository.direct_dependencies(group, artifact, version)` | Список всех прямых зависимостей пакета |
| `MavenRepository.dependencies(node)` | Зависимости для графа (только транзитивные) в виде вершин (этап 3) |

`src/local_repo.py` — тестовый репозиторий (этап 3):

| Функция | Что делает |
|---|---|
| `TestRepository(path, packages)` | Тестовый репозиторий: `{пакет: [зависимости]}` |
| `TestRepository.load(path)` | Читает файл тестового репозитория |
| `TestRepository.dependencies(node)` | Зависимости пакета; если пакета нет в файле — `RepositoryError` |
| `parse_line(text, where)` | Разбирает строку `A: B C` в `("A", ["B", "C"])` |
| `parse_lines(lines, path)` | Разбирает все строки файла, пропускает пустые и комментарии |

`src/graph.py` — граф зависимостей (этап 3):

| Функция | Что делает |
|---|---|
| `package_name(node)` | Имя пакета без версии: `g:a:1.0` → `g:a`, `A` → `A` |
| `Graph` | Результат обхода: `edges` (рёбра в порядке обхода), `cycles`, `skipped`, `errors` |
| `Graph.edge_count()` | Число рёбер |
| `GraphBuilder(repository, text_filter)` | Построитель графа для любого репозитория с методом `dependencies` |
| `GraphBuilder.build(root)` | Строит граф от пакета `root` |
| `GraphBuilder.is_skipped(node)` | Имя пакета содержит подстроку фильтра |
| `GraphBuilder.children(node)` | Зависимости пакета без отфильтрованных; ошибки зависимостей запоминает |
| `GraphBuilder.visit(node)` | Рекурсивный обход в глубину (DFS), поиск циклов |
| `summary_lines(graph)` | Итог обхода: число пакетов и рёбер, отфильтрованные пакеты, циклы (этап 5) |

`src/diagram.py` — визуализация (этап 5):

| Функция | Что делает |
|---|---|
| `DiagramError` | Исключение: не удалось нарисовать или сохранить картинку |
| `quote(node)` | Имя пакета в двойных кавычках для D2 |
| `d2_text(graph)` | Текст графа на языке D2: все пакеты, потом все рёбра |
| `render_png(text)` | Запускает программу `d2`, возвращает картинку PNG (байты) |
| `save_png(text, path)` | Рисует картинку по тексту D2 и сохраняет её в файл |

`src/main.py` — точка входа:

| Функция | Что делает |
|---|---|
| `parse_args(argv)` | Разбирает командную строку (только `--config`) |
| `print_config_errors(error)` | Печатает все ошибки конфига в stderr |
| `open_repository(settings)` | Настоящий или тестовый репозиторий и начальный пакет |
| `show_graph(settings)` | Строит граф, печатает текст D2 и итог, сохраняет картинку PNG |
| `main(argv)` | Точка входа; возвращает код завершения |

## 3. Сборка, запуск и тесты

Нужен Python 3.9 или новее и библиотека PyYAML для чтения YAML. Сборка не требуется. Для работы с настоящим
репозиторием нужен интернет, для тестового режима — нет.

```
pip install -r requirements.txt
```

Для картинок (этап 5) нужна программа `d2` (проверено с версией 0.9.0, она рисует PNG сама, без браузера
и без интернета). Её можно скачать со страницы https://github.com/d2lang/d2/releases (для Windows —
`d2-v0.9.0-windows-amd64.tar.gz` или установщик `.msi`). Папку `bin` с файлом `d2.exe` нужно добавить
в переменную окружения `PATH`. Только для текущего окна cmd это можно сделать так (путь — куда распакован архив):

```
set PATH=%LOCALAPPDATA%\Programs\d2\d2-v0.9.0\bin;%PATH%
d2 --version
```

Без `d2` программа всё равно печатает текст графа на D2, но картинку не сохраняет (ошибка `Image error`, код 1).

Запуск на Windows (из папки проекта):

```
.\run.bat
.\run.bat --config examples/test_mode/complex.yaml
```

Запуск на Linux/macOS: `sh run.sh [параметры]`. Или напрямую: `python src/main.py [параметры]`.

Тесты (из папки проекта). Интернет и программа `d2` для них не нужны: вместо настоящего репозитория тесты
подставляют свои POM-файлы, а вместо запуска `d2` — готовый ответ. Один тест проверяет, что настоящая `d2`
понимает текст программы; он запускается, только если `d2` есть в `PATH`.

```
python -m unittest -v
```

| Файл тестов | Что проверяет |
|---|---|
| `tests/test_settings.py` | Этап 1: чтение и проверка конфига |
| `tests/test_maven.py` | Этап 2: POM-файлы, родители, свойства, BOM, ошибки репозитория |
| `tests/test_local_repo.py` | Этап 3: файл тестового репозитория |
| `tests/test_graph.py` | Этап 3: обход в глубину, циклы, фильтр |
| `tests/test_diagram.py` | Этап 5: текст D2, запуск `d2`, сохранение PNG |
| `tests/test_main.py` | Программа целиком: вывод, картинка, коды завершения |

Скрипты для проверки (папка `scripts/`) запускают программу с разными конфигами и печатают код завершения:

| Скрипт | Этап | Что проверяет |
|---|---|---|
| `test_errors.bat` | 1 | Ошибки в конфиге для каждого параметра (`examples/errors/`), нет файла, неизвестный параметр |
| `test_real_repo.bat` | 2, 3 | Графы пяти настоящих пакетов из Maven Central, ошибки репозитория |
| `test_test_repo.bat` | 3 | Все случаи тестового репозитория (перед каждым печатается файл графа) |
| `test_d2.bat` | 5 | Текст D2 и картинки PNG для трёх пакетов: `spring.png`, `okhttp.png`, `examples\guava.png` |
| `compare_maven.bat` | 5 | Дерево зависимостей тех же пакетов штатным инструментом Maven (`mvn dependency:tree`) |

```
.\scripts\test_errors.bat
.\scripts\test_real_repo.bat
.\scripts\test_test_repo.bat
.\scripts\test_d2.bat
.\scripts\compare_maven.bat
```

Для `compare_maven.bat` нужен Maven (команда `mvn` в `PATH`; подходит и Maven, встроенный в IntelliJ IDEA:
`plugins\maven\lib\maven3\bin\mvn.cmd`). Скрипт вызывает `maven-dependency-plugin` версии 3.11.0: обычное дерево
и дерево с `-Dverbose`, где видны пакеты, которые Maven отбросил. Если интернет идёт через прокси, его нужно
прописать в `settings.xml` Maven (раздел `<proxies>`): Java не читает переменные `http_proxy` / `https_proxy`.

Примеры конфигов для настоящего репозитория:

| Файл | Что в нём |
|---|---|
| `config.yaml` | Конфиг по умолчанию: `commons-text 1.12.0` |
| `examples/spring.yaml` | `spring-context 6.1.12`: несколько уровней транзитивных зависимостей |
| `examples/okhttp.yaml` | `okhttp 4.12.0`: две версии `kotlin-stdlib` приходят разными путями (этап 5) |
| `examples/real.yaml` | `guava 33.3.1-jre` с фильтром `annotations` |
| `examples/jackson.yaml` | `jackson-databind 2.17.2`: версии из свойств родителей и из импортированного BOM |
| `examples/codec.yaml` | `commons-codec 1.10`: версия `1.10` без кавычек, в графе нет зависимостей |
| `examples/errors/*.yaml` | Ошибки в конфиге: по одной на каждый параметр и `many_errors.yaml` с несколькими сразу |
| `examples/repo_errors/*.yaml` | Верные конфиги, но ошибка в репозитории: нет пакета, нет версии, нет сервера |
| `examples/maven/*/pom.xml` | Проекты для `mvn dependency:tree` (этап 5) |

## 4. Примеры использования

### Этап 1. Настройки

На этапе 1 программа печатала все настройки (коммит `4394fe5`, `.\run.bat`):

```
Settings from 'config.yaml':
  package: org.apache.commons:commons-text
  repository: https://repo1.maven.org/maven2/
  test_mode: false
  version: 1.12.0
  output: graph.png
  filter: ""
```

Проверка конфига работает и сейчас. Несколько ошибок сразу (`.\run.bat --config examples/errors/many_errors.yaml`),
код завершения 1:

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

### Этап 2. Прямые зависимости

На этапе 2 программа печатала прямые зависимости пакета (коммит `2225b84`, `.\run.bat`, commons-text 1.12.0).
Версия `junit-jupiter` не написана в POM пакета: она взята из BOM `junit-bom 5.10.2`, который импортирует
родительский POM `commons-parent 69`:

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

guava 33.3.1-jre (коммит `2225b84`, `.\run.bat --config examples/real.yaml`): у `jsr305`, `checker-qual`,
`error_prone_annotations` и `j2objc-annotations` в POM пакета нет версий, они взяты из `dependencyManagement`
родительского POM `guava-parent`:

```
Direct dependencies of com.google.guava:guava:33.3.1-jre:
  com.google.guava:failureaccess:1.0.2 (compile)
  com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava (compile)
  com.google.code.findbugs:jsr305:3.0.2 (compile)
  org.checkerframework:checker-qual:3.43.0 (compile)
  com.google.errorprone:error_prone_annotations:2.28.0 (compile)
  com.google.j2objc:j2objc-annotations:3.0.0 (compile)
```

Ошибки репозитория работают и сейчас. Нет такой версии
(`.\run.bat --config examples/repo_errors/version_not_found.yaml`), код завершения 1:

```
Repository error: not found: https://repo1.maven.org/maven2/org/apache/commons/commons-text/0.0.1/commons-text-0.0.1.pom
```

### Этап 3. Граф зависимостей

Так граф печатался на этапах 3 и 4 (коммит `808a7d0`). Сейчас тот же граф печатается текстом D2 (см. этап 5).

Транзитивные зависимости spring-context 6.1.12 (`.\run.bat --config examples/spring.yaml`). Пакет spring-core
нужен четырём пакетам, но посещается один раз (номер 4):

```
Dependency graph of org.springframework:spring-context:6.1.12:
  1. org.springframework:spring-context:6.1.12
       -> org.springframework:spring-aop:6.1.12
       -> org.springframework:spring-beans:6.1.12
       -> org.springframework:spring-core:6.1.12
       -> org.springframework:spring-expression:6.1.12
       -> io.micrometer:micrometer-observation:1.12.9
  2. org.springframework:spring-aop:6.1.12
       -> org.springframework:spring-beans:6.1.12
       -> org.springframework:spring-core:6.1.12
  3. org.springframework:spring-beans:6.1.12
       -> org.springframework:spring-core:6.1.12
  4. org.springframework:spring-core:6.1.12
       -> org.springframework:spring-jcl:6.1.12
  5. org.springframework:spring-jcl:6.1.12
  6. org.springframework:spring-expression:6.1.12
       -> org.springframework:spring-core:6.1.12
  7. io.micrometer:micrometer-observation:1.12.9
       -> io.micrometer:micrometer-commons:1.12.9
  8. io.micrometer:micrometer-commons:1.12.9
Packages: 8, dependencies: 11
Cycles: none
```

Тестовый репозиторий с двумя циклами (`.\run.bat --config examples/test_mode/complex.yaml`, файл
`examples/test_repos/complex.txt`). Пакет H недостижим из A, поэтому его нет в графе:

```
Dependency graph of A:
  1. A
       -> B
       -> C
  2. B
       -> D
  3. D
       -> B
       -> F
  4. F
       -> G
  5. G
       -> E
  6. E
       -> F
  7. C
       -> D
       -> E
Packages: 7, dependencies: 10
Cycle: B -> D -> B
Cycle: F -> G -> E -> F
```

Фильтр разрывает цикл (`.\run.bat --config examples/test_mode/cycle_filter.yaml`, цикл A → B → C → A, фильтр `C`):

```
Dependency graph of A:
  1. A
       -> B
  2. B
Packages: 2, dependencies: 1
Skipped by filter 'C':
  C
Cycles: none
```

Зависимость не описана в тестовом файле (`.\run.bat --config examples/test_mode/missing.yaml`), код завершения 0:

```
Dependency graph of A:
  1. A
       -> B
       -> X
  2. B
  3. X
Packages: 3, dependencies: 2
Cycles: none
Warning: cannot get dependencies of X: package 'X' not found in 'examples/test_repos/missing.txt'
```

Ошибка в тестовом файле (`.\run.bat --config examples/test_mode/bad_name.yaml`), код завершения 1 (так и сейчас):

```
Repository error: 'examples/test_repos/bad_name.txt', line 2: 'c' is not a name of capital Latin letters
```

### Этап 4. Обратные зависимости

Так режим работал на этапе 4 (коммит `8d97567`; посмотреть: `git checkout 8d97567`, вернуться: `git checkout main`).
Стрелка `<- B` под пакетом значит «B зависит от этого пакета».

Кто зависит от D в «ромбе» (`.\run.bat --config examples/reverse/simple.yaml`, файл `simple.txt`): B и C
напрямую, A через них:

```
Reverse dependencies of D:
  1. D
       <- B
       <- C
  2. B
       <- A
  3. A
  4. C
       <- A
Packages that depend on D: B, A, C
Cycles: none
```

Обратные зависимости F в графе с двумя циклами (`.\run.bat --config examples/reverse/complex.yaml`). При обходе
от A пакет H не попадал в граф, а здесь видно, что он зависит от F (H → A → B → D → F). F лежит в цикле
F → G → E → F, поэтому зависит сам от себя:

```
Reverse dependencies of F:
  1. F
       <- D
       <- E
  2. D
       <- B
       <- C
  3. B
       <- A
       <- D
  4. A
       <- H
  5. H
  6. C
       <- A
  7. E
       <- C
       <- G
  8. G
       <- F
Packages that depend on F: D, B, A, H, C, E, G, F
Cycle: D <- B <- D
Cycle: F <- E <- G <- F
```

### Этап 5. Визуализация трёх пакетов

Все три примера запускает `.\scripts\test_d2.bat`. Ниже — текст D2, который печатает программа; картинки
сохраняются в файлы из параметра `output`.

**1. spring-context 6.1.12** (`.\run.bat --config examples/spring.yaml`, картинка `spring.png`). На картинке
spring-context наверху, spring-jcl внизу; в spring-core входят четыре стрелки:

```
D2 code of the dependency graph of org.springframework:spring-context:6.1.12:
"org.springframework:spring-context:6.1.12"
"org.springframework:spring-aop:6.1.12"
"org.springframework:spring-beans:6.1.12"
"org.springframework:spring-core:6.1.12"
"org.springframework:spring-jcl:6.1.12"
"org.springframework:spring-expression:6.1.12"
"io.micrometer:micrometer-observation:1.12.9"
"io.micrometer:micrometer-commons:1.12.9"
"org.springframework:spring-context:6.1.12" -> "org.springframework:spring-aop:6.1.12"
"org.springframework:spring-context:6.1.12" -> "org.springframework:spring-beans:6.1.12"
"org.springframework:spring-context:6.1.12" -> "org.springframework:spring-core:6.1.12"
"org.springframework:spring-context:6.1.12" -> "org.springframework:spring-expression:6.1.12"
"org.springframework:spring-context:6.1.12" -> "io.micrometer:micrometer-observation:1.12.9"
"org.springframework:spring-aop:6.1.12" -> "org.springframework:spring-beans:6.1.12"
"org.springframework:spring-aop:6.1.12" -> "org.springframework:spring-core:6.1.12"
"org.springframework:spring-beans:6.1.12" -> "org.springframework:spring-core:6.1.12"
"org.springframework:spring-core:6.1.12" -> "org.springframework:spring-jcl:6.1.12"
"org.springframework:spring-expression:6.1.12" -> "org.springframework:spring-core:6.1.12"
"io.micrometer:micrometer-observation:1.12.9" -> "io.micrometer:micrometer-commons:1.12.9"
Packages: 8, dependencies: 11
Cycles: none
PNG image saved to spring.png
```

**2. okhttp 4.12.0** (`.\run.bat --config examples/okhttp.yaml`, картинка `okhttp.png`). okhttp сам зависит
от `kotlin-stdlib-jdk8:1.8.21`, а его зависимость okio-jvm — от `kotlin-stdlib-jdk8:1.9.10`. Поэтому в графе
две версии каждого пакета Kotlin, а `org.jetbrains:annotations:13.0` нужен обеим версиям `kotlin-stdlib`:

```
D2 code of the dependency graph of com.squareup.okhttp3:okhttp:4.12.0:
"com.squareup.okhttp3:okhttp:4.12.0"
"com.squareup.okio:okio:3.6.0"
"com.squareup.okio:okio-jvm:3.6.0"
"org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib-common:1.9.10"
"org.jetbrains:annotations:13.0"
"org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.21"
"org.jetbrains.kotlin:kotlin-stdlib:1.8.21"
"org.jetbrains.kotlin:kotlin-stdlib-common:1.8.21"
"org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.8.21"
"com.squareup.okhttp3:okhttp:4.12.0" -> "com.squareup.okio:okio:3.6.0"
"com.squareup.okhttp3:okhttp:4.12.0" -> "org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.21"
"com.squareup.okio:okio:3.6.0" -> "com.squareup.okio:okio-jvm:3.6.0"
"com.squareup.okio:okio-jvm:3.6.0" -> "org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.10"
"com.squareup.okio:okio-jvm:3.6.0" -> "org.jetbrains.kotlin:kotlin-stdlib-common:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.10" -> "org.jetbrains.kotlin:kotlin-stdlib:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.10" -> "org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib:1.9.10" -> "org.jetbrains.kotlin:kotlin-stdlib-common:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib:1.9.10" -> "org.jetbrains:annotations:13.0"
"org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.9.10" -> "org.jetbrains.kotlin:kotlin-stdlib:1.9.10"
"org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.21" -> "org.jetbrains.kotlin:kotlin-stdlib:1.8.21"
"org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.21" -> "org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.8.21"
"org.jetbrains.kotlin:kotlin-stdlib:1.8.21" -> "org.jetbrains.kotlin:kotlin-stdlib-common:1.8.21"
"org.jetbrains.kotlin:kotlin-stdlib:1.8.21" -> "org.jetbrains:annotations:13.0"
"org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.8.21" -> "org.jetbrains.kotlin:kotlin-stdlib:1.8.21"
Packages: 12, dependencies: 15
Cycles: none
PNG image saved to okhttp.png
```

**3. guava 33.3.1-jre с фильтром `annotations`** (`.\run.bat --config examples/real.yaml`, картинка
`examples/guava.png`). Два пакета, в имени которых есть `annotations`, не попали на картинку:

```
D2 code of the dependency graph of com.google.guava:guava:33.3.1-jre:
"com.google.guava:guava:33.3.1-jre"
"com.google.guava:failureaccess:1.0.2"
"com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava"
"com.google.code.findbugs:jsr305:3.0.2"
"org.checkerframework:checker-qual:3.43.0"
"com.google.guava:guava:33.3.1-jre" -> "com.google.guava:failureaccess:1.0.2"
"com.google.guava:guava:33.3.1-jre" -> "com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava"
"com.google.guava:guava:33.3.1-jre" -> "com.google.code.findbugs:jsr305:3.0.2"
"com.google.guava:guava:33.3.1-jre" -> "org.checkerframework:checker-qual:3.43.0"
Packages: 5, dependencies: 4
Skipped by filter 'annotations':
  com.google.errorprone:error_prone_annotations:2.28.0
  com.google.j2objc:j2objc-annotations:3.0.0
Cycles: none
PNG image saved to examples/guava.png
```

Граф тестового репозитория с циклом A → B → C → A (`.\run.bat --config examples/test_mode/cycle.yaml`, картинка
`test_graph.png`) показан выше, в разделе «Вывод программы». На картинке ребро цикла C → A идёт снизу вверх.

### Этап 5. Сравнение со штатным инструментом Maven

Деревья получены командой `.\scripts\compare_maven.bat` (Maven 3.9.9, `maven-dependency-plugin` 3.11.0). Ниже
вывод без префикса `[INFO]` и без строк о сборке. В дереве Maven пишет у пакета ещё тип (`jar`) и `scope`.

**1. spring-context 6.1.12.** Обычное дерево:

```
example:spring-context-tree:pom:1.0
\- org.springframework:spring-context:jar:6.1.12:compile
   +- org.springframework:spring-aop:jar:6.1.12:compile
   +- org.springframework:spring-beans:jar:6.1.12:compile
   +- org.springframework:spring-core:jar:6.1.12:compile
   |  \- org.springframework:spring-jcl:jar:6.1.12:compile
   +- org.springframework:spring-expression:jar:6.1.12:compile
   \- io.micrometer:micrometer-observation:jar:1.12.9:compile
      \- io.micrometer:micrometer-commons:jar:1.12.9:compile
```

С `-Dverbose`:

```
example:spring-context-tree:pom:1.0
\- org.springframework:spring-context:jar:6.1.12:compile
   +- org.springframework:spring-aop:jar:6.1.12:compile
   |  +- (org.springframework:spring-beans:jar:6.1.12:compile - omitted for duplicate)
   |  \- (org.springframework:spring-core:jar:6.1.12:compile - omitted for duplicate)
   +- org.springframework:spring-beans:jar:6.1.12:compile
   |  \- (org.springframework:spring-core:jar:6.1.12:compile - omitted for duplicate)
   +- org.springframework:spring-core:jar:6.1.12:compile
   |  \- org.springframework:spring-jcl:jar:6.1.12:compile
   +- org.springframework:spring-expression:jar:6.1.12:compile
   |  \- (org.springframework:spring-core:jar:6.1.12:compile - omitted for duplicate)
   \- io.micrometer:micrometer-observation:jar:1.12.9:compile
      \- io.micrometer:micrometer-commons:jar:1.12.9:compile
```

Пакеты и версии совпадают с графом программы (8 пакетов). Расхождение только в рёбрах: в обычном дереве Maven
их 7, а у программы 11. Дерево показывает каждый пакет один раз, поэтому четыре ребра
(spring-aop → spring-beans, spring-aop → spring-core, spring-beans → spring-core, spring-expression → spring-core)
в нём не видны. С `-Dverbose` они появляются с пометкой `omitted for duplicate` — это ровно те рёбра, которые
есть в графе D2.

**2. okhttp 4.12.0.** Обычное дерево:

```
example:okhttp-tree:pom:1.0
\- com.squareup.okhttp3:okhttp:jar:4.12.0:compile
   +- com.squareup.okio:okio:jar:3.6.0:compile
   |  \- com.squareup.okio:okio-jvm:jar:3.6.0:compile
   |     \- org.jetbrains.kotlin:kotlin-stdlib-common:jar:1.9.10:compile
   \- org.jetbrains.kotlin:kotlin-stdlib-jdk8:jar:1.8.21:compile
      +- org.jetbrains.kotlin:kotlin-stdlib:jar:1.8.21:compile
      |  \- org.jetbrains:annotations:jar:13.0:compile
      \- org.jetbrains.kotlin:kotlin-stdlib-jdk7:jar:1.8.21:compile
```

С `-Dverbose`:

```
example:okhttp-tree:pom:1.0
\- com.squareup.okhttp3:okhttp:jar:4.12.0:compile
   +- com.squareup.okio:okio:jar:3.6.0:compile
   |  \- com.squareup.okio:okio-jvm:jar:3.6.0:compile
   |     +- (org.jetbrains.kotlin:kotlin-stdlib-jdk8:jar:1.9.10:compile - omitted for conflict with 1.8.21)
   |     \- org.jetbrains.kotlin:kotlin-stdlib-common:jar:1.9.10:compile
   \- org.jetbrains.kotlin:kotlin-stdlib-jdk8:jar:1.8.21:compile
      +- org.jetbrains.kotlin:kotlin-stdlib:jar:1.8.21:compile
      |  +- (org.jetbrains.kotlin:kotlin-stdlib-common:jar:1.8.21:compile - omitted for conflict with 1.9.10)
      |  \- org.jetbrains:annotations:jar:13.0:compile
      \- org.jetbrains.kotlin:kotlin-stdlib-jdk7:jar:1.8.21:compile
         \- (org.jetbrains.kotlin:kotlin-stdlib:jar:1.8.21:compile - omitted for duplicate)
```

Здесь расхождение большое: у программы 12 пакетов, у Maven 8. Причина — конфликт версий. Из одного пакета
в проект попадает только одна версия, и Maven выбирает ту, что **ближе к корню** (nearest wins):

- `kotlin-stdlib-jdk8`: версия 1.8.21 на глубине 1 (okhttp → jdk8), версия 1.9.10 на глубине 3
  (okhttp → okio → okio-jvm → jdk8). Maven берёт 1.8.21. Отброшенная версия 1.9.10 тянула за собой
  `kotlin-stdlib:1.9.10` и `kotlin-stdlib-jdk7:1.9.10`, поэтому в дереве Maven их тоже нет (у отброшенного пакета
  Maven не показывает зависимости даже с `-Dverbose`).
- `kotlin-stdlib-common`: обе версии на одинаковой глубине 3 (okhttp → okio → okio-jvm → common и
  okhttp → jdk8 → stdlib → common). При равной глубине побеждает версия, которая встретилась первой, а в POM
  okhttp пакет okio объявлен раньше `kotlin-stdlib-jdk8`. Поэтому Maven взял `kotlin-stdlib-common:1.9.10`,
  хотя остальные пакеты Kotlin у него версии 1.8.21.

Программа конфликты версий не разрешает: она показывает, какие версии записаны в каждом POM-файле. Поэтому
в графе обе версии, каждая со своими зависимостями, а на картинке видно, откуда пришла каждая версия.

**3. guava 33.3.1-jre.** Обычное дерево (без фильтра):

```
example:guava-tree:pom:1.0
\- com.google.guava:guava:jar:33.3.1-jre:compile
   +- com.google.guava:failureaccess:jar:1.0.2:compile
   +- com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
   +- com.google.code.findbugs:jsr305:jar:3.0.2:compile
   +- org.checkerframework:checker-qual:jar:3.43.0:compile
   +- com.google.errorprone:error_prone_annotations:jar:2.28.0:compile
   \- com.google.j2objc:j2objc-annotations:jar:3.0.0:compile
```

С `"-Dexcludes=*:*annotations*"` (не показывать пакеты, в `artifactId` которых есть `annotations`):

```
example:guava-tree:pom:1.0
\- com.google.guava:guava:jar:33.3.1-jre:compile
   +- com.google.guava:failureaccess:jar:1.0.2:compile
   +- com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
   +- com.google.code.findbugs:jsr305:jar:3.0.2:compile
   \- org.checkerframework:checker-qual:jar:3.43.0:compile
```

Без фильтра у Maven те же 6 зависимостей, что и у программы до фильтра (их видно в списке `Skipped by filter`).
С `-Dexcludes` дерево Maven совпадает с графом программы с фильтром `annotations`. Но фильтры работают
по-разному: программа ищет подстроку во всём имени `groupId:artifactId` и не анализирует зависимости
отфильтрованного пакета, а Maven сравнивает шаблон по частям (здесь только `artifactId`) и лишь скрывает пакет
при выводе. У guava отфильтрованные пакеты своих зависимостей не имеют, поэтому результат одинаковый.

**Итог: почему результаты расходятся.**

1. **Граф и дерево (spring-context).** Программа строит граф и рисует все рёбра. Maven печатает дерево, где
   каждый пакет встречается один раз, а повторы видны только с `-Dverbose` (`omitted for duplicate`). Поэтому
   у программы больше рёбер, а пакеты те же.
2. **Конфликт версий (okhttp).** Maven оставляет одну версию каждого пакета: ближайшую к корню, а при равной
   глубине — ту, что встретилась первой (`omitted for conflict`). Программа показывает все версии, записанные
   в POM-файлах, поэтому у неё больше пакетов.
3. **Смешанные версии у Maven (okhttp).** Правило «ближайшая побеждает» применяется к каждому пакету отдельно,
   поэтому Maven взял `kotlin-stdlib-common:1.9.10` вместе с `kotlin-stdlib:1.8.21`.
4. **Фильтр (guava).** Результат совпал, но программа убирает пакет из анализа по подстроке имени, а `-Dexcludes`
   у Maven только скрывает пакет при выводе по шаблону.
5. **Тип и `scope`.** Maven пишет у пакета `jar` и `compile`. Программа их не печатает: в граф и так попадают
   только зависимости `compile` и `runtime` без `optional`.

Есть и расхождения, которых в этих трёх примерах нет, но они возможны. Программа не учитывает `<exclusions>`
у зависимостей, а Maven убирает исключённые пакеты. Графы с циклами из тестового репозитория сравнить с Maven
нельзя: Maven работает только с настоящими пакетами, а файл тестового репозитория — это формат самой программы.

## Структура репозитория

```
src/main.py           точка входа
src/settings.py       чтение и проверка конфига (этап 1)
src/maven.py          скачивание POM-файлов и зависимости пакетов Maven (этап 2)
src/local_repo.py     тестовый репозиторий из файла (этап 3)
src/graph.py          граф зависимостей: обход в глубину с рекурсией (этап 3)
src/diagram.py        текст графа на языке D2 и картинка PNG (этап 5)
tests/                тесты (unittest, без интернета)
scripts/              скрипты Windows для проверки
examples/             примеры конфигов; errors/ — ошибки в конфиге, repo_errors/ — ошибки репозитория,
                      test_repos/ — файлы тестового репозитория, test_mode/ — конфиги для графа,
                      maven/ — проекты pom.xml для сравнения с mvn dependency:tree
config.yaml           конфиг по умолчанию
requirements.txt      зависимости (PyYAML)
run.bat, run.sh       запуск (Windows / Linux, macOS)
```
