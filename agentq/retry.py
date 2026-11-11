from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    """How many times a task may run before it is given up on."""

    max_attempts: int = 3
    base_delay_s: float = 0.5

    def should_retry(self, attempts: int) -> bool:
        return attempts < self.max_attempts

    def delay(self, attempts: int) -> float:
        return self.base_delay_s * (2 ** max(attempts - 1, 0))
