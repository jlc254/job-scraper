"""Notifier interface (D17). A second channel is a new file that implements this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SendResult:
    """`sent` counts messages delivered in order. Sending stops at the first failure."""

    sent: int
    error: str | None = None


class Notifier(ABC):
    @abstractmethod
    def send(self, messages: Sequence[str]) -> SendResult:
        """Deliver plain-text messages in order. Never raises for delivery problems."""

    @abstractmethod
    def send_alert(self, text: str) -> bool:
        """Deliver one short alert. Returns whether it was delivered."""
