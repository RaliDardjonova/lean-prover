from dataclasses import dataclass, field
from typing import List, Dict, Any

from lean_dojo import Pos

from common_utils.premise import Premise


@dataclass(frozen=True)
class File:
    """A file defines 0 or multiple premises."""

    path: str
    """Path of the ``*.lean`` file.
    """

    premises: List[Premise] = field(repr=False, compare=False)
    """A list of premises defined in this file.
    """

    @classmethod
    def from_data(cls, file_data: Dict[str, Any]) -> "File":
        """Construct a :class:`File` object from ``file_data``."""
        path = file_data["path"]
        premises = []
        for p in file_data["premises"]:
            full_name = p["full_name"]
            if full_name is None:
                continue
            if "user__.n" in full_name or p["code"] == "":
                # Ignore ill-formed premises (often due to errors in ASTs).
                continue
            if full_name.startswith("[") and full_name.endswith("]"):
                # Ignore mutual definitions.
                continue
            premises.append(
                Premise(
                    path, p["full_name"], Pos(*p["start"]), Pos(*p["end"]), p["code"]
                )
            )
        return cls(path, premises)

    @property
    def is_empty(self) -> bool:
        """Check whether the file contains no premise."""
        return self.premises == []