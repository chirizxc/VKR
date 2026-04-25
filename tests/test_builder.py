from pathlib import Path

import pytest

from onec_gen.builder import OneCCommandExecutor, build_config
from onec_gen.exceptions import OneCBuildError
from onec_gen.models import ConfigSpec


@pytest.mark.parametrize(
    ("source_name", "expected_fragment"),
    [
        ("source.cf", 'copy "'),
        ("source.xml", "CREATEINFOBASE"),
    ],
)
def test_build_config_dry_run_returns_command_preview(
    tmp_path: Path,
    sample_config: ConfigSpec,
    source_name: str,
    expected_fragment: str,
) -> None:
    source_path = tmp_path / source_name
    output_path = tmp_path / "result.cf"
    if source_path.suffix == ".cf":
        source_path.write_text("cf", encoding="utf-8")
    else:
        source_path.write_text("<xml />", encoding="utf-8")

    result = build_config(
        source_path=source_path,
        output_path=output_path,
        onec_binary=Path(r"C:\1C\1cv8t.exe"),
        config=sample_config,
        dry_run=True,
    )

    assert "Dry-run: сборка не запускалась." in result
    assert expected_fragment in result


def test_build_config_copies_ready_cf(
    tmp_path: Path,
    sample_config: ConfigSpec,
) -> None:
    source_path = tmp_path / "ready.cf"
    source_path.write_text("ready", encoding="utf-8")
    output_path = tmp_path / "result.cf"

    result = build_config(
        source_path=source_path,
        output_path=output_path,
        onec_binary=Path(r"C:\1C\1cv8t.exe"),
        config=sample_config,
        dry_run=False,
    )

    assert output_path.read_text(encoding="utf-8") == "ready"
    assert "Исходный cf-файл скопирован в целевой путь." in result


def test_build_config_raises_for_unsupported_source(
    tmp_path: Path,
    sample_config: ConfigSpec,
) -> None:
    source_path = tmp_path / "unsupported.txt"
    source_path.write_text("data", encoding="utf-8")

    with pytest.raises(OneCBuildError, match="Неподдерживаемый источник"):
        build_config(
            source_path=source_path,
            output_path=tmp_path / "result.cf",
            onec_binary=Path(r"C:\1C\1cv8t.exe"),
            config=sample_config,
            dry_run=False,
        )


def test_command_executor_includes_log_details(tmp_path: Path) -> None:
    log_path = tmp_path / "designer.log"
    log_path.write_text("diagnostic details", encoding="utf-8")
    executor = OneCCommandExecutor()

    with pytest.raises(OneCBuildError, match="diagnostic details"):
        executor.run(
            ["python", "-c", "import sys; sys.exit(3)"],
            step_name="падающий шаг",
            log_path=log_path,
        )
