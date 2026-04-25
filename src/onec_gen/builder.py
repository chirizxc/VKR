import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from onec_gen.detect import detect_ibcmd_binary
from onec_gen.exceptions import OneCBuildError
from onec_gen.models import ConfigSpec

logger = logging.getLogger(__name__)


class OneCCommandExecutor:
    def run(
        self,
        command: list[str],
        *,
        step_name: str,
        log_path: Path | None = None,
    ) -> None:
        logger.debug("Запуск шага 1С: %s", step_name)
        logger.debug("Команда: %s", command)
        completed_process = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed_process.returncode == 0:
            return

        stdout = completed_process.stdout.strip()
        stderr = completed_process.stderr.strip()
        rendered_command = subprocess.list2cmdline(command)
        log_details = _read_optional_log(log_path)
        msg = (
            f"Шаг 1С завершился с ошибкой: {step_name}. "
            f"Код возврата: {completed_process.returncode}. "
            f"Команда: {rendered_command}. "
            f"STDOUT: {stdout or '<пусто>'} "
            f"STDERR: {stderr or '<пусто>'}"
        )
        if log_details is not None:
            msg += f" LOG: {log_details}"
        raise OneCBuildError(msg)


_command_executor = OneCCommandExecutor()


def build_config(
    source_path: Path,
    output_path: Path,
    onec_binary: Path,
    config: ConfigSpec,
    *,
    dry_run: bool,
) -> str:
    resolved_source_path = source_path.expanduser().resolve()
    resolved_output_path = output_path.expanduser().resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("Нормализован путь к источнику: %s", resolved_source_path)
    logger.debug("Нормализован путь к результату: %s", resolved_output_path)

    source_kind = _detect_source_kind(resolved_source_path)
    command_preview = _command_preview(
        source_path=resolved_source_path,
        output_path=resolved_output_path,
        onec_binary=onec_binary,
        source_kind=source_kind,
    )
    logger.info("Подготовлен сценарий сборки для проекта: %s", config.project.name)

    if dry_run:
        return _build_summary(
            title="Dry-run: сборка не запускалась.",
            config=config,
            source_path=resolved_source_path,
            output_path=resolved_output_path,
            extra_lines=(
                f"Путь к 1С: {onec_binary}",
                f"Команда: {command_preview}",
            ),
        )

    if source_kind == "cf":
        shutil.copy2(resolved_source_path, resolved_output_path)
        logger.info("Готовый cf-файл скопирован: %s", resolved_output_path)
        return _build_summary(
            title="Исходный cf-файл скопирован в целевой путь.",
            config=config,
            source_path=resolved_source_path,
            output_path=resolved_output_path,
        )

    if source_kind == "config-dump":
        _build_from_config_dump(
            source_path=resolved_source_path,
            output_path=resolved_output_path,
            onec_binary=onec_binary,
        )
        return _build_summary(
            title="Сборка cf завершена.",
            config=config,
            source_path=resolved_source_path,
            output_path=resolved_output_path,
        )

    if source_kind == "generated-xml":
        _build_empty_cf(
            output_path=resolved_output_path,
            onec_binary=onec_binary,
        )
        return _build_summary(
            title="Собран минимальный пустой cf-файл.",
            config=config,
            source_path=resolved_source_path,
            output_path=resolved_output_path,
            extra_lines=(
                "Он откроется в 1С, но пока не содержит объектов из JSON-описания.",
            ),
        )

    msg = (
        f"Неподдерживаемый источник для сборки: {resolved_source_path}. "
        "Используйте .cf, каталог файловой выгрузки конфигурации, "
        "или XML, сгенерированный текущим CLI."
    )
    raise OneCBuildError(msg)


def _build_empty_cf(
    *,
    output_path: Path,
    onec_binary: Path,
) -> None:
    ibcmd_path = detect_ibcmd_binary(onec_binary)
    if ibcmd_path is not None:
        _build_empty_cf_with_ibcmd(
            output_path=output_path,
            ibcmd_path=ibcmd_path,
        )
        return

    logger.info("ibcmd не найден, использую Designer для сборки пустого cf.")
    _build_empty_cf_with_designer(
        output_path=output_path,
        onec_binary=onec_binary,
    )


def _build_empty_cf_with_ibcmd(*, output_path: Path, ibcmd_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="onec-gen-empty-") as temporary_directory:
        server_data_path = Path(temporary_directory) / "server-data"
        infobase_path = Path(temporary_directory) / "ib"
        server_data_path.mkdir(parents=True, exist_ok=True)

        _command_executor.run(
            [
                str(ibcmd_path),
                "infobase",
                "create",
                f"--data={server_data_path}",
                f"--db-path={infobase_path}",
                "--create-database",
            ],
            step_name="создание пустой информационной базы через ibcmd",
        )
        _command_executor.run(
            [
                str(ibcmd_path),
                "config",
                "save",
                f"--data={server_data_path}",
                f"--db-path={infobase_path}",
                str(output_path),
            ],
            step_name="сохранение пустой конфигурации в cf через ibcmd",
        )


def _build_empty_cf_with_designer(*, output_path: Path, onec_binary: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="onec-gen-empty-") as temporary_directory:
        infobase_path = Path(temporary_directory) / "ib"

        _run_designer_create_infobase(
            onec_binary=onec_binary,
            infobase_path=infobase_path,
            step_name="создание пустой информационной базы через Designer",
        )
        _run_designer_dump_cfg(
            onec_binary=onec_binary,
            infobase_path=infobase_path,
            output_path=output_path,
            step_name="сохранение пустой конфигурации в cf через Designer",
        )


def _build_from_config_dump(
    *,
    source_path: Path,
    output_path: Path,
    onec_binary: Path,
) -> None:
    ibcmd_path = detect_ibcmd_binary(onec_binary)
    if ibcmd_path is not None:
        _build_from_config_dump_with_ibcmd(
            source_path=source_path,
            output_path=output_path,
            ibcmd_path=ibcmd_path,
        )
        return

    logger.info(
        "ibcmd не найден, использую Designer для сборки cf. "
        "Проект поддерживает только учебный сценарий сборки.",
    )
    _build_from_config_dump_with_designer(
        source_path=source_path,
        output_path=output_path,
        onec_binary=onec_binary,
    )


def _build_from_config_dump_with_ibcmd(
    *,
    source_path: Path,
    output_path: Path,
    ibcmd_path: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="onec-gen-ib-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        server_data_path = temporary_root / "server-data"
        infobase_path = temporary_root / "ib"
        server_data_path.mkdir(parents=True, exist_ok=True)

        _command_executor.run(
            [
                str(ibcmd_path),
                "infobase",
                "create",
                f"--data={server_data_path}",
                f"--db-path={infobase_path}",
                "--create-database",
                f"--import={source_path}",
                "--apply",
                "--force",
            ],
            step_name=(
                "импорт файловой выгрузки "
                "в временную информационную базу через ibcmd"
            ),
        )
        _command_executor.run(
            [
                str(ibcmd_path),
                "config",
                "save",
                f"--data={server_data_path}",
                f"--db-path={infobase_path}",
                str(output_path),
            ],
            step_name="сохранение конфигурации в cf через ibcmd",
        )


def _build_from_config_dump_with_designer(
    *,
    source_path: Path,
    output_path: Path,
    onec_binary: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="onec-gen-designer-") as temporary_directory:
        infobase_path = Path(temporary_directory) / "ib"
        designer_log_path = Path(temporary_directory) / "designer-load.log"

        _run_designer_create_infobase(
            onec_binary=onec_binary,
            infobase_path=infobase_path,
            step_name="создание временной информационной базы через Designer",
        )
        _command_executor.run(
            [
                str(onec_binary),
                "DESIGNER",
                f"/F{infobase_path}",
                "/DisableStartupDialogs",
                "/LoadConfigFromFiles",
                str(source_path),
                "/UpdateDBCfg",
                "/Out",
                str(designer_log_path),
            ],
            step_name="загрузка конфигурации из файлов через Designer",
            log_path=designer_log_path,
        )
        _run_designer_dump_cfg(
            onec_binary=onec_binary,
            infobase_path=infobase_path,
            output_path=output_path,
            step_name="сохранение конфигурации в cf через Designer",
        )


def _run_designer_create_infobase(
    *,
    onec_binary: Path,
    infobase_path: Path,
    step_name: str,
) -> None:
    _command_executor.run(
        [
            str(onec_binary),
            "CREATEINFOBASE",
            _create_infobase_connection_string(infobase_path),
            "/DisableStartupDialogs",
        ],
        step_name=step_name,
    )


def _run_designer_dump_cfg(
    *,
    onec_binary: Path,
    infobase_path: Path,
    output_path: Path,
    step_name: str,
) -> None:
    with tempfile.TemporaryDirectory(
        prefix="onec-gen-designer-log-",
    ) as temporary_directory:
        log_path = Path(temporary_directory) / "designer-dump.log"
        _command_executor.run(
            [
                str(onec_binary),
                "DESIGNER",
                f"/F{infobase_path}",
                "/DisableStartupDialogs",
                "/DumpCfg",
                str(output_path),
                "/Out",
                str(log_path),
            ],
            step_name=step_name,
            log_path=log_path,
        )


def _read_optional_log(log_path: Path | None) -> str | None:
    if log_path is None or not log_path.is_file():
        return None

    log_text = log_path.read_text(encoding="utf-8", errors="replace").strip()
    if not log_text:
        return "<пусто>"
    return log_text


def _create_infobase_connection_string(infobase_path: Path) -> str:
    return f"File={infobase_path};"


def _build_summary(
    *,
    title: str,
    config: ConfigSpec,
    source_path: Path,
    output_path: Path,
    extra_lines: tuple[str, ...] = (),
) -> str:
    lines = [
        title,
        f"Проект: {config.project.name} ({config.project.namespace})",
        f"Источник: {source_path}",
        f"Выходной файл: {output_path}",
        *extra_lines,
    ]
    return "\n".join(lines)


def _detect_source_kind(source_path: Path) -> str:
    if not source_path.exists():
        msg = f"Исходный путь не найден: {source_path}"
        raise OneCBuildError(msg)

    if source_path.is_file() and source_path.suffix.lower() == ".cf":
        return "cf"

    if source_path.is_dir() and (source_path / "Configuration.xml").exists():
        return "config-dump"

    if source_path.is_file() and source_path.suffix.lower() == ".xml":
        return "generated-xml"

    msg = (
        f"Неподдерживаемый источник для сборки: {source_path}. "
        "Используйте .cf, каталог файловой выгрузки конфигурации, "
        "или XML, сгенерированный текущим CLI."
    )
    raise OneCBuildError(msg)


def _command_preview(
    *,
    source_path: Path,
    output_path: Path,
    onec_binary: Path,
    source_kind: str,
) -> str:
    ibcmd_path = detect_ibcmd_binary(onec_binary)
    if source_kind == "cf":
        return f'copy "{source_path}" "{output_path}"'

    if source_kind == "config-dump":
        return _config_dump_command_preview(
            source_path=source_path,
            output_path=output_path,
            onec_binary=onec_binary,
            ibcmd_path=ibcmd_path,
        )

    if source_kind == "generated-xml":
        return _generated_xml_command_preview(
            output_path=output_path,
            onec_binary=onec_binary,
            ibcmd_path=ibcmd_path,
        )

    return f'"{onec_binary}" <неизвестный сценарий сборки>'


def _config_dump_command_preview(
    *,
    source_path: Path,
    output_path: Path,
    onec_binary: Path,
    ibcmd_path: Path | None,
) -> str:
    if ibcmd_path is not None:
        return (
            f'"{ibcmd_path}" infobase create --data="<temp_data>" '
            f'--db-path="<temp_ib>" --create-database '
            f'--import="{source_path}" --apply --force && '
            f'"{ibcmd_path}" config save '
            f'--data="<temp_data>" --db-path="<temp_ib>" "{output_path}"'
        )

    return (
        f'"{onec_binary}" CREATEINFOBASE File="<temp_ib>" && '
        f'"{onec_binary}" DESIGNER /F"<temp_ib>" '
        f'/LoadConfigFromFiles "{source_path}" /UpdateDBCfg && '
        f'"{onec_binary}" DESIGNER /F"<temp_ib>" /DumpCfg "{output_path}"'
    )


def _generated_xml_command_preview(
    *,
    output_path: Path,
    onec_binary: Path,
    ibcmd_path: Path | None,
) -> str:
    if ibcmd_path is not None:
        return (
            f'"{ibcmd_path}" infobase create '
            f'--data="<temp_data>" --db-path="<temp_ib>" --create-database && '
            f'"{ibcmd_path}" config save '
            f'--data="<temp_data>" --db-path="<temp_ib>" "{output_path}"'
        )

    return (
        f'"{onec_binary}" CREATEINFOBASE File="<temp_ib>" && '
        f'"{onec_binary}" DESIGNER /F"<temp_ib>" /DumpCfg "{output_path}"'
    )
