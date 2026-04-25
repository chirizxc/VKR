from pathlib import Path

import pytest

from onec_gen.exceptions import (
    ConfigFileReadError,
    ConfigJsonDecodeError,
    ConfigSchemaValidationError,
)
from onec_gen.loader import load_config_spec
from onec_gen.models import ConfigSpec
from onec_gen.naming import (
    default_cf_file_name,
    default_generated_dir_name,
    default_template_stem,
)


def test_load_config_spec_from_manifest(manifests_dir: Path) -> None:
    config = load_config_spec(manifests_dir / "config_valid.json")

    assert config.project.name == "Demo"
    assert config.project.namespace == "DemoConfig"


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ("{", ConfigJsonDecodeError),
        ('{"project": {"name": "Demo"}}', ConfigSchemaValidationError),
    ],
)
def test_load_config_spec_validation_errors(
    tmp_path: Path,
    payload: str,
    expected_error: type[Exception],
) -> None:
    input_path = tmp_path / "configuration.json"
    input_path.write_text(payload, encoding="utf-8")

    with pytest.raises(expected_error):
        load_config_spec(input_path)


def test_load_config_spec_missing_file_raises() -> None:
    with pytest.raises(ConfigFileReadError):
        load_config_spec(Path("missing.json"))


def test_naming_functions_use_template_prefix(sample_config: ConfigSpec) -> None:
    assert default_template_stem(sample_config) == "ШаблонDemo"
    assert default_cf_file_name(sample_config) == "ШаблонDemo.cf"
    assert default_generated_dir_name(sample_config) == "ШаблонDemo"
