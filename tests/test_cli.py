from pytest_mock import MockerFixture

from onec_gen import cli


def test_main_search_prints_matches(mocker: MockerFixture) -> None:
    mocker.patch(
        "onec_gen.cli.find_presets",
        return_value=(
            mocker.Mock(title="Продажи", id="sales", summary="sum"),
        ),
    )
    writer = mocker.patch("onec_gen.cli._write_line")
    mocker.patch("sys.argv", ["1c-gen-cli", "search", "продажи"])

    result = cli.main()

    assert result == 0
    writer.assert_any_call("1. Продажи [sales]")


def test_main_search_prints_available_presets_when_empty(
    mocker: MockerFixture,
) -> None:
    mocker.patch("onec_gen.cli.find_presets", return_value=())
    mocker.patch(
        "onec_gen.cli.list_presets",
        return_value=(
            mocker.Mock(title="Продажи", id="sales", summary="sum"),
        ),
    )
    writer = mocker.patch("onec_gen.cli._write_line")
    mocker.patch("sys.argv", ["1c-gen-cli", "search", "missing"])

    result = cli.main()

    assert result == 1
    writer.assert_any_call("Совпадений не найдено.")
