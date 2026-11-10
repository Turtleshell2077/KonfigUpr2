# Визуализатор графа зависимостей Maven-пакетов (вариант 14)

Практическая работа № 2 по дисциплине «Конфигурационное управление» (РТУ МИРЭА, ИКБО-10-25).
Готовы этапы 1 (минимальный прототип с конфигурацией), 2 (сбор данных), 3 (основные операции)
и 4 (дополнительные операции).

## 1. Общее описание

Консольная программа на Python. Она строит граф зависимостей пакета Maven (Java), а в итоге будет его рисовать.
Готовые менеджеры пакетов и библиотеки для получения зависимостей не используются: описание пакета скачивается
стандартным модулем `urllib` и разбирается стандартным модулем `xml.etree`.

Что умеет программа сейчас:

- Все настройки берутся из конфигурационного файла YAML. В командной строке указывается только путь к нему
  (`--config`), по умолчанию это `config.yaml` в текущей папке.
- Настроек семь: имя пакета, URL репозитория (или путь к файлу тестового репозитория), режим работы
  с тестовым репозиторием, режим обратных зависимостей (добавлен на этапе 4), версия пакета, имя файла
  с картинкой графа и подстрока для фильтрации пакетов. Каждая настройка проверяется; если есть ошибки,
  программа печатает их все сразу и завершается с кодом 1.
- Программа скачивает из репозитория Maven описание пакета (POM-файл) заданной версии и находит его прямые
  зависимости (этап 2).
- По прямым зависимостям строится граф зависимостей с учётом транзитивности: зависимости зависимостей и так
  далее. Граф обходится в глубину (DFS) с рекурсией (этап 3).
- Пакеты, имя которых содержит подстроку из `filter`, не учитываются.
- Циклические зависимости обрабатываются: каждый пакет посещается один раз, а найденные циклы печатаются.
- Режим тестирования: вместо настоящего репозитория можно указать файл с описанием графа, где пакеты называются
  большими латинскими буквами.
- Режим обратных зависимостей (этап 4): программа выводит пакеты, которые зависят от заданного пакета (напрямую
  или через другие пакеты). Используется тот же обход в глубину, что и на этапе 3.

Вывод всех настроек был нужен только на этапе 1, а вывод прямых зависимостей — только на этапе 2, поэтому сейчас
программа печатает граф. Файл с картинкой (`output`) пока не создаётся: он понадобится на этапе 5.

## 2. Описание функций и настроек

### Параметры командной строки

| Параметр | Что задаёт |
|---|---|
| `-c ПУТЬ`, `--config ПУТЬ` | Путь к конфигурационному файлу YAML (по умолчанию `config.yaml`) |
| `-h`, `--help` | Справка |

### Конфигурационный файл (YAML)

Все семь ключей обязательны.

| Ключ | Что задаёт |
|---|---|
| `package` | Имя анализируемого пакета |
| `repository` | URL репозитория или путь к файлу тестового репозитория |
| `test_mode` | Режим работы с тестовым репозиторием (`true` / `false`) |
| `reverse_mode` | Режим вывода обратных зависимостей (`true` / `false`), только с `test_mode: true` |
| `version` | Версия пакета (в тестовом режиме не используется, у пакетов-букв версий нет) |
| `output` | Имя сгенерированного файла с изображением графа |
| `filter` | Подстрока для фильтрации пакетов (может быть пустой — тогда фильтра нет) |

Пример (это файл `config.yaml` из корня проекта):

```yaml
package: org.apache.commons:commons-text
repository: https://repo1.maven.org/maven2/
test_mode: false
reverse_mode: false
version: 1.12.0
output: graph.png
filter: ""
```

Как проверяются значения:

- `package` — в обычном режиме имя пакета Maven в виде `groupId:artifactId` (буквы, цифры, `.`, `-`, `_`),
  например `org.slf4j:slf4j-api`. В тестовом режиме пакеты называются большими латинскими буквами: `A`, `B`, `ABC`.
- `repository` — в обычном режиме адрес, который начинается с `http://` или `https://` (например, Maven Central
  `https://repo1.maven.org/maven2/`). В тестовом режиме это путь к файлу, и файл должен существовать.
- `test_mode` и `reverse_mode` — только `true` или `false` (регистр не важен). `reverse_mode: true` можно только
  вместе с `test_mode: true` (почему — в разделе про обратные зависимости).
- `version` — не пустая, из букв, цифр и знаков `.`, `-`, `_`, `+` (например `2.0.16`, `33.3.1-jre`).
- `output` — не пустое имя файла; это не должна быть папка, а папка, в которой будет файл, должна существовать.
- `filter` — одна строка (не список); пустая строка значит, что фильтра нет.

Ещё правила:

- Неизвестный ключ — ошибка (так ловятся опечатки, например `pakage` вместо `package`).
- Все значения читаются как текст, поэтому кавычки не нужны: `version: 1.10` так и остаётся `1.10`
  (обычный YAML прочитал бы это как число `1.1`).
- Относительные пути (`repository` в тестовом режиме, `output`) считаются от текущей папки.

### Как программа получает прямые зависимости пакета Maven

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

### Как строится граф (этап 3)

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
Тогда это разные вершины: программа показывает версии, записанные в POM-файлах. Сам Maven при сборке выбрал бы
одну версию.

### Тестовый репозиторий

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

### Обратные зависимости (этап 4)

Обратные зависимости пакета — это пакеты, которые от него зависят: напрямую или через другие пакеты. Режим
включается ключом `reverse_mode: true`.

**Как они ищутся.** Используется тот же обход в глубину с рекурсией, что и на этапе 3 (`GraphBuilder`), только
рёбра графа развёрнуты: если в файле написано `A: B` (A зависит от B), то в развёрнутом графе из B идёт ребро
в A. Обход развёрнутого графа от заданного пакета посещает все пакеты, которые от него зависят. Фильтр и циклы
работают так же, как на этапе 3: отфильтрованный пакет не учитывается (и пакеты, которые зависят от заданного
только через него, не находятся), а если заданный пакет лежит в цикле, он зависит сам от себя.

**Только для тестового репозитория.** Чтобы развернуть рёбра, нужно знать все пакеты репозитория и их
зависимости. Тестовый файл описывает весь граф целиком, а в репозитории Maven каждый POM-файл знает только свои
зависимости — списка «кто зависит от этого пакета» там нет. Пришлось бы скачать все пакеты Maven Central, поэтому
`reverse_mode: true` вместе с `test_mode: false` — ошибка в конфиге.

Пакет, который в файле упомянут только как зависимость (не описан отдельной строкой), тоже можно задать: от него
зависят те, кто его упоминает. Если пакета в файле нет совсем — ошибка.

Вывод похож на граф этапа 3, но стрелка `<- B` под пакетом значит «B зависит от этого пакета». В конце —
список всех найденных пакетов (`.\run.bat --config examples/reverse/simple.yaml`, файл `simple.txt`):

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

Конфиги в `examples/reverse/` (файлы те же, что для этапа 3, из `examples/test_repos/`):

| Конфиг | Пакет | Что показывает |
|---|---|---|
| `simple.yaml` | D в `simple.txt` | От D зависят B и C напрямую и A через них |
| `nobody.yaml` | A в `simple.txt` | От верхнего пакета никто не зависит: `(none)` |
| `filter.yaml` | D в `simple.txt` | Фильтр `B`: A всё равно найден, но только через C |
| `cycle.yaml` | A в `cycle.txt` | A лежит в цикле A → B → C → A, поэтому от A зависят C, B и сам A |
| `self_loop.yaml` | A в `self_loop.txt` | A зависит сам от себя |
| `complex.yaml` | F в `complex.txt` | От F зависят все 8 пакетов, даже H, до которого нельзя дойти от A |
| `complex_filter.yaml` | F в `complex.txt` | Фильтр `D`: B зависит от F только через D, поэтому не найден |
| `not_described.yaml` | X в `missing.txt` | X не описан в файле, но A от него зависит |
| `no_package.yaml` | Z в `simple.txt` | Пакета Z нет в файле: ошибка |

### Вывод

Пакеты пронумерованы в порядке обхода в глубину, под каждым — его зависимости (рёбра графа). Дальше идут
число пакетов и рёбер, отфильтрованные пакеты (если есть) и найденные циклы:

```
Dependency graph of A:
  1. A
       -> B
  2. B
       -> C
  3. C
       -> A
       -> D
  4. D
Packages: 4, dependencies: 4
Cycle: A -> B -> C -> A
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
| Режим не `true`/`false` | `test_mode: '...': must be true or false` (так же `reverse_mode`) | 1 |
| Обратные зависимости для настоящего репозитория | `reverse_mode: works only with the test repository ...` | 1 |
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
| Нет зависимостей одного из пакетов графа (граф печатается) | `Warning: cannot get dependencies of ...` | 0 |
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
| `check_flag(value)` | Проверяет режим (`test_mode`, `reverse_mode`): `true` или `false` |
| `check_package(value, test_mode)` | Проверяет имя пакета (зависит от режима) |
| `check_repository(value, test_mode)` | Проверяет URL или путь к тестовому репозиторию |
| `check_url(value)` | Адрес должен начинаться с `http://` или `https://` |
| `check_test_file(value)` | Файл тестового репозитория должен существовать |
| `check_version(value)` | Проверяет версию |
| `check_output(value)` | Проверяет имя файла с картинкой и папку для него |
| `check_filter(value)` | Проверяет подстроку для фильтрации |
| `find_errors(data)` | Проверяет все заданные параметры (и `reverse_mode` вместе с `test_mode`), собирает ошибки |
| `load_settings(path)` | Читает и проверяет конфиг, возвращает словарь настроек или бросает `ConfigError` |

`src/maven.py` — получение зависимостей из репозитория Maven:

| Функция | Что делает |
|---|---|
| `RepositoryError` | Исключение: не удалось получить данные из репозитория |
| `Dependency` | Зависимость: `group`, `artifact`, `version`, `scope`, `optional` |
| `Dependency.name`, `Dependency.node` | Имя `groupId:artifactId` и вершина графа `groupId:artifactId:версия` |
| `Dependency.is_transitive` | Попадает ли зависимость в граф: `compile` или `runtime`, не `optional` |
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
| `MavenRepository.dependencies(node)` | Зависимости для графа (только транзитивные) в виде вершин |

`src/local_repo.py` — тестовый репозиторий:

| Функция | Что делает |
|---|---|
| `TestRepository(path, packages)` | Тестовый репозиторий: `{пакет: [зависимости]}` |
| `TestRepository.load(path)` | Читает файл тестового репозитория |
| `TestRepository.dependencies(node)` | Зависимости пакета; если пакета нет в файле — `RepositoryError` |
| `TestRepository.names()` | Все пакеты файла: описанные и упомянутые как зависимости |
| `TestRepository.reversed()` | Репозиторий с развёрнутыми рёбрами (для обратных зависимостей) |
| `parse_line(text, where)` | Разбирает строку `A: B C` в `("A", ["B", "C"])` |
| `parse_lines(lines, path)` | Разбирает все строки файла, пропускает пустые и комментарии |

`src/graph.py` — граф зависимостей:

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
| `dependents(graph)` | Пакеты, которые зависят от начального (для обратного графа) |
| `summary_line(graph, reverse)` | Итоговая строка: число пакетов и рёбер или список зависящих пакетов |
| `graph_lines(graph, reverse)` | Строки для вывода графа (`->`) или обратных зависимостей (`<-`) |

`src/main.py` — точка входа:

| Функция | Что делает |
|---|---|
| `parse_args(argv)` | Разбирает командную строку (только `--config`) |
| `print_config_errors(error)` | Печатает все ошибки конфига в stderr |
| `open_repository(settings)` | Настоящий или тестовый репозиторий (в обратном режиме — развёрнутый) и пакет |
| `print_graph(settings)` | Строит граф и печатает его, затем предупреждения |
| `main(argv)` | Точка входа; возвращает код завершения |

## 3. Сборка, запуск и тесты

Нужен Python 3.9 или новее и библиотека PyYAML для чтения YAML. Сборка не требуется. Для работы с настоящим
репозиторием нужен интернет, для тестового режима — нет.

```
pip install -r requirements.txt
```

Запуск на Windows (из папки проекта):

```
.\run.bat
.\run.bat --config examples/test_mode/complex.yaml
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
| `test_test_repo.bat` | Этап 3: все случаи тестового репозитория (перед каждым печатается файл графа) |
| `test_reverse.bat` | Этап 4: обратные зависимости на разных случаях тестового репозитория |
| `test_real_repo.bat` | Этап 3: графы пяти настоящих пакетов из Maven Central, ошибки репозитория |
| `test_errors.bat` | Ошибки в конфиге для каждого параметра (`examples/errors/`), нет файла, неизвестный параметр |

```
.\scripts\test_test_repo.bat
.\scripts\test_reverse.bat
.\scripts\test_real_repo.bat
.\scripts\test_errors.bat
```

Примеры конфигов для настоящего репозитория:

| Файл | Что в нём |
|---|---|
| `config.yaml` | Конфиг по умолчанию: `commons-text 1.12.0` |
| `examples/spring.yaml` | `spring-context 6.1.12`: несколько уровней транзитивных зависимостей |
| `examples/real.yaml` | `guava 33.3.1-jre` с фильтром `annotations` |
| `examples/jackson.yaml` | `jackson-databind 2.17.2`: версии из свойств родителей и из импортированного BOM |
| `examples/codec.yaml` | `commons-codec 1.10`: версия `1.10` без кавычек, в графе нет зависимостей |
| `examples/errors/*.yaml` | Ошибки в конфиге: по одной на каждый параметр и `many_errors.yaml` с несколькими сразу |
| `examples/repo_errors/*.yaml` | Верные конфиги, но ошибка в репозитории: нет пакета, нет версии, нет сервера |

## 4. Примеры использования

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

guava с фильтром `annotations` (`.\run.bat --config examples/real.yaml`):

```
Dependency graph of com.google.guava:guava:33.3.1-jre:
  1. com.google.guava:guava:33.3.1-jre
       -> com.google.guava:failureaccess:1.0.2
       -> com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
       -> com.google.code.findbugs:jsr305:3.0.2
       -> org.checkerframework:checker-qual:3.43.0
  2. com.google.guava:failureaccess:1.0.2
  3. com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
  4. com.google.code.findbugs:jsr305:3.0.2
  5. org.checkerframework:checker-qual:3.43.0
Packages: 5, dependencies: 4
Skipped by filter 'annotations':
  com.google.errorprone:error_prone_annotations:2.28.0
  com.google.j2objc:j2objc-annotations:3.0.0
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

Ошибка в тестовом файле (`.\run.bat --config examples/test_mode/bad_name.yaml`), код завершения 1:

```
Repository error: 'examples/test_repos/bad_name.txt', line 2: 'c' is not a name of capital Latin letters
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

Обратные зависимости для настоящего репозитория (`.\run.bat --config examples/errors/reverse_real.yaml`),
код завершения 1:

```
Config error in 'examples/errors/reverse_real.yaml':
  reverse_mode: works only with the test repository (test_mode: true)
```

## Структура репозитория

```
src/main.py           точка входа
src/settings.py       чтение и проверка конфига
src/maven.py          скачивание POM-файлов и зависимости пакетов Maven
src/local_repo.py     тестовый репозиторий из файла
src/graph.py          граф зависимостей: обход в глубину с рекурсией
tests/                тесты (unittest, без интернета)
scripts/              скрипты Windows для проверки
examples/             примеры конфигов; errors/ — ошибки в конфиге, repo_errors/ — ошибки репозитория,
                      test_repos/ — файлы тестового репозитория, test_mode/ — конфиги для графа,
                      reverse/ — конфиги для обратных зависимостей
config.yaml           конфиг по умолчанию
requirements.txt      зависимости (PyYAML)
run.bat, run.sh       запуск (Windows / Linux, macOS)
```
