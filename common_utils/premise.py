import re
from dataclasses import dataclass, field
from typing import List, Dict, Generator

from lean_dojo import Pos

from common_utils import MARK_START_SYMBOL, MARK_END_SYMBOL


@dataclass(unsafe_hash=True)
class Premise:
    """Premises are "documents" in our retrieval setup."""

    path: str
    """The ``*.lean`` file this premise comes from.
    """

    full_name: str
    """Fully qualified name.
    """

    start: Pos = field(repr=False)
    """Start position of the premise's definition in the ``*.lean`` file.
    """

    end: Pos = field(repr=False, compare=False)
    """End position of the premise's definition in the ``*.lean`` file.
    """

    code: str = field(compare=False)
    """Raw, human-written code for defining the premise.
    """

    def __post_init__(self) -> None:
        assert isinstance(self.path, str)
        assert isinstance(self.full_name, str)
        assert (
            isinstance(self.start, Pos)
            and isinstance(self.end, Pos)
            and self.start <= self.end
        )
        assert isinstance(self.code, str) and self.code != ""

    def serialize(self) -> str:
        """Serialize the premise into a string for Transformers."""
        annot_full_name = f"{MARK_START_SYMBOL}{self.full_name}{MARK_END_SYMBOL}"
        code = self.code.replace(f"_root_.{self.full_name}", annot_full_name)
        fields = self.full_name.split(".")

        for i in range(len(fields)):
            prefix = ".".join(fields[i:])
            new_code = re.sub(f"(?<=\s)«?{prefix}»?", annot_full_name, code)
            if new_code != code:
                code = new_code
                break

        return code


class PremiseSet:
    """A set of premises indexed by their paths and full names."""

    path2premises: Dict[str, Dict[str, Premise]]

    def __init__(self) -> None:
        self.path2premises = {}

    def __iter__(self) -> Generator[Premise, None, None]:
        for _, premises in self.path2premises.items():
            for p in premises.values():
                yield p

    def add(self, p: Premise) -> None:
        if p.path in self.path2premises:
            self.path2premises[p.path][p.full_name] = p
        else:
            self.path2premises[p.path] = {p.full_name: p}

    def update(self, premises: List[Premise]) -> None:
        for p in premises:
            self.add(p)

    def __contains__(self, p: Premise) -> bool:
        return (
            p.path in self.path2premises and p.full_name in self.path2premises[p.path]
        )

    def __len__(self) -> int:
        return sum(len(premises) for premises in self.path2premises.values())