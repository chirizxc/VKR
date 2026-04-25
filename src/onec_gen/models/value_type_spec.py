from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValueTypeSpec:
    kind: str
    target: str = ""
    length: int = 0
    precision: int = 10
    scale: int = 0
    non_negative: bool = False
    date_fractions: str = "Date"
