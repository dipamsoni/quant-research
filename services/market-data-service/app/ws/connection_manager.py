"""In-process price bus for WebSocket fan-out.

PriceBus dispatches price ticks to per-client asyncio.Queue instances.
Chosen over Redis pub/sub because Phase 2 is single-process; Redis pub/sub
is Phase 10+ (horizontal WS gateway). No network hop, no serialization.

Sequence numbers
----------------
Every published tick is stamped with a monotonically increasing `seq` integer
and stored in a per-symbol ring buffer (maxlen=_BUFFER_SIZE). Reconnecting
clients send `?seq=N`; the server replays all buffered ticks with seq > N.
"""

from __future__ import annotations

import asyncio
import itertools
from collections import defaultdict, deque

import structlog

logger = structlog.get_logger()

_BUFFER_SIZE = 500  # ticks per symbol retained for replay


class PriceBus:
    """Fan-out price ticks to subscribed queues by symbol."""

    def __init__(self) -> None:
        # symbol (uppercase) → set of queues for subscribed WS clients
        self._subscribers: dict[str, set[asyncio.Queue[dict]]] = defaultdict(set)
        # Monotonically increasing sequence counter shared across all symbols.
        self._seq_gen = itertools.count(1)
        # symbol → ring buffer of stamped ticks (most recent _BUFFER_SIZE)
        self._buffer: dict[str, deque[dict]] = defaultdict(lambda: deque(maxlen=_BUFFER_SIZE))

    def subscribe(self, symbols: list[str], queue: asyncio.Queue[dict]) -> None:
        for sym in symbols:
            self._subscribers[sym.upper()].add(queue)

    def unsubscribe(self, symbols: list[str], queue: asyncio.Queue[dict]) -> None:
        for sym in symbols:
            self._subscribers[sym.upper()].discard(queue)

    def publish(self, symbol: str, tick: dict) -> None:
        """Stamp tick with seq, buffer it, put on every subscribed queue."""
        sym = symbol.upper()
        stamped = {**tick, "seq": next(self._seq_gen)}
        self._buffer[sym].append(stamped)
        for q in list(self._subscribers.get(sym, set())):
            try:
                q.put_nowait(stamped)
            except asyncio.QueueFull:
                # slow consumer — drop tick rather than block pipeline
                logger.warning(
                    "ws_tick_dropped",
                    symbol=sym,
                    seq=stamped["seq"],
                    queue_maxsize=q.maxsize,
                )

    def get_missed(self, symbols: list[str], since_seq: int) -> list[dict]:
        """Return buffered ticks across symbols with seq > since_seq, sorted by seq."""
        missed: list[dict] = []
        for sym in symbols:
            for tick in self._buffer.get(sym.upper(), []):
                if tick["seq"] > since_seq:
                    missed.append(tick)
        missed.sort(key=lambda t: t["seq"])
        return missed
