from __future__ import annotations

import statistics
import time

from app.risk import AccountActivitySnapshot, score_order, score_transfer
from app.schemas import OrderCreate, TransferCreate


def benchmark_transfer(iterations: int) -> list[float]:
    payload = TransferCreate(
        sender_account_id="acct_bench",
        destination_address="0xabc123456789def0",
        asset_symbol="ETH",
        amount=12500,
        memo="benchmark",
        idempotency_key="bench-transfer-key",
    )
    activity = AccountActivitySnapshot(transfer_count=2, order_count=1)
    latencies_ms: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter()
        score_transfer(payload, activity)
        latencies_ms.append((time.perf_counter() - start) * 1000)

    return latencies_ms


def benchmark_order(iterations: int) -> list[float]:
    payload = OrderCreate(
        account_id="acct_bench",
        symbol="BTC-USD",
        side="buy",
        quantity=1.25,
        limit_price=67500,
        idempotency_key="bench-order-key",
    )
    activity = AccountActivitySnapshot(transfer_count=2, order_count=1)
    latencies_ms: list[float] = []

    for _ in range(iterations):
        start = time.perf_counter()
        score_order(payload, activity)
        latencies_ms.append((time.perf_counter() - start) * 1000)

    return latencies_ms


def print_summary(label: str, latencies_ms: list[float]) -> None:
    p95_index = max(0, min(len(latencies_ms) - 1, int(len(latencies_ms) * 0.95) - 1))
    sorted_latencies = sorted(latencies_ms)
    print(f"{label} benchmark")
    print(f"  samples: {len(latencies_ms)}")
    print(f"  mean latency:   {statistics.mean(latencies_ms):.4f} ms")
    print(f"  median latency: {statistics.median(latencies_ms):.4f} ms")
    print(f"  p95 latency:    {sorted_latencies[p95_index]:.4f} ms")
    print(f"  min latency:    {min(latencies_ms):.4f} ms")
    print(f"  max latency:    {max(latencies_ms):.4f} ms")


if __name__ == "__main__":
    transfer_latencies = benchmark_transfer(iterations=2000)
    order_latencies = benchmark_order(iterations=2000)
    print_summary("Transfer risk engine", transfer_latencies)
    print_summary("Order risk engine", order_latencies)
