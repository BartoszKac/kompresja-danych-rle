"""Skala osi wykresu: zamienia wartość na pozycję i wyznacza podziałkę."""

import math
from dataclasses import dataclass

NICE_MULTIPLIERS = (1, 2, 5)
TARGET_LINEAR_TICKS = 5
MAX_LOG_TICKS = 9


@dataclass(frozen=True)
class ValueScale:
    minimum: float
    maximum: float
    baseline: float
    is_log: bool

    @classmethod
    def for_values(
        cls, values: list[float], baseline: float | None, is_log: bool
    ) -> "ValueScale":
        """Skala obejmuje wszystkie wartości i punkt odniesienia, od którego rosną słupki."""
        lowest = min(values)
        if baseline is None:
            baseline = _nice_floor(lowest) if is_log else 0.0
        return cls(min(lowest, baseline), max(*values, baseline), baseline, is_log)

    def fraction(self, value: float) -> float:
        """Pozycja wartości na osi: 0 to początek, a 1 koniec."""
        low, high, position = self.minimum, self.maximum, value
        if self.is_log:
            low, high, position = math.log10(low), math.log10(high), math.log10(value)
        if high == low:
            return 0.0
        return (position - low) / (high - low)

    def ticks(self) -> list[float]:
        return self._log_ticks() if self.is_log else self._linear_ticks()

    def _linear_ticks(self) -> list[float]:
        span = self.maximum - self.minimum
        if span == 0:
            return [self.baseline]
        step = _nice_step(span / TARGET_LINEAR_TICKS)
        first = math.ceil(self.minimum / step)
        last = math.floor(self.maximum / step)
        return [index * step for index in range(first, last + 1)]

    def _log_ticks(self) -> list[float]:
        first_decade = math.floor(math.log10(self.minimum))
        last_decade = math.ceil(math.log10(self.maximum))
        all_ticks = _ticks_in_range(first_decade, last_decade, NICE_MULTIPLIERS, self)
        if len(all_ticks) <= MAX_LOG_TICKS:
            return all_ticks
        return _ticks_in_range(first_decade, last_decade, (1,), self)


def _ticks_in_range(
    first_decade: int, last_decade: int, multipliers: tuple[int, ...], scale: ValueScale
) -> list[float]:
    candidates = (
        multiplier * 10.0**decade
        for decade in range(first_decade, last_decade + 1)
        for multiplier in multipliers
    )
    return [tick for tick in candidates if scale.minimum <= tick <= scale.maximum]


def _nice_step(rough_step: float) -> float:
    decade = 10.0 ** math.floor(math.log10(rough_step))
    for multiplier in NICE_MULTIPLIERS:
        if rough_step <= multiplier * decade:
            return multiplier * decade
    return 10 * decade


def _nice_floor(value: float) -> float:
    """Największa „ładna” liczba (1, 2 lub 5 razy potęga 10) nie większa od wartości."""
    decade = 10.0 ** math.floor(math.log10(value))
    return max(
        multiplier * decade for multiplier in NICE_MULTIPLIERS if multiplier * decade <= value
    )
