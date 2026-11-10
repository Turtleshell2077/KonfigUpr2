"""Визуализация графа: текст на языке диаграмм D2 и картинка PNG.

Каждый пакет графа записывается в D2 отдельной строкой, каждое ребро —
строкой «"A" -> "B"» (A зависит от B). Имена пакетов берутся в кавычки,
потому что точка и двоеточие в D2 — служебные знаки.

Картинку по тексту рисует программа d2 (https://d2lang.com), она должна
быть установлена и доступна через PATH. Программа получает текст через
stdin и возвращает PNG через stdout, файл сохраняется здесь.
"""

import subprocess

D2_COMMAND = ("d2", "--stdout-format", "png", "-", "-")
D2_SITE = "https://d2lang.com"


class DiagramError(Exception):
    """Не удалось нарисовать или сохранить картинку графа."""


def quote(node):
    """Имя пакета в двойных кавычках для D2."""
    text = node.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def d2_text(graph):
    """Текст графа на языке D2: сначала все пакеты, потом все рёбра.

    Пакеты перечисляются отдельно, чтобы на картинке был и пакет без
    зависимостей. Отфильтрованных пакетов в графе нет, а рёбра циклов
    рисуются как обычные рёбра.
    """
    lines = [quote(node) for node in graph.edges]
    for node, children in graph.edges.items():
        lines.extend(f"{quote(node)} -> {quote(child)}"
                     for child in children)
    return "\n".join(lines) + "\n"


def render_png(text):
    """Запускает d2 и возвращает картинку PNG (байты)."""
    try:
        result = subprocess.run(D2_COMMAND, input=text.encode("utf-8"),
                                capture_output=True, check=False)
    except FileNotFoundError:
        raise DiagramError(f"the d2 program is not found (install it "
                           f"from {D2_SITE} and add it to PATH)")
    except OSError as error:
        raise DiagramError(f"cannot run d2: {error}")
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace")
        raise DiagramError("d2 failed: " + " ".join(message.split()))
    return result.stdout


def save_png(text, path):
    """Рисует граф по тексту D2 и сохраняет PNG в файл path."""
    image = render_png(text)
    try:
        with open(path, "wb") as file:
            file.write(image)
    except OSError as error:
        raise DiagramError(f"cannot write '{path}': {error.strerror}")
