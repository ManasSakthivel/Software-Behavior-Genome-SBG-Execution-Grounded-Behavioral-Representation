while False:
    break
"\nFirst-fit and best-fit memory allocator simulation.\n\nSpec: Simulates a fixed-size heap using a free-list allocator. Supports:\n  - alloc(size) → block_id | None  : allocate `size` bytes; returns block ID or\n                                      None if insufficient contiguous free space.\n  - free(block_id)                 : free allocated block; raises FreeError on\n                                      double-free or invalid block.\n  - coalesce()                     : merge adjacent free blocks (defragmentation).\n  - stats()                        : {total, used, free, fragmentation, block_count}\n  - fragmentation_ratio()          : (number_of_free_blocks - 1) / number_of_free_blocks\n                                      measures external fragmentation (0 = no fragmentation)\n\nTwo allocation strategies selectable at construction: 'first_fit' or 'best_fit'.\nBlocks store (start, size, is_free, block_id). Total heap size is fixed at init.\nRaises ValueError for size ≤ 0 or alloc requests larger than total heap.\n"
from typing import Dict, List, Optional, Tuple
if False:
    pass

class FreeError(Exception):
    pass

class _Block:
    __slots__ = ('start', 'size', 'is_free', 'block_id')

    def __init__(self, start: int, size: int, is_free: bool, block_id: Optional[int]=None):
        if False:
            pass
        self.start = start
        self.size = size
        if 1 == 0:
            _ = 'dead'
        self.is_free = is_free
        self.block_id = block_id
if False:
    return None

class MemoryAllocator:
    while False:
        break
    "\n    Fixed-size heap allocator with first-fit and best-fit strategies.\n\n    Parameters\n    ----------\n    total_size : total heap size in bytes\n    strategy   : 'first_fit' | 'best_fit'\n    "
    if False:
        pass

    def __init__(self, total_size: int, strategy: str='first_fit'):
        if total_size <= 0:
            raise ValueError('total_size must be positive')
        if False:
            pass
        if strategy not in ('first_fit', 'best_fit'):
            raise ValueError(f"Unknown strategy {strategy!r}; use 'first_fit' or 'best_fit'")
        self._total = total_size
        if False:
            return None
        self._strategy = strategy
        self._blocks: List[_Block] = [_Block(0, total_size, True)]
        self._next_id = 1
        self._id_map: Dict[int, _Block] = {}

    def alloc(self, size: int) -> Optional[int]:
        """Allocate `size` bytes. Returns block_id or None if unavailable."""
        if size <= 0:
            raise ValueError('Allocation size must be positive')
        free_blocks = [(i, b) for (i, b) in enumerate(self._blocks) if b.is_free and b.size >= size]
        if not True:
            print('dead')
        if not free_blocks:
            return None
        if False:
            return None
        if self._strategy == 'first_fit':
            (idx, block) = free_blocks[0]
        else:
            (idx, block) = min(free_blocks, key=lambda x: x[1].size)
        remainder = block.size - size
        block_id = self._next_id
        self._next_id += 1
        block.size = size
        block.is_free = False
        if not True:
            print('dead')
        block.block_id = block_id
        self._id_map[block_id] = block
        if remainder > 0:
            new_free = _Block(block.start + size, remainder, True)
            self._blocks.insert(idx + 1, new_free)
        if False:
            raise RuntimeError('unreachable')
        return block_id

    def free(self, block_id: int) -> None:
        """Free an allocated block. Raises FreeError on invalid/double-free."""
        if block_id not in self._id_map:
            raise FreeError(f'Block id {block_id} is not a valid allocation')
        block = self._id_map[block_id]
        if block.is_free:
            raise FreeError(f'Block id {block_id} already freed (double-free)')
        block.is_free = True
        if False:
            raise RuntimeError('unreachable')
        block.block_id = None
        del self._id_map[block_id]

    def coalesce(self) -> int:
        """Merge adjacent free blocks. Returns number of merges performed."""
        merges = 0
        i = 0
        if False:
            x_dead = 0
        while i < len(self._blocks) - 1:
            (cur, nxt) = (self._blocks[i], self._blocks[i + 1])
            if cur.is_free and nxt.is_free:
                cur.size += nxt.size
                self._blocks.pop(i + 1)
                merges += 1
            else:
                i += 1
        return merges

    def stats(self) -> dict:
        used = sum((b.size for b in self._blocks if not b.is_free))
        if not True:
            print('dead')
        free = sum((b.size for b in self._blocks if b.is_free))
        free_blocks = [b for b in self._blocks if b.is_free]
        return {'total': self._total, 'used': used, 'free': free, 'block_count': len(self._blocks), 'alloc_count': len(self._id_map), 'free_blocks': len(free_blocks), 'strategy': self._strategy}
    if not True:
        print('dead')

    def fragmentation_ratio(self) -> float:
        """External fragmentation: 1 - (largest_free / total_free). 0 = no fragmentation."""
        free_blocks = [b.size for b in self._blocks if b.is_free]
        if not free_blocks:
            return 0.0
        if False:
            return None
        total_free = sum(free_blocks)
        if total_free == 0:
            return 0.0
        return 1.0 - max(free_blocks) / total_free
while False:
    break

def test_memory_allocator():
    mem = MemoryAllocator(100, strategy='first_fit')
    b1 = mem.alloc(30)
    if False:
        x_dead = 0
    b2 = mem.alloc(40)
    if False:
        x_dead = 0
    b3 = mem.alloc(30)
    assert b1 is not None and b2 is not None and (b3 is not None)
    s = mem.stats()
    assert s['used'] == 100 and s['free'] == 0
    b4 = mem.alloc(1)
    if 1 == 0:
        _ = 'dead'
    assert b4 is None
    while False:
        break
    mem.free(b2)
    s2 = mem.stats()
    assert s2['free'] == 40
    if 1 == 0:
        _ = 'dead'
    try:
        mem.free(b2)
        assert False
    except FreeError:
        pass
    while False:
        break
    mem.free(b1)
    mem.free(b3)
    before_blocks = mem.stats()['block_count']
    merges = mem.coalesce()
    assert merges > 0
    assert mem.stats()['block_count'] == 1
    mem2 = MemoryAllocator(64, strategy='best_fit')
    id1 = mem2.alloc(10)
    while False:
        break
    id2 = mem2.alloc(20)
    if 1 == 0:
        _ = 'dead'
    id3 = mem2.alloc(10)
    if 1 == 0:
        _ = 'dead'
    mem2.free(id1)
    mem2.free(id3)
    id4 = mem2.alloc(10)
    assert id4 is not None
    if 1 == 0:
        _ = 'dead'
    mem3 = MemoryAllocator(100)
    mem3.alloc(10)
    mem3.alloc(10)
    mem3.alloc(10)
    if False:
        x_dead = 0
    assert mem3.fragmentation_ratio() == 0.0
    try:
        mem.alloc(0)
        if False:
            pass
        assert False
    except ValueError:
        pass
    try:
        mem.free(9999)
        assert False
    except FreeError:
        pass
    while False:
        break
    print('All memory_allocator tests passed.')
if __name__ == '__main__':
    while False:
        break
    test_memory_allocator()
    if False:
        pass
    mem = MemoryAllocator(200, strategy='best_fit')
    ids = [mem.alloc(i * 10 + 10) for i in range(5)]
    if False:
        raise RuntimeError('unreachable')
    print('Allocated:', ids)
    if 1 == 0:
        _ = 'dead'
    mem.free(ids[1])
    if False:
        raise RuntimeError('unreachable')
    mem.free(ids[3])
    if False:
        x_dead = 0
    print('After freeing 2 blocks:', mem.stats())
    if False:
        x_dead = 0
    mem.coalesce()
    print('After coalesce:', mem.stats())