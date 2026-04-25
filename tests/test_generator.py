from pathlib import Path

import orjson

from onec_gen import cli
from onec_gen.generator import generate_config
from onec_gen.loader import load_config_spec
from onec_gen.models import (
    AccumulationRegisterSpec,
    CatalogSpec,
    ConfigSpec,
    DocumentSpec,
    FieldSpec,
    ProjectSpec,
    RoleSpec,
    SubsystemSpec,
    TabularSectionSpec,
    ValueTypeSpec,
)
from onec_gen.presets import TemplatePreset, build_config_spec_from_preset


def test_load_config_spec(tmp_path: Path) -> None:
    input_path = tmp_path / "configuration.json"
    payload = {
        "project": {
            "name": "Demo",
            "namespace": "DemoConfig",
        },
        "subsystems": [
            {
                "name": "Продажи",
            },
        ],
        "catalogs": [
            {
                "name": "Номенклатура",
            },
        ],
        "documents": [
            {
                "name": "Продажа",
            },
        ],
    }
    input_path.write_bytes(orjson.dumps(payload))

    config = load_config_spec(input_path)

    assert config.project.name == "Demo"
    assert config.project.namespace == "DemoConfig"
    assert config.catalogs[0].name == "Номенклатура"


def test_build_config_spec_from_preset() -> None:
    preset = TemplatePreset(
        id="retail-store",
        title="Торговая точка",
        summary="Базовый контур для номенклатуры, складов, продаж и остатков товаров.",
        keywords=("магазин", "розница"),
        subsystems=(
            SubsystemSpec(name="Продажи"),
            SubsystemSpec(name="Склад"),
            SubsystemSpec(name="НСИ"),
        ),
        catalogs=(
            CatalogSpec(name="Номенклатура"),
            CatalogSpec(name="Склады"),
            CatalogSpec(name="Кассы"),
        ),
        documents=(
            DocumentSpec(name="Продажа"),
            DocumentSpec(name="ПоступлениеТоваров"),
            DocumentSpec(name="ПеремещениеТоваров"),
        ),
        accumulation_registers=(AccumulationRegisterSpec(name="ТоварныеЗапасы"),),
        roles=(RoleSpec(name="ПолныеПрава", profile="full"),),
    )

    config = build_config_spec_from_preset(preset)

    assert config.project.name == "Торговая точка"
    assert config.project.namespace == "ШаблонТорговаяТочка"
    assert tuple(item.name for item in config.subsystems) == ("Продажи", "Склад", "НСИ")
    assert tuple(item.name for item in config.catalogs) == (
        "Номенклатура",
        "Склады",
        "Кассы",
    )


def test_build_config_spec_from_preset_with_empty_template() -> None:
    preset = TemplatePreset(
        id="unknown",
        title="Неизвестный",
        summary="Тестовый пресет без шаблона.",
        keywords=("тест",),
        subsystems=(),
        catalogs=(),
        documents=(),
    )

    config = build_config_spec_from_preset(preset)

    assert config.project.name == "Неизвестный"
    assert config.subsystems == ()
    assert config.catalogs == ()
    assert config.documents == ()


def test_preset_cf_file_name_uses_compact_title() -> None:
    preset = TemplatePreset(
        id="services",
        title="Торговая точка",
        summary="Тест",
        keywords=(),
        subsystems=(),
        catalogs=(),
        documents=(),
    )

    preset_cf_file_name = cli.__dict__["_preset_cf_file_name"]

    assert preset_cf_file_name(preset) == "ШаблонТорговаяТочка.cf"


def test_format_preset_choice_title_aligns_separator() -> None:
    preset = TemplatePreset(
        id="sales",
        title="Продажи",
        summary="Краткое описание",
        keywords=(),
        subsystems=(),
        catalogs=(),
        documents=(),
    )

    format_preset_choice_title = cli.__dict__["_format_preset_choice_title"]
    formatted = format_preset_choice_title(preset, max_title_length=12)

    assert formatted == "Продажи      | Краткое описание"


def test_generate_config_without_onec_uses_bundled_template(tmp_path: Path) -> None:
    output_path = tmp_path / "generated"
    config = ConfigSpec(
        project=ProjectSpec(name="Demo", namespace="Demo"),
        subsystems=(SubsystemSpec(name="Продажи"),),
        catalogs=(
            CatalogSpec(
                name="Номенклатура",
                attributes=(
                    FieldSpec(
                        name="Артикул",
                        type=ValueTypeSpec(kind="string", length=20),
                    ),
                ),
            ),
        ),
        documents=(
            DocumentSpec(
                name="Продажа",
                attributes=(
                    FieldSpec(
                        name="Комментарий",
                        type=ValueTypeSpec(kind="string", length=100),
                    ),
                ),
                tabular_sections=(
                    TabularSectionSpec(
                        name="Товары",
                        attributes=(
                            FieldSpec(
                                name="Номенклатура",
                                type=ValueTypeSpec(
                                    kind="catalog_ref",
                                    target="Номенклатура",
                                ),
                            ),
                        ),
                    ),
                ),
                register_records=("Продажи",),
            ),
        ),
        accumulation_registers=(
            AccumulationRegisterSpec(
                name="Продажи",
                dimensions=(
                    FieldSpec(
                        name="Номенклатура",
                        type=ValueTypeSpec(kind="catalog_ref", target="Номенклатура"),
                    ),
                ),
                resources=(
                    FieldSpec(
                        name="Сумма",
                        type=ValueTypeSpec(kind="number", precision=12, scale=2),
                    ),
                ),
            ),
        ),
        roles=(RoleSpec(name="ПолныеПрава", profile="full"),),
    )

    generated_path = generate_config(config, output_path, onec_binary=None)

    assert generated_path == output_path.resolve()
    assert (generated_path / "Configuration.xml").exists()
    assert (generated_path / "ConfigDumpInfo.xml").exists()
    assert (generated_path / "Languages" / "Русский.xml").exists()
    assert (generated_path / "Catalogs" / "Номенклатура.xml").exists()
    assert (generated_path / "Documents" / "Продажа.xml").exists()
    assert (generated_path / "AccumulationRegisters" / "Продажи.xml").exists()
    assert (generated_path / "Roles" / "ПолныеПрава.xml").exists()
    assert (generated_path / "Roles" / "ПолныеПрава" / "Ext" / "Rights.xml").exists()
    assert (generated_path / "Subsystems" / "Продажи.xml").exists()
