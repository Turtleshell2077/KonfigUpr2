"""Визуализатор графа зависимостей Maven-пакетов (вариант 14).

Этап 1: параметры читаются из YAML-файла, проверяются и выводятся
на экран в виде «ключ: значение».
"""

import argparse
import sys

from settings import ConfigError, load_settings, settings_lines

DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1


def parse_args(argv=None):
    """Разбирает командную строку: в ней только путь к конфигу."""
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer for Maven packages")
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG,
        help=f"path to the YAML config file (default: {DEFAULT_CONFIG})")
    return parser.parse_args(argv)


def print_errors(error):
    """Печатает все ошибки конфига в поток ошибок."""
    print(f"Config error in '{error.path}':", file=sys.stderr)
    for message in error.messages:
        print(f"  {message}", file=sys.stderr)


def main(argv=None):
    """Точка входа: читает конфиг и печатает все параметры."""
    args = parse_args(argv)
    try:
        settings = load_settings(args.config)
    except ConfigError as error:
        print_errors(error)
        return EXIT_CONFIG_ERROR
    print(f"Settings from '{args.config}':")
    for line in settings_lines(settings):
        print(f"  {line}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
