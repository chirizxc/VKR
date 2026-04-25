from collections.abc import Iterable

from onec_gen.models import ConfigSpec, FieldSpec, TabularSectionSpec


def validate_config_spec(config: ConfigSpec) -> None:
    _ensure_unique_names("подсистема", (item.name for item in config.subsystems))
    _ensure_unique_names("справочник", (item.name for item in config.catalogs))
    _ensure_unique_names("документ", (item.name for item in config.documents))
    _ensure_unique_names(
        "регистр накопления",
        (item.name for item in config.accumulation_registers),
    )
    _ensure_unique_names("роль", (item.name for item in config.roles))

    catalog_names = {item.name for item in config.catalogs}
    document_names = {item.name for item in config.documents}
    register_names = {item.name for item in config.accumulation_registers}

    for catalog in config.catalogs:
        _validate_field_collection(
            scope=f"справочник {catalog.name}",
            fields=catalog.attributes,
            catalog_names=catalog_names,
            document_names=document_names,
        )
        _validate_tabular_sections(
            scope=f"справочник {catalog.name}",
            sections=catalog.tabular_sections,
            catalog_names=catalog_names,
            document_names=document_names,
        )

    for document in config.documents:
        _validate_field_collection(
            scope=f"документ {document.name}",
            fields=document.attributes,
            catalog_names=catalog_names,
            document_names=document_names,
        )
        _validate_tabular_sections(
            scope=f"документ {document.name}",
            sections=document.tabular_sections,
            catalog_names=catalog_names,
            document_names=document_names,
        )
        for register_name in document.register_records:
            if register_name not in register_names:
                message = (
                    "Документ "
                    f"{document.name} ссылается на неизвестный регистр накопления "
                    f"{register_name}."
                )
                raise ValueError(message)

    for register in config.accumulation_registers:
        _validate_field_collection(
            scope=f"регистр накопления {register.name}",
            fields=register.dimensions,
            catalog_names=catalog_names,
            document_names=document_names,
        )
        _validate_field_collection(
            scope=f"регистр накопления {register.name}",
            fields=register.resources,
            catalog_names=catalog_names,
            document_names=document_names,
        )


def _validate_tabular_sections(
    *,
    scope: str,
    sections: tuple[TabularSectionSpec, ...],
    catalog_names: set[str],
    document_names: set[str],
) -> None:
    _ensure_unique_names(
        f"табличная часть ({scope})",
        (section.name for section in sections),
    )
    for section in sections:
        _validate_field_collection(
            scope=f"{scope}, табличная часть {section.name}",
            fields=section.attributes,
            catalog_names=catalog_names,
            document_names=document_names,
        )


def _validate_field_collection(
    *,
    scope: str,
    fields: tuple[FieldSpec, ...],
    catalog_names: set[str],
    document_names: set[str],
) -> None:
    _ensure_unique_names(f"реквизит ({scope})", (field.name for field in fields))
    for field in fields:
        if field.type.kind == "catalog_ref" and field.type.target not in catalog_names:
            message = (
                f"{scope}: реквизит {field.name} ссылается на "
                f"неизвестный справочник {field.type.target}."
            )
            raise ValueError(message)
        if field.type.kind == "document_ref" and field.type.target not in document_names:
            message = (
                f"{scope}: реквизит {field.name} ссылается на "
                f"неизвестный документ {field.type.target}."
            )
            raise ValueError(message)


def _ensure_unique_names(kind: str, names: Iterable[str]) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            message = f"Повторяющееся имя ({kind}): {name}"
            raise ValueError(message)
        seen.add(name)
