from dataclasses import dataclass, field

from onec_gen.models.field_spec import FieldSpec
from onec_gen.models.tabular_section_spec import TabularSectionSpec


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    name: str
    synonym: str = ""
    number_length: int = 9
    attributes: tuple[FieldSpec, ...] = field(default_factory=tuple)
    tabular_sections: tuple[TabularSectionSpec, ...] = field(default_factory=tuple)
    register_records: tuple[str, ...] = field(default_factory=tuple)
