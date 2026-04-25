import functools
import logging
from importlib.resources import files
from typing import Any

import orjson

logger = logging.getLogger(__name__)


@functools.cache
def load_json_schema() -> Any:
    json_schema = files("onec_gen.schemas").joinpath("schema.json")
    logger.debug("Загружаю JSON Schema из файла: %s", json_schema)
    return orjson.loads(json_schema.read_bytes())
