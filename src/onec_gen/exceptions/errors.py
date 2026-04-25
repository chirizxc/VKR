from dataclasses import dataclass
from pathlib import Path

from onec_gen.exceptions.base import OneCGenError

_ = {
    "eq": False,
    "repr": False,
    "match_args": False,
    "slots": True,
}


@dataclass(**_)
class PresetsFileReadError(OneCGenError):
    path: Path
    details: str

    def __str__(self) -> str:
        return f"Ошибка чтения файла пресетов {self.path}: {self.details}"


@dataclass(**_)
class PresetsDecodeError(OneCGenError):
    path: Path
    details: str

    def __str__(self) -> str:
        return f"Некорректный YAML в файле пресетов {self.path}: {self.details}"


@dataclass(**_)
class PresetsLoadError(OneCGenError):
    path: Path
    details: str

    def __str__(self) -> str:
        return f"Ошибка загрузки пресетов из файла {self.path}: {self.details}"


class EmptyDirectoryPathError(OneCGenError):
    def __str__(self) -> str:
        return "Путь до каталога не должен быть пустым."


@dataclass(**_)
class OneCNotFoundError(OneCGenError):
    path: str | Path | None = None

    def __str__(self) -> str:
        if self.path is None:
            return "1С не найдена автоматически. Попробуйте указать путь через --1c-path."
        return (
            f"Не удалось найти 1С по пути: {self.path}. "
            "Укажите путь до 1cv8.exe, 1cv8t.exe или каталога bin "
            "через --1c-path."
        )


@dataclass(**_)
class OneCBatchModeNotSupportedError(OneCGenError):
    path: Path

    def __str__(self) -> str:
        return (
            f"Найденный исполняемый файл 1С не подходит для batch-сборки: {self.path}. "
            "Для CLI-сценариев генерации и сборки .cf нужен batch-пригодный "
            "исполняемый файл платформы: 1cv8.exe или 1cv8t.exe. "
            "Укажите путь до такого бинаря через --1c-path или каталога bin."
        )


@dataclass(**_)
class ConfigFileReadError(OneCGenError):
    path: Path
    details: str

    def __str__(self) -> str:
        return f"Ошибка чтения файла {self.path}: {self.details}"


@dataclass(**_)
class ConfigJsonDecodeError(OneCGenError):
    path: Path
    details: str

    def __str__(self) -> str:
        return f"Некорректный JSON в файле {self.path}: {self.details}"


@dataclass(**_)
class ConfigSchemaValidationError(OneCGenError):
    details: str

    def __str__(self) -> str:
        return f"Ошибка валидации JSON Schema: {self.details}"


@dataclass(**_)
class ConfigLoadError(OneCGenError):
    details: str

    def __str__(self) -> str:
        return f"Ошибка загрузки описания конфигурации: {self.details}"


@dataclass(**_)
class ConfigGenerationError(OneCGenError):
    details: str

    def __str__(self) -> str:
        return f"Ошибка генерации конфигурации: {self.details}"


@dataclass(**_)
class OneCBuildError(OneCGenError):
    details: str

    def __str__(self) -> str:
        return f"Ошибка сборки конфигурации: {self.details}"
