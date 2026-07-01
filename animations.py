"""Lightweight, dependency-free UI animations for AdLens Data Cleaner."""
from __future__ import annotations

import tkinter as tk

class Spinner(tk.Canvas):
    """A smooth rotating-arc loading spinner drawn on a Tk canvas.

    Uses the widget's own `after` loop, so it never blocks the UI thread.
    """

    def __init__(
        self,
        master,
        size: int = 26,
        thickness: int = 4,
        color: str = "#3B82F6",
        track: str = "#22262F",
        bg: str = "#1A1D24",
        interval: int = 40,
        step: int = 18,
        arc_length: int = 100,
    ) -> None:
        super().__init__(
            master, width=size, height=size, bg=bg,
            highlightthickness=0, bd=0,
        )
        self._size = size
        self._thickness = thickness
        self._color = color
        self._track = track
        self._interval = interval        # ms between frames
        self._step = step                # degrees rotated per frame
        self._arc_length = arc_length    # length of the moving arc (degrees)
        self._angle = 0
        self._running = False
        self._job = None
        self._render()

    def _render(self) -> None:
        self.delete("all")
        pad = self._thickness + 2
        box = (pad, pad, self._size - pad, self._size - pad)
        # Faint full-circle track.
        self.create_oval(*box, outline=self._track, width=self._thickness)
        # Bright moving arc segment.
        self.create_arc(
            *box, start=self._angle, extent=self._arc_length,
            style="arc", outline=self._color, width=self._thickness,
        )

    def _tick(self) -> None:
        if not self._running:
            return
        self._angle = (self._angle - self._step) % 360
        self._render()
        self._job = self.after(self._interval, self._tick)

    def start(self) -> None:
        """Begin spinning (idempotent)."""
        if not self._running:
            self._running = True
            self._tick()

    def stop(self) -> None:
        """Stop spinning and cancel the pending frame."""
        self._running = False
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None