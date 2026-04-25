from dataclasses import dataclass, field

from onec_gen.models.field_spec import FieldSpec


@dataclass(frozen=True, slots=True)
class AccumulationRegisterSpec:
    name: str
    synonym: str = ""
    register_type: str = "Balance"
    dimensions: tuple[FieldSpec, ...] = field(default_factory=tuple)
    resources: tuple[FieldSpec, ...] = field(default_factory=tuple)
