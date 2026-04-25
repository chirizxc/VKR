from pathlib import Path

import pytest

from onec_gen.exceptions import PresetsDecodeError, PresetsLoadError
from onec_gen.presets import find_presets, list_presets


def test_list_presets_loads_from_manifest(
    monkeypatch: pytest.MonkeyPatch,
    manifests_dir: Path,
) -> None:
    monkeypatch.setattr(
        "onec_gen.presets.PRESETS_PATH",
        manifests_dir / "presets_valid.yaml",
    )

    presets = list_presets()

    assert tuple(preset.id for preset in presets) == ("sales", "services")


@pytest.mark.parametrize(
    ("query", "expected_ids"),
    [
        ("", ("sales", "services")),
        ("продажи", ("sales",)),
        ("услуги", ("services",)),
        ("missing", ()),
    ],
)
def test_find_presets_filters_by_query(
    monkeypatch: pytest.MonkeyPatch,
    manifests_dir: Path,
    query: str,
    expected_ids: tuple[str, ...],
) -> None:
    monkeypatch.setattr(
        "onec_gen.presets.PRESETS_PATH",
        manifests_dir / "presets_valid.yaml",
    )

    presets = find_presets(query)

    assert tuple(preset.id for preset in presets) == expected_ids


def test_list_presets_raises_on_malformed_yaml(
    monkeypatch: pytest.MonkeyPatch,
    manifests_dir: Path,
) -> None:
    monkeypatch.setattr(
        "onec_gen.presets.PRESETS_PATH",
        manifests_dir / "presets_malformed.yaml",
    )

    with pytest.raises(PresetsDecodeError):
        list_presets()


def test_list_presets_raises_on_invalid_shape(
    monkeypatch: pytest.MonkeyPatch,
    manifests_dir: Path,
) -> None:
    monkeypatch.setattr(
        "onec_gen.presets.PRESETS_PATH",
        manifests_dir / "presets_invalid.yaml",
    )

    with pytest.raises(PresetsLoadError):
        list_presets()
