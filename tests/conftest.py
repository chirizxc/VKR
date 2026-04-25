from pathlib import Path

import pytest

from onec_gen.models import (
    CatalogSpec,
    ConfigSpec,
    DocumentSpec,
    ProjectSpec,
    SubsystemSpec,
)


@pytest.fixture
def sample_config() -> ConfigSpec:
    return ConfigSpec(
        project=ProjectSpec(name="Demo", namespace="DemoConfig"),
        subsystems=(SubsystemSpec(name="Продажи"),),
        catalogs=(CatalogSpec(name="Номенклатура"),),
        documents=(DocumentSpec(name="Продажа"),),
    )


@pytest.fixture
def manifests_dir() -> Path:
    return Path(__file__).resolve().parent / "manifests"
