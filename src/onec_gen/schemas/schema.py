import functools
import logging
from pathlib import Path
from typing import Any

import orjson

logger = logging.getLogger(__name__)


@functools.cache
def load_json_schema() -> Any:
    json_schema = Path(__file__).resolve().parents[3] / "schema.json"
    logger.debug("Загружаю JSON Schema из файла: %s", json_schema)
    return orjson.loads(json_schema.read_bytes())
