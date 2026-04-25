from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoleSpec:
    name: str
    profile: str = "editor"
