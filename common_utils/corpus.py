import json
from dataclasses import dataclass
from typing import Optional, List, Tuple

import networkx as nx
import torch
from lean_dojo import Pos
from loguru import logger

from common_utils.context import Context
from common_utils.file import File
from common_utils.premise import Premise, PremiseSet


class Corpus:
    """Our retrieval corpus is a DAG of files. Each file consists of
    premises (theorems, definitoins, etc.) that can be retrieved.
    """

    transitive_dep_graph: nx.DiGraph
    """Transitive closure of the dependency graph among files. 
    There is an edge from file X to Y iff X import Y (directly or indirectly).
    """

    all_premises: List[Premise]
    """All premises in the entire corpus.
    """

    def __init__(self, jsonl_path: str) -> None:
        """Construct a :class:`Corpus` object from a ``corpus.jsonl`` data file."""
        dep_graph = nx.DiGraph()
        self.all_premises = []

        logger.info(f"Building the corpus from {jsonl_path}")

        for line in open(jsonl_path):
            file_data = json.loads(line)
            path = file_data["path"]
            assert not dep_graph.has_node(path)
            file = File.from_data(file_data)

            dep_graph.add_node(path, file=file)
            self.all_premises.extend(file.premises)

            for p in file_data["imports"]:
                assert dep_graph.has_node(p)
                dep_graph.add_edge(path, p)

        assert nx.is_directed_acyclic_graph(dep_graph)
        self.transitive_dep_graph = nx.transitive_closure_dag(dep_graph)
        print('----------------------------------------')
        print(len(self.transitive_dep_graph.nodes))

        self.imported_premises_cache = {}
        self.fill_cache()

    def _get_file(self, path: str) -> File:
        return self.transitive_dep_graph.nodes[path]["file"]

    def __len__(self) -> int:
        return len(self.all_premises)

    def __contains__(self, path: str) -> bool:
        return path in self.transitive_dep_graph

    def __getitem__(self, idx: int) -> Premise:
        return self.all_premises[idx]

    @property
    def files(self) -> List[File]:
        return [self._get_file(p) for p in self.transitive_dep_graph.nodes]

    @property
    def num_files(self) -> int:
        return len(self.files)

    def get_dependencies(self, path: str) -> List[str]:
        """Return a list of (direct and indirect) dependencies of the file ``path``."""
        return list(self.transitive_dep_graph.successors(path))

    def get_premises(self, path: str) -> List[Premise]:
        """Return a list of premises defined in the file ``path``."""
        return self._get_file(path).premises

    def num_premises(self, path: str) -> int:
        """Return the number of premises defined in the file ``path``."""
        return len(self.get_premises(path))

    def locate_premise(self, path: str, pos: Pos) -> Optional[Premise]:
        """Return a premise at position ``pos`` in file ``path``.

        Return None if no such premise can be found.
        """
        for p in self.get_premises(path):
            assert p.path == path
            if p.start <= pos <= p.end:
                return p
        return None

    def fill_cache(self) -> None:
        for path in self.transitive_dep_graph.nodes:
            self._get_imported_premises(path)

    def _get_imported_premises(self, path: str) -> List[Premise]:
        """Return a list of premises imported in file ``path``. The result is cached."""
        premises = self.imported_premises_cache.get(path, None)
        if premises is not None:
            return premises

        premises = []
        for p in self.transitive_dep_graph.successors(path):
            premises.extend(self._get_file(p).premises)
        self.imported_premises_cache[path] = premises
        return premises

    def get_accessible_premises(self, path: str, pos: Pos) -> PremiseSet:
        """Return the set of premises accessible at position ``pos`` in file ``path``,
        i.e., all premises defined in the (transitively) imported files or earlier in the same file.
        """
        premises = PremiseSet()
        for p in self.get_premises(path):
            if p.end <= pos:
                premises.add(p)
        premises.update(self._get_imported_premises(path))
        return premises

    def get_accessible_premise_indexes(self, path: str, pos: Pos) -> List[int]:
        return [
            i
            for i, p in enumerate(self.all_premises)
            if (p.path == path and p.end <= pos)
            or self.transitive_dep_graph.has_edge(path, p.path)
        ]

    def get_nearest_premises(
        self,
        premise_embeddings: torch.FloatTensor,
        batch_context: List[Context],
        batch_context_emb: torch.Tensor,
        k: int,
    ) -> Tuple[List[List[Premise]], List[List[float]]]:
        """Perform a batch of nearest neighbour search."""
        similarities = batch_context_emb @ premise_embeddings.t()
        idxs_batch = similarities.argsort(dim=1, descending=True).tolist()
        results = [[] for _ in batch_context]
        scores = [[] for _ in batch_context]

        for j, (ctx, idxs) in enumerate(zip(batch_context, idxs_batch)):
            accessible_premises = self.get_accessible_premises(
                ctx.path, ctx.theorem_pos
            )
            for i in idxs:
                p = self.all_premises[i]
                if p in accessible_premises:
                    results[j].append(p)
                    scores[j].append(similarities[j, i].item())
                    if len(results[j]) >= k:
                        break
            else:
                raise ValueError

        return results, scores

@dataclass(frozen=True)
class IndexedCorpus:
    """A corpus with premise embeddings."""

    corpus: Corpus
    embeddings: torch.FloatTensor

    def __post_init__(self):
        assert self.embeddings.device == torch.device("cpu")
        assert len(self.embeddings) == len(self.corpus)