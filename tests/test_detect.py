from pathlib import Path

import pytest
from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
from pytest_mock import MockerFixture

from onec_gen.detect import OneCDetector
from onec_gen.exceptions import OneCBatchModeNotSupportedError, OneCNotFoundError


def test_read_installed_location_handles_utf16le_bom(tmp_path: Path) -> None:
    config_path = tmp_path / "1cestart.cfg"
    config_path.write_text(
        "InstalledLocation=C:\\Program Files (x86)\\1cv8t\n",
        encoding="utf-16",
    )
    detector = OneCDetector()

    read_installed_location = detector.__class__.__dict__["_read_installed_location"]
    installed_location = read_installed_location(detector, config_path)

    assert installed_location == Path(r"C:\Program Files (x86)\1cv8t")


def test_detect_ibcmd_binary_next_to_onec(tmp_path: Path) -> None:
    onec_binary = tmp_path / "1cv8t.exe"
    ibcmd_binary = tmp_path / "ibcmd.exe"
    onec_binary.write_text("", encoding="utf-8")
    ibcmd_binary.write_text("", encoding="utf-8")
    detector = OneCDetector()

    detected = detector.detect_ibcmd_binary(onec_binary)

    assert detected == ibcmd_binary.resolve()


def test_resolve_onec_binary_raises_for_unsupported_manual_binary(tmp_path: Path) -> None:
    unsupported = tmp_path / "1cv8c.exe"
    unsupported.write_text("", encoding="utf-8")
    detector = OneCDetector()

    with pytest.raises(OneCBatchModeNotSupportedError):
        detector.resolve_onec_binary(unsupported)


def test_resolve_onec_binary_raises_when_nothing_found(
    mocker: MockerFixture,
) -> None:
    detector = OneCDetector()
    mocker.patch.object(detector, "detect_onec_binary", return_value=None)

    with pytest.raises(OneCNotFoundError):
        detector.resolve_onec_binary(None)


def test_ask_user_to_choose_path_falls_back_to_educational(
    mocker: MockerFixture,
) -> None:
    detector = OneCDetector()
    mock_question = mocker.patch("onec_gen.detect.select_with_compact_answer")
    mock_question.side_effect = NoConsoleScreenBufferError
    candidates = (
        Path(r"C:\Program Files (x86)\1cv8\8.3.27.1936\bin\1cv8.exe"),
        Path(r"C:\Program Files (x86)\1cv8t\8.3.27.1688\bin\1cv8t.exe"),
    )

    ask_user_to_choose_path = detector.__class__.__dict__["_ask_user_to_choose_path"]
    selected = ask_user_to_choose_path(detector, candidates)

    assert selected == candidates[1]
