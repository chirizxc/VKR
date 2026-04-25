import logging
from dataclasses import dataclass
from pathlib import Path

from adaptix import Retort
from yaml_rs import YAMLDecodeError, loads

from onec_gen.exceptions import (
    PresetsDecodeError,
    PresetsFileReadError,
    PresetsLoadError,
)
from onec_gen.models import (
    AccumulationRegisterSpec,
    CatalogSpec,
    ConfigSpec,
    DocumentSpec,
    ProjectSpec,
    RoleSpec,
    SubsystemSpec,
)
from onec_gen.naming import default_template_stem

logger = logging.getLogger(__name__)

PRESETS_PATH = Path(__file__).resolve().parents[2] / "presets.yaml"


@dataclass(frozen=True, slots=True)
class TemplatePreset:
    id: str
    title: str
    summary: str
    keywords: tuple[str, ...]
    subsystems: tuple[SubsystemSpec, ...]
    catalogs: tuple[CatalogSpec, ...]
    documents: tuple[DocumentSpec, ...]
    accumulation_registers: tuple[AccumulationRegisterSpec, ...] = ()
    roles: tuple[RoleSpec, ...] = ()


def list_presets() -> tuple[TemplatePreset, ...]:
    return _load_presets()


def build_config_spec_from_preset(preset: TemplatePreset) -> ConfigSpec:
    project_name = preset.title.strip()
    provisional_config = ConfigSpec(
        project=ProjectSpec(name=project_name, namespace=project_name),
    )
    project_namespace = default_template_stem(provisional_config)

    return ConfigSpec(
        project=ProjectSpec(
            name=project_name,
            namespace=project_namespace,
        ),
        subsystems=preset.subsystems,
        catalogs=preset.catalogs,
        documents=preset.documents,
        accumulation_registers=preset.accumulation_registers,
        roles=preset.roles,
    )


def find_presets(query: str) -> tuple[TemplatePreset, ...]:
    presets = _load_presets()
    normalized_query = query.strip().lower()
    if not normalized_query:
        return presets

    matched_presets = []
    for preset in presets:
        haystack = " ".join((preset.id, preset.title, preset.summary, *preset.keywords))
        if normalized_query in haystack.lower():
            matched_presets.append(preset)

    return tuple(matched_presets)


_retort = Retort()


def _load_presets() -> tuple[TemplatePreset, ...]:
    logger.debug("Загружаю пресеты из файла: %s", PRESETS_PATH)
    try:
        text = PRESETS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise PresetsFileReadError(PRESETS_PATH, str(exc)) from exc

    try:
        yaml_presets = loads(text)
    except YAMLDecodeError as exc:
        raise PresetsDecodeError(PRESETS_PATH, str(exc)) from exc

    try:
        presets = _retort.load(yaml_presets, list[TemplatePreset])
    except Exception as exc:
        raise PresetsLoadError(PRESETS_PATH, str(exc)) from exc

    return tuple(presets)
