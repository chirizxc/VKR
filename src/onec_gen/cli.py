import argparse
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any, TextIO

import questionary
from questionary.prompts.common import Choice

from onec_gen.builder import build_config
from onec_gen.consts import KBI_MESSAGE, RE_PATTERN, SELECT_INSTRUCTION
from onec_gen.detect import resolve_onec_binary
from onec_gen.exceptions import (
    EmptyDirectoryPathError,
    OneCGenError,
)
from onec_gen.generator import default_generated_path, generate_config
from onec_gen.models import ConfigSpec
from onec_gen.presets import (
    TemplatePreset,
    build_config_spec_from_preset,
    find_presets,
    list_presets,
)
from onec_gen.select import select_with_compact_answer

logger = logging.getLogger(__name__)


class InteractiveCli:
    def run(self) -> Path:
        logger.debug("Запущен интерактивный поиск пресетов")
        query = _ask_text(
            "Введите описание для поиска шаблона конфигурации:",
            default="",
        )
        presets = find_presets(query)
        if not presets:
            _write_line(f"""По запросу "{query or 'пустой запрос'}" ничего не найдено""")
            presets = list_presets()

        selected_preset = _select_preset_interactively(presets)
        config = build_config_spec_from_preset(selected_preset)
        onec_binary = resolve_onec_binary(None)
        output_path = _select_output_path_interactively(selected_preset)
        return _build_cf_from_preset(
            preset=selected_preset,
            config=config,
            output_path=output_path,
            onec_binary=onec_binary,
        )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    _configure_logging(verbose=args.verbose)

    try:
        logger.debug("Аргументы CLI разобраны: %s", args)
        return _dispatch(args)
    except OneCGenError as exc:
        logger.debug("Ожидаемая ошибка CLI: %s", exc)
        _write_line(str(exc), stream=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="1c-gen-cli",
        description="CLI для генерации и сборки шаблонных конфигураций 1С.",
    )
    parser.set_defaults(handler=_handle_interactive)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Включить подробный вывод логов.",
    )

    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser(
        "search",
        help="Найти пресеты по текстовому запросу.",
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Текстовый запрос для фильтрации доступных пресетов.",
    )
    search_parser.set_defaults(handler=_handle_search)
    return parser


def _dispatch(args: argparse.Namespace) -> int:
    handler = args.handler
    logger.debug("Выбран обработчик команды: %s", handler.__name__)
    return handler(args)


def _handle_interactive(_: argparse.Namespace) -> int:
    built_path = InteractiveCli().run()
    _write_line("")
    _write_line(f"Файл шаблона сохранен по пути: {built_path}")
    return 0


def _handle_search(args: argparse.Namespace) -> int:
    logger.debug("Выполняю поиск пресетов по запросу: %s", args.query)
    presets = find_presets(args.query)
    if not presets:
        _write_line("Совпадений не найдено.")
        _write_line("")
        _write_line("Доступные шаблоны:")
        _print_presets(list_presets())
        return 1
    _print_presets(presets)
    return 0


def _build_cf_from_preset(
    *,
    preset: TemplatePreset,
    config: ConfigSpec,
    output_path: Path,
    onec_binary: Path,
) -> Path:
    logger.debug("Собираю .cf из пресета: %s", preset.id)
    with tempfile.TemporaryDirectory(prefix="onec-gen-preset-") as temporary_directory:
        source_path = default_generated_path(Path(temporary_directory), config)
        generate_config(
            config,
            source_path,
            onec_binary=onec_binary,
        )
        build_config(
            source_path=source_path,
            output_path=output_path,
            onec_binary=onec_binary,
            config=config,
            dry_run=False,
        )
    return output_path.expanduser().resolve()


def _select_preset_interactively(presets: tuple[TemplatePreset, ...]) -> TemplatePreset:
    max_title_length = max(len(preset.title) for preset in presets)
    selected_preset = select_with_compact_answer(
        "Выберите подходящий шаблон:",
        choices=[
            Choice(
                title=_format_preset_choice_title(
                    preset,
                    max_title_length=max_title_length,
                ),
                value=preset,
            )
            for preset in presets
        ],
        answer_formatter=_format_selected_preset_answer,
    ).ask(kbi_msg=KBI_MESSAGE)
    if selected_preset is None:
        raise KeyboardInterrupt
    logger.debug("Выбран пресет: %s", selected_preset.id)
    return selected_preset


def _format_preset_choice_title(
    preset: TemplatePreset,
    *,
    max_title_length: int,
) -> str:
    padded_title = preset.title.ljust(max_title_length)
    return f"{padded_title} | {preset.summary}"


def _format_selected_preset_answer(preset: Any) -> str:
    if not isinstance(preset, TemplatePreset):
        return str(preset)
    return f"{preset.title} | {preset.summary}"


def _select_output_path_interactively(preset: TemplatePreset) -> Path:
    choice = questionary.select(
        "Куда сохранить итоговый .cf файл?",
        choices=(
            questionary.Choice("В текущую директорию", value="current"),
            questionary.Choice("Указать каталог вручную", value="custom"),
        ),
        instruction=SELECT_INSTRUCTION,
        use_indicator=True,
    ).ask(kbi_msg=KBI_MESSAGE)
    if choice is None:
        raise KeyboardInterrupt

    if choice == "current":
        base_directory = Path.cwd()
    else:
        raw_path = _ask_path("Введите путь до каталога для сохранения .cf файла:")
        if not raw_path:
            raise EmptyDirectoryPathError
        base_directory = Path(raw_path).expanduser()

    return base_directory / _preset_cf_file_name(preset)


def _preset_cf_file_name(preset: TemplatePreset) -> str:
    parts = RE_PATTERN.findall(preset.title)
    compact_name = "".join(_capitalize_name_part(part) for part in parts)
    if not compact_name:
        compact_name = "Конфигурация"
    return f"Шаблон{compact_name}.cf"


def _capitalize_name_part(value: str) -> str:
    return value[:1].upper() + value[1:]


def _print_presets(presets: tuple[TemplatePreset, ...]) -> None:
    for index, preset in enumerate(presets, start=1):
        _write_line(f"{index}. {preset.title} [{preset.id}]")
        _write_line(f"   {preset.summary}")


def _ask_text(message: str, *, default: str) -> str:
    value = questionary.text(
        message,
        default=default,
    ).ask(kbi_msg=KBI_MESSAGE)
    if value is None:
        raise KeyboardInterrupt
    return value.strip()


def _ask_path(message: str) -> str:
    value = questionary.path(message).ask(kbi_msg=KBI_MESSAGE)
    if value is None:
        raise KeyboardInterrupt
    return value.strip()


def _write_line(message: str, *, stream: TextIO = sys.stdout) -> None:
    stream.write(f"{message}\n")


def _configure_logging(*, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )
