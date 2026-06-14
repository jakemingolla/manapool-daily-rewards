"""Output seam: a thin abstraction over stdout/stderr and debug logging."""

from __future__ import annotations

import sys
from typing import Protocol, TextIO


class Console(Protocol):
    """Where user-facing and diagnostic output is written."""

    def out(self, message: str) -> None:
        """Write a normal line to standard output."""
        ...

    def err(self, message: str) -> None:
        """Write a line to standard error."""
        ...

    def debug(self, message: str) -> None:
        """Write a diagnostic line (only when debugging is enabled)."""
        ...


class StreamConsole:
    """``Console`` backed by real text streams (defaults to stdout/stderr)."""

    def __init__(
        self,
        *,
        debug: bool = False,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self._debug = debug
        self._stdout = stdout if stdout is not None else sys.stdout
        self._stderr = stderr if stderr is not None else sys.stderr

    def out(self, message: str) -> None:
        print(message, file=self._stdout)

    def err(self, message: str) -> None:
        print(message, file=self._stderr)

    def debug(self, message: str) -> None:
        if self._debug:
            print(message, file=self._stderr)
