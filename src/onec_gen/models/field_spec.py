from dataclasses import dataclass, field

from onec_gen.models.value_type_spec import ValueTypeSpec


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    synonym: str = ""
    comment: str = ""
    type: ValueTypeSpec = field(
        default_factory=lambda: ValueTypeSpec(kind="string", length=50),
    )
    fill_checking: str = "DontCheck"
    indexing: str = "DontIndex"
    full_text_search: str = "Use"
    multiline: bool = False
    extended_edit: bool = False
    mark_negatives: bool = False
    fill_from_filling_value: bool = False
    use_in_totals: bool = False
    use: str = "ForItem"
