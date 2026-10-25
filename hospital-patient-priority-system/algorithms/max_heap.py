"""Binary max-heap written from scratch (array representation, no ``heapq``).

Array layout: parent(i) = (i-1)//2, children 2i+1 and 2i+2.
A position map (id -> index) makes ``update_priority`` possible in O(log n).

Operation          time          extra space
insert             O(log n)      O(1) auxiliary (amortised array growth)
peek               O(1)          O(1)
extract            O(log n)      O(1)
update_priority    O(log n)      O(1)
build by n inserts O(n log n)    O(n) for the heap itself

``before(a, b)`` decides which of two items is nearer the root. For patients it is the
same ``precedes`` rule used by the greedy scheduler and merge sort, so all three agree.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .greedy_scheduler import precedes


@dataclass
class HeapItem:
    item_id: str
    score: float
    payload: Any = None


def patient_before(a: HeapItem, b: HeapItem) -> bool:
    """Priority-policy comparator: score, severity, arrival, patient ID."""
    return precedes(a.score, a.payload, b.score, b.payload)


def _score_before(a: HeapItem, b: HeapItem) -> bool:
    if a.score != b.score:
        return a.score > b.score
    return a.item_id < b.item_id


class MaxHeap:
    def __init__(self, before: Optional[Callable[[HeapItem, HeapItem], bool]] = None,
                 record: bool = False):
        self._a: List[HeapItem] = []
        self._pos: Dict[str, int] = {}
        self._before = before or _score_before
        self.record = record
        self.history: List[dict] = []

    # ---- inspection -------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._a)

    def is_empty(self) -> bool:
        return len(self._a) == 0

    def __contains__(self, item_id: str) -> bool:
        return item_id in self._pos

    def items(self) -> List[HeapItem]:
        return list(self._a)

    def to_array(self) -> List[Tuple[str, float]]:
        return [(it.item_id, it.score) for it in self._a]

    def peek(self) -> HeapItem:
        if not self._a:
            raise IndexError("peek from an empty heap")
        return self._a[0]

    def is_valid(self) -> bool:
        """Heap property: no child may strictly precede its parent."""
        for i in range(1, len(self._a)):
            if self._before(self._a[i], self._a[(i - 1) // 2]):
                return False
        return True

    def to_tree_text(self) -> str:
        """Indented text drawing of the tree (root first)."""
        lines: List[str] = []

        def walk(i: int, depth: int) -> None:
            if i >= len(self._a):
                return
            it = self._a[i]
            lines.append(f"{'    ' * depth}{'└─ ' if depth else ''}[{i}] {it.item_id}  ({it.score:.2f})")
            walk(2 * i + 1, depth + 1)
            walk(2 * i + 2, depth + 1)

        walk(0, 0)
        return "\n".join(lines)

    # ---- internals --------------------------------------------------------------------
    def _swap(self, i: int, j: int) -> None:
        a = self._a
        a[i], a[j] = a[j], a[i]
        self._pos[a[i].item_id] = i
        self._pos[a[j].item_id] = j

    def _sift_up(self, i: int) -> List[Tuple[str, str]]:
        swaps: List[Tuple[str, str]] = []
        while i > 0:
            parent = (i - 1) // 2
            if self._before(self._a[i], self._a[parent]):
                swaps.append((self._a[i].item_id, self._a[parent].item_id))
                self._swap(i, parent)
                i = parent
            else:
                break
        return swaps

    def _sift_down(self, i: int) -> List[Tuple[str, str]]:
        swaps: List[Tuple[str, str]] = []
        n = len(self._a)
        while True:
            left, right, best = 2 * i + 1, 2 * i + 2, i
            if left < n and self._before(self._a[left], self._a[best]):
                best = left
            if right < n and self._before(self._a[right], self._a[best]):
                best = right
            if best == i:
                break
            swaps.append((self._a[best].item_id, self._a[i].item_id))
            self._swap(i, best)
            i = best
        return swaps

    def _log(self, op: str, detail: str, swaps: List[Tuple[str, str]]) -> None:
        if self.record:
            self.history.append({"op": op, "detail": detail, "swaps": swaps,
                                 "array": self.to_array(), "size": len(self._a)})

    # ---- public operations ------------------------------------------------------------
    def insert(self, item_id: str, score: float, payload: Any = None) -> None:
        if item_id in self._pos:
            raise ValueError(f"Item {item_id!r} is already in the heap.")
        if score != score or score in (math.inf, -math.inf):
            raise ValueError("Score must be a finite number.")
        self._a.append(HeapItem(item_id, score, payload))
        self._pos[item_id] = len(self._a) - 1
        swaps = self._sift_up(len(self._a) - 1)
        self._log("insert", f"Insert {item_id} (score {score:.2f}) at the end, sift up ({len(swaps)} swap(s)).", swaps)

    def extract(self) -> HeapItem:
        if not self._a:
            raise IndexError("extract from an empty heap")
        root = self._a[0]
        last = self._a.pop()
        del self._pos[root.item_id]
        swaps: List[Tuple[str, str]] = []
        if self._a:
            self._a[0] = last
            self._pos[last.item_id] = 0
            swaps = self._sift_down(0)
        self._log("extract", f"Extract root {root.item_id} (score {root.score:.2f}); move last item to the root and sift down ({len(swaps)} swap(s)).", swaps)
        return root

    def update_priority(self, item_id: str, new_score: float) -> None:
        """Change an item's score and restore the heap property (sift up or down)."""
        if item_id not in self._pos:
            raise KeyError(f"Item {item_id!r} is not in the heap.")
        if new_score != new_score or new_score in (math.inf, -math.inf):
            raise ValueError("Score must be a finite number.")
        idx = self._pos[item_id]
        old = self._a[idx].score
        self._a[idx].score = new_score
        swaps = self._sift_up(idx)
        swaps += self._sift_down(self._pos[item_id])
        self._log("update", f"Update {item_id}: {old:.2f} -> {new_score:.2f} ({len(swaps)} swap(s)).", swaps)


def patient_heap(record: bool = False) -> MaxHeap:
    """A heap that orders patients by the shared priority policy."""
    return MaxHeap(before=patient_before, record=record)
