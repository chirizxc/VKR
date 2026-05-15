from dataclasses import dataclass

import uuid7_rs

from onec_gen.models import (
    AccumulationRegisterSpec,
    CatalogSpec,
    ConfigSpec,
    DocumentSpec,
    FieldSpec,
    RoleSpec,
    SubsystemSpec,
    TabularSectionSpec,
)

DOCUMENT_STANDARD_ATTRIBUTES = (
    "Posted",
    "Ref",
    "DeletionMark",
    "Date",
    "Number",
)


@dataclass(frozen=True, slots=True)
class GeneratedTypeContext:
    name: str
    category: str
    type_id: str
    value_id: str


@dataclass(frozen=True, slots=True)
class FieldTemplateContext:
    field: FieldSpec
    uuid: str


@dataclass(frozen=True, slots=True)
class TabularSectionTemplateContext:
    name: str
    synonym: str
    uuid: str
    fill_checking: str
    generated_types: tuple[GeneratedTypeContext, ...]
    attributes: tuple[FieldTemplateContext, ...]


@dataclass(frozen=True, slots=True)
class ConfigurationTemplateContext:
    project_name: str
    project_prefix: str
    project_version: str
    subsystem_names: tuple[str, ...]
    catalog_names: tuple[str, ...]
    document_names: tuple[str, ...]
    accumulation_register_names: tuple[str, ...]
    role_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CatalogTemplateContext:
    catalog_name: str
    synonym: str
    catalog_uuid: str
    hierarchical: bool
    quick_choice: bool
    code_length: int
    description_length: int
    generated_types: tuple[GeneratedTypeContext, ...]
    attributes: tuple[FieldTemplateContext, ...]
    tabular_sections: tuple[TabularSectionTemplateContext, ...]


@dataclass(frozen=True, slots=True)
class DocumentTemplateContext:
    document_name: str
    synonym: str
    document_uuid: str
    number_length: int
    generated_types: tuple[GeneratedTypeContext, ...]
    standard_attribute_names: tuple[str, ...]
    attributes: tuple[FieldTemplateContext, ...]
    tabular_sections: tuple[TabularSectionTemplateContext, ...]
    register_records: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AccumulationRegisterTemplateContext:
    register_name: str
    synonym: str
    register_uuid: str
    register_type: str
    generated_types: tuple[GeneratedTypeContext, ...]
    dimensions: tuple[FieldTemplateContext, ...]
    resources: tuple[FieldTemplateContext, ...]


@dataclass(frozen=True, slots=True)
class RoleObjectRightsContext:
    object_name: str
    rights: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoleTemplateContext:
    role_name: str
    role_uuid: str
    profile: str
    object_rights: tuple[RoleObjectRightsContext, ...]


@dataclass(frozen=True, slots=True)
class SubsystemTemplateContext:
    subsystem_name: str
    subsystem_uuid: str
    content_items: tuple[str, ...]


class TemplateContextBuilder:
    def build_configuration_context(
        self,
        config: ConfigSpec,
    ) -> ConfigurationTemplateContext:
        return ConfigurationTemplateContext(
            project_name=config.project.name,
            project_prefix=config.project.namespace[:3].upper(),
            project_version=config.project.version,
            subsystem_names=tuple(item.name for item in config.subsystems),
            catalog_names=tuple(item.name for item in config.catalogs),
            document_names=tuple(item.name for item in config.documents),
            accumulation_register_names=tuple(
                item.name for item in config.accumulation_registers
            ),
            role_names=tuple(item.name for item in config.roles),
        )

    def build_catalog_context(self, catalog: CatalogSpec) -> CatalogTemplateContext:
        return CatalogTemplateContext(
            catalog_name=catalog.name,
            synonym=catalog.synonym or catalog.name,
            catalog_uuid=str(uuid7_rs.uuid7()),
            hierarchical=catalog.hierarchical,
            quick_choice=catalog.quick_choice,
            code_length=catalog.code_length,
            description_length=catalog.description_length,
            generated_types=self._build_generated_types(
                (
                    ("CatalogObject", "Object"),
                    ("CatalogRef", "Ref"),
                    ("CatalogSelection", "Selection"),
                    ("CatalogList", "List"),
                    ("CatalogManager", "Manager"),
                ),
                catalog.name,
            ),
            attributes=self._build_fields(catalog.attributes),
            tabular_sections=self._build_catalog_tabular_sections(catalog),
        )

    def build_document_context(
        self,
        document: DocumentSpec,
    ) -> DocumentTemplateContext:
        return DocumentTemplateContext(
            document_name=document.name,
            synonym=document.synonym or document.name,
            document_uuid=str(uuid7_rs.uuid7()),
            number_length=document.number_length,
            generated_types=self._build_generated_types(
                (
                    ("DocumentObject", "Object"),
                    ("DocumentRef", "Ref"),
                    ("DocumentSelection", "Selection"),
                    ("DocumentList", "List"),
                    ("DocumentManager", "Manager"),
                ),
                document.name,
            ),
            standard_attribute_names=DOCUMENT_STANDARD_ATTRIBUTES,
            attributes=self._build_fields(document.attributes),
            tabular_sections=self._build_document_tabular_sections(document),
            register_records=document.register_records,
        )

    def build_accumulation_register_context(
        self,
        accumulation_register: AccumulationRegisterSpec,
    ) -> AccumulationRegisterTemplateContext:
        return AccumulationRegisterTemplateContext(
            register_name=accumulation_register.name,
            synonym=accumulation_register.synonym or accumulation_register.name,
            register_uuid=str(uuid7_rs.uuid7()),
            register_type=accumulation_register.register_type,
            generated_types=self._build_generated_types(
                (
                    ("AccumulationRegisterRecord", "Record"),
                    ("AccumulationRegisterManager", "Manager"),
                    ("AccumulationRegisterSelection", "Selection"),
                    ("AccumulationRegisterList", "List"),
                    ("AccumulationRegisterRecordSet", "RecordSet"),
                    ("AccumulationRegisterRecordKey", "RecordKey"),
                ),
                accumulation_register.name,
            ),
            dimensions=self._build_fields(accumulation_register.dimensions),
            resources=self._build_fields(accumulation_register.resources),
        )

    def build_role_context(
        self,
        role: RoleSpec,
        config: ConfigSpec,
    ) -> RoleTemplateContext:
        return RoleTemplateContext(
            role_name=role.name,
            role_uuid=str(uuid7_rs.uuid7()),
            profile=role.profile,
            object_rights=self._build_role_object_rights(role, config),
        )

    def build_subsystem_context(
        self,
        subsystem: SubsystemSpec,
        config: ConfigSpec,
    ) -> SubsystemTemplateContext:
        return SubsystemTemplateContext(
            subsystem_name=subsystem.name,
            subsystem_uuid=str(uuid7_rs.uuid7()),
            content_items=(
                *(f"Catalog.{catalog.name}" for catalog in config.catalogs),
                *(f"Document.{document.name}" for document in config.documents),
                *(
                    f"AccumulationRegister.{register.name}"
                    for register in config.accumulation_registers
                ),
            ),
        )

    def _build_fields(
        self,
        fields: tuple[FieldSpec, ...],
    ) -> tuple[FieldTemplateContext, ...]:
        return tuple(
            FieldTemplateContext(field=field, uuid=str(uuid7_rs.uuid7()))
            for field in fields
        )

    def _build_catalog_tabular_sections(
        self,
        catalog: CatalogSpec,
    ) -> tuple[TabularSectionTemplateContext, ...]:
        return tuple(
            self._build_tabular_section(
                owner_kind="Catalog",
                owner_name=catalog.name,
                section=section,
            )
            for section in catalog.tabular_sections
        )

    def _build_document_tabular_sections(
        self,
        document: DocumentSpec,
    ) -> tuple[TabularSectionTemplateContext, ...]:
        return tuple(
            self._build_tabular_section(
                owner_kind="Document",
                owner_name=document.name,
                section=section,
            )
            for section in document.tabular_sections
        )

    def _build_tabular_section(
        self,
        *,
        owner_kind: str,
        owner_name: str,
        section: TabularSectionSpec,
    ) -> TabularSectionTemplateContext:
        type_prefix = f"{owner_kind}TabularSection"
        row_prefix = f"{owner_kind}TabularSectionRow"
        return TabularSectionTemplateContext(
            name=section.name,
            synonym=section.synonym or section.name,
            uuid=str(uuid7_rs.uuid7()),
            fill_checking=section.fill_checking,
            generated_types=self._build_generated_types(
                (
                    (f"{type_prefix}", "TabularSection"),
                    (f"{row_prefix}", "TabularSectionRow"),
                ),
                f"{owner_name}.{section.name}",
            ),
            attributes=self._build_fields(section.attributes),
        )

    def _build_role_object_rights(
        self,
        role: RoleSpec,
        config: ConfigSpec,
    ) -> tuple[RoleObjectRightsContext, ...]:
        catalog_rights = self._profile_catalog_rights(role.profile)
        document_rights = self._profile_document_rights(role.profile)
        register_rights = self._profile_register_rights(role.profile)
        object_rights = [
            *[
                RoleObjectRightsContext(
                    object_name=f"Catalog.{catalog.name}",
                    rights=catalog_rights,
                )
                for catalog in config.catalogs
            ],
            *[
                RoleObjectRightsContext(
                    object_name=f"Document.{document.name}",
                    rights=document_rights,
                )
                for document in config.documents
            ],
            *[
                RoleObjectRightsContext(
                    object_name=f"AccumulationRegister.{accumulation_register.name}",
                    rights=register_rights,
                )
                for accumulation_register in config.accumulation_registers
            ],
        ]
        return tuple(object_rights)

    def _profile_catalog_rights(self, profile: str) -> tuple[str, ...]:
        if profile == "full":
            return (
                "Read",
                "Insert",
                "Update",
                "Delete",
                "View",
                "InteractiveInsert",
                "Edit",
                "InteractiveDelete",
                "InteractiveSetDeletionMark",
                "InteractiveClearDeletionMark",
                "InteractiveDeleteMarked",
                "InputByString",
            )
        if profile == "viewer":
            return "Read", "View", "InputByString"
        return (
            "Read",
            "Insert",
            "Update",
            "Delete",
            "View",
            "InteractiveInsert",
            "Edit",
            "InteractiveDelete",
            "InteractiveSetDeletionMark",
            "InteractiveClearDeletionMark",
            "InteractiveDeleteMarked",
            "InputByString",
        )

    def _profile_document_rights(self, profile: str) -> tuple[str, ...]:
        if profile == "full":
            return (
                "Read",
                "Insert",
                "Update",
                "Delete",
                "Posting",
                "UndoPosting",
                "View",
                "InteractiveInsert",
                "Edit",
                "InteractiveDelete",
                "InteractiveSetDeletionMark",
                "InteractiveClearDeletionMark",
                "InteractiveDeleteMarked",
                "InteractivePosting",
                "InteractivePostingRegular",
                "InteractiveUndoPosting",
                "InteractiveChangeOfPosted",
                "InputByString",
            )
        if profile == "viewer":
            return "Read", "View", "InputByString"
        return (
            "Read",
            "Insert",
            "Update",
            "Delete",
            "Posting",
            "UndoPosting",
            "View",
            "InteractiveInsert",
            "Edit",
            "InteractiveDelete",
            "InteractiveSetDeletionMark",
            "InteractiveClearDeletionMark",
            "InteractiveDeleteMarked",
            "InteractivePosting",
            "InteractivePostingRegular",
            "InteractiveUndoPosting",
            "InteractiveChangeOfPosted",
            "InputByString",
        )

    def _profile_register_rights(self, profile: str) -> tuple[str, ...]:
        if profile == "viewer":
            return "Read", "View"
        return "Read", "View"

    def _build_generated_types(
        self,
        type_definitions: tuple[tuple[str, str], ...],
        object_name: str,
    ) -> tuple[GeneratedTypeContext, ...]:
        generated_types: list[GeneratedTypeContext] = []
        for type_prefix, category in type_definitions:
            generated_types.append(
                GeneratedTypeContext(
                    name=f"{type_prefix}.{object_name}",
                    category=category,
                    type_id=str(uuid7_rs.uuid7()),
                    value_id=str(uuid7_rs.uuid7()),
                ),
            )
        return tuple(generated_types)
