from dataclasses import dataclass, field

from onec_gen.models.field_spec import FieldSpec
from onec_gen.models.tabular_section_spec import TabularSectionSpec


@dataclass(frozen=True, slots=True)
class CatalogSpec:
    name: str
    synonym: str = ""
    hierarchical: bool = False
    quick_choice: bool = False
    code_length: int = 9
    description_length: int = 25
    attributes: tuple[FieldSpec, ...] = field(default_factory=tuple)
    tabular_sections: tuple[TabularSectionSpec, ...] = field(default_factory=tuple)
