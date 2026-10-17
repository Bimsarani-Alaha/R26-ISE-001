import uuid
from contextlib import contextmanager
from typing import Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

_shared_progress: Optional[Progress] = None


def _build_columns() -> list:
    return [
        SpinnerColumn(finished_text=" "),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ]


def _get_shared_progress() -> Progress:
    global _shared_progress
    if _shared_progress is None:
        _shared_progress = Progress(*_build_columns())
        _shared_progress.start()
    return _shared_progress


def new_request_id() -> str:
    return uuid.uuid4().hex[:8]


class PipelineProgress:
    """One row per request in a shared terminal progress display."""

    def __init__(
        self,
        label: str,
        total_stages: int,
        console: Optional[Console] = None,
    ):
        self.history: list[str] = []
        self._done = False
        self._total = total_stages
        if console is None:
            self._progress = _get_shared_progress()
            self._owned = False
        else:
            self._progress = Progress(*_build_columns(), console=console)
            self._progress.start()
            self._owned = True
        self._task_id = self._progress.add_task(label, total=total_stages)

    @contextmanager
    def stage(self, name: str):
        self.history.append(name)
        self._progress.update(self._task_id, description=f"{name}...")
        yield
        self._progress.advance(self._task_id, 1)

    def finish(self):
        if self._done:
            return
        self._done = True
        self._progress.update(
            self._task_id,
            description="[green]✓ Done[/green]",
            completed=self._total,
        )

    def fail(self):
        if self._done:
            return
        self._done = True
        self._progress.update(
            self._task_id,
            description="[red]✗ Failed[/red]",
        )

    def close(self):
        """Stop the display. Only used when this instance owns it (tests)."""
        if self._owned:
            self._progress.stop()
