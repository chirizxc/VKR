from dataclasses import dataclass, field

from onec_gen.models.field_spec import FieldSpec


@dataclass(frozen=True, slots=True)
class TabularSectionSpec:
    name: str
    synonym: str = ""
    fill_checking: str = "DontCheck"
    attributes: tuple[FieldSpec, ...] = field(default_factory=tuple)
