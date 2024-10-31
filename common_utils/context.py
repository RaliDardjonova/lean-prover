from dataclasses import dataclass, field
from typing import Dict, Any

from lean_dojo import Pos

from common_utils import MARK_START_SYMBOL, MARK_END_SYMBOL

Example = Dict[str, Any]
Batch = Dict[str, Any]


def remove_marks(s: str) -> str:
    """Remove all :code:`<a>` and :code:`</a>` from ``s``."""
    return s.replace(MARK_START_SYMBOL, "").replace(MARK_END_SYMBOL, "")


@dataclass(unsafe_hash=True)
class Context:
    """Contexts are "queries" in our retrieval setup."""

    path: str
    theorem_full_name: str
    theorem_pos: Pos = field(compare=False)
    state: str

    def __post_init__(self) -> None:
        assert isinstance(self.path, str)
        assert isinstance(self.theorem_full_name, str)
        assert isinstance(self.theorem_pos, Pos)
        assert (
            isinstance(self.state, str)
            and "⊢" in self.state
            and MARK_START_SYMBOL not in self.state
            and MARK_END_SYMBOL not in self.state
        )

    def serialize(self) -> str:
        """Serialize the context into a string for Transformers."""
        return self.state
