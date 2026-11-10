"""Чтение и проверка настроек из конфигурационного файла YAML."""

import os
import re
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None

KEYS = ("package", "repository", "test_mode", "reverse_mode", "version",
        "output", "filter")
FLAGS = ("test_mode", "reverse_mode")
NAME_PART = r"[A-Za-z0-9_.-]+"
MAVEN_NAME = re.compile(rf"{NAME_PART}:{NAME_PART}")
TEST_NAME = re.compile(r"[A-Z]+")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")
URL_SCHEMES = ("http", "https")
BOOLEANS = {"true": True, "false": False}


class ConfigError(Exception):
    """Ошибка в конфиге: путь к файлу и список сообщений."""

    def __init__(self, path, messages):
        """Запоминает путь к конфигу и все найденные ошибки."""
        super().__init__(f"{path}: {'; '.join(messages)}")
        self.path = path
        self.messages = messages


def read_yaml(path):
    """Читает YAML-файл и возвращает словарь «ключ: значение».

    Все значения читаются как текст (BaseLoader), поэтому версия 1.10
    остаётся строкой «1.10», а не превращается в число 1.1.
    """
    if yaml is None:
        raise ConfigError(path, ["PyYAML is not installed "
                                 "(pip install -r requirements.txt)"])
    try:
        with open(path, encoding="utf-8-sig") as file:
            data = yaml.load(file, Loader=yaml.BaseLoader)
    except OSError as error:
        raise ConfigError(path, [f"cannot read the file: {error.strerror}"])
    except UnicodeDecodeError:
        raise ConfigError(path, ["the file is not UTF-8 text"])
    except yaml.YAMLError as error:
        text = " ".join(str(error).split())
        raise ConfigError(path, [f"invalid YAML: {text}"])
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(path, ["the file must contain 'key: value' pairs"])
    return data


def parse_bool(value):
    """Строка true/false (в любом регистре) -> True/False, иначе None."""
    if isinstance(value, str):
        return BOOLEANS.get(value.lower())
    return None


def text_error(value):
    """Ошибка, если значение не строка (а список или словарь) или пустое."""
    if not isinstance(value, str):
        return "must be a single value, not a list or a mapping"
    if not value.strip():
        return "the value is empty"
    return None


def check_flag(value):
    """Режим (test_mode, reverse_mode): только true или false."""
    if parse_bool(value) is None:
        return f"'{value}': must be true or false"
    return None


def check_package(value, test_mode):
    """Имя пакета: groupId:artifactId или большие буквы в тестовом режиме."""
    error = text_error(value)
    if error:
        return error
    if test_mode and not TEST_NAME.fullmatch(value):
        return (f"'{value}': in test mode the name must be capital "
                "Latin letters (A, B, ...)")
    if not test_mode and not MAVEN_NAME.fullmatch(value):
        return (f"'{value}': must look like groupId:artifactId "
                "(e.g. org.slf4j:slf4j-api)")
    return None


def check_url(value):
    """Адрес репозитория должен начинаться с http:// или https://."""
    parts = urlparse(value)
    if parts.scheme not in URL_SCHEMES or not parts.netloc:
        return f"'{value}' is not an http(s) URL"
    return None


def check_test_file(value):
    """Файл тестового репозитория должен существовать."""
    if not os.path.exists(value):
        return f"test repository file '{value}' not found"
    if not os.path.isfile(value):
        return f"'{value}' is not a file"
    return None


def check_repository(value, test_mode):
    """URL репозитория или путь к файлу (в тестовом режиме)."""
    error = text_error(value)
    if error:
        return error
    if test_mode:
        return check_test_file(value)
    return check_url(value)


def check_version(value):
    """Версия пакета: буквы, цифры и знаки . - _ +"""
    error = text_error(value)
    if error:
        return error
    if not VERSION.fullmatch(value):
        return f"'{value}' is not a valid version"
    return None


def check_output(value):
    """Имя файла для картинки графа: не папка, и папка для него есть."""
    error = text_error(value)
    if error:
        return error
    if os.path.isdir(value):
        return f"'{value}' is a folder"
    folder = os.path.dirname(value) or "."
    if not os.path.isdir(folder):
        return f"'{value}': folder '{folder}' does not exist"
    return None


def check_filter(value):
    """Подстрока для фильтрации: строка (пустая — фильтра нет)."""
    if not isinstance(value, str):
        return "must be a single value, not a list or a mapping"
    return None


def find_errors(data):
    """Проверяет заданные параметры, возвращает строки «ключ: ошибка».

    Имя пакета и репозиторий проверяются по-разному в зависимости
    от режима, поэтому без верного test_mode они не проверяются.
    Обратные зависимости можно искать только в тестовом репозитории:
    в репозитории Maven нет списка пакетов, которые зависят от пакета.
    """
    checks = {"test_mode": check_flag, "reverse_mode": check_flag,
              "version": check_version, "output": check_output,
              "filter": check_filter}
    errors = {key: check(data[key]) for key, check in checks.items()
              if key in data}
    test_mode = parse_bool(data.get("test_mode"))
    if test_mode is not None:
        for key, check in (("package", check_package),
                           ("repository", check_repository)):
            if key in data:
                errors[key] = check(data[key], test_mode)
    if test_mode is False and parse_bool(data.get("reverse_mode")):
        errors["reverse_mode"] = ("works only with the test repository "
                                  "(test_mode: true)")
    return [f"{key}: {errors[key]}" for key in KEYS if errors.get(key)]


def load_settings(path):
    """Читает конфиг и проверяет его; при ошибках бросает ConfigError."""
    data = read_yaml(path)
    errors = [f"unknown key '{key}'" for key in data if key not in KEYS]
    errors += [f"{key}: the key is required" for key in KEYS
               if key not in data]
    errors += find_errors(data)
    if errors:
        raise ConfigError(path, errors)
    settings = {key: data[key] for key in KEYS}
    for key in FLAGS:
        settings[key] = parse_bool(data[key])
    return settings
