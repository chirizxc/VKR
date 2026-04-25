from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectSpec:
    name: str
    namespace: str
    version: str = "0.1.0"
