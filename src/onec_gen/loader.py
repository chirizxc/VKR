import logging
from pathlib import Path
from typing import Any

import orjson
from adaptix import Retort
from jsonschema_rs import ValidationError, validate

from onec_gen.exceptions import (
    ConfigFileReadError,
    ConfigJsonDecodeError,
    ConfigLoadError,
    ConfigSchemaValidationError,
)
from onec_gen.models import ConfigSpec
from onec_gen.schemas.schema import load_json_schema
from onec_gen.validation import validate_config_spec

logger = logging.getLogger(__name__)
_retort = Retort()


def load_config_spec(input_path: Path) -> ConfigSpec:
    logger.info("Загружаю описание конфигурации из файла: %s", input_path)
    try:
        raw_payload = input_path.read_bytes()
    except OSError as exc:
        raise ConfigFileReadError(input_path, str(exc)) from exc

    try:
        payload: Any = orjson.loads(raw_payload)
    except orjson.JSONDecodeError as exc:
        raise ConfigJsonDecodeError(input_path, str(exc)) from exc

    _validate_payload(payload)

    try:
        config_spec = _retort.load(payload, ConfigSpec)
    except Exception as exc:
        raise ConfigLoadError(str(exc)) from exc
    try:
        validate_config_spec(config_spec)
    except ValueError as exc:
        raise ConfigLoadError(str(exc)) from exc

    logger.info("Описание конфигурации загружено: %s", config_spec.project.name)
    return config_spec


def _validate_payload(payload: Any) -> None:
    try:
        validate(load_json_schema(), payload)
    except ValidationError as exc:
        raise ConfigSchemaValidationError(str(exc)) from exc
