from dataclasses import dataclass, field

from onec_gen.models.accumulation_register_spec import AccumulationRegisterSpec
from onec_gen.models.catalog_spec import CatalogSpec
from onec_gen.models.document_spec import DocumentSpec
from onec_gen.models.project_spec import ProjectSpec
from onec_gen.models.role_spec import RoleSpec
from onec_gen.models.subsystem_spec import SubsystemSpec


@dataclass(frozen=True, slots=True)
class ConfigSpec:
    project: ProjectSpec
    subsystems: tuple[SubsystemSpec, ...] = field(default_factory=tuple)
    catalogs: tuple[CatalogSpec, ...] = field(default_factory=tuple)
    documents: tuple[DocumentSpec, ...] = field(default_factory=tuple)
    accumulation_registers: tuple[AccumulationRegisterSpec, ...] = field(
        default_factory=tuple,
    )
    roles: tuple[RoleSpec, ...] = field(default_factory=tuple)
