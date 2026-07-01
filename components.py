"""Reusable dashboard widgets: brand logo, stat cards, pipeline checklist,
developer badge, and an idle animation to keep the screen lively."""
from __future__ import annotations

import math
import random
import tkinter as tk

import customtkinter as ctk

import config

class BrandLogo(tk.Canvas):
    """A simple drawn magnifying-glass ('lens') logo for AdLens."""

    def __init__(self, master, size: int = 44, bg: str = config.COLOR_PANEL,
                 ring: str = config.COLOR_ACCENT, glass: str = config.COLOR_BG) -> None:
        super().__init__(master, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0)
        pad = size * 0.12
        d = size * 0.60
        ring_w = max(3, int(size * 0.08))
        # Tinted glass + lens ring.
        self.create_oval(pad + d * 0.16, pad + d * 0.16, pad + d * 0.84, pad + d * 0.84,
                         outline="", fill=glass)
        self.create_oval(pad, pad, pad + d, pad + d, outline=ring, width=ring_w)
        # Handle.
        hx, hy = pad + d * 0.78, pad + d * 0.78
        self.create_line(hx, hy, size - pad * 0.5, size - pad * 0.5,
                         fill=ring, width=max(4, int(size * 0.11)), capstyle="round")

class StatCard(ctk.CTkFrame):
    """A small dashboard metric card with an optional count-up animation."""

    def __init__(self, master, title: str, icon: str = "",
                 accent: str = config.COLOR_ACCENT) -> None:
        super().__init__(master, fg_color=config.COLOR_CARD, corner_radius=12)
        self.grid_columnconfigure(0, weight=1)
        self._anim_job = None

        ctk.CTkLabel(
            self, text=f"{icon}  {title}".strip(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config.COLOR_SUBTLE, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))

        self.value_label = ctk.CTkLabel(
            self, text="—", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=accent, anchor="w",
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))

    def _cancel(self) -> None:
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

    def set_text(self, text: str) -> None:
        self._cancel()
        self.value_label.configure(text=text)

    def count_up(self, target: int, suffix: str = "", steps: int = 28) -> None:
        """Animate the value rising from 0 to target."""
        self._cancel()
        inc = max(1, target // steps) if target else 1

        def tick(val: int) -> None:
            val = min(val, target)
            self.value_label.configure(text=f"{val:,}{suffix}")
            if val < target:
                self._anim_job = self.after(22, lambda: tick(val + inc))
            else:
                self._anim_job = None

        tick(0)

    def reset(self) -> None:
        self.set_text("—")

class StepChecklist(ctk.CTkFrame):
    """A vertical pipeline checklist that lights up as steps complete."""

    PENDING, ACTIVE, DONE = "○", "◆", "✓"

    def __init__(self, master, steps) -> None:
        super().__init__(master, fg_color=config.COLOR_CARD, corner_radius=12)
        self._steps = list(steps)
        self._rows = {}

        ctk.CTkLabel(
            self, text="Pipeline", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_TEXT, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))

        for i, name in enumerate(self._steps, start=1):
            icon = ctk.CTkLabel(
                self, text=self.PENDING, width=18,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=config.COLOR_SUBTLE,
            )
            icon.grid(row=i, column=0, sticky="w", padx=(14, 4), pady=2)
            lbl = ctk.CTkLabel(
                self, text=name, font=ctk.CTkFont(size=12),
                text_color=config.COLOR_SUBTLE, anchor="w",
            )
            lbl.grid(row=i, column=1, sticky="w", padx=(0, 14), pady=2)
            self._rows[name] = (icon, lbl)

    def reset(self) -> None:
        for icon, lbl in self._rows.values():
            icon.configure(text=self.PENDING, text_color=config.COLOR_SUBTLE)
            lbl.configure(text_color=config.COLOR_SUBTLE)

    def set_active(self, step: str) -> None:
        """Mark all steps before `step` done, `step` active, rest pending."""
        if step not in self._rows:
            return
        idx = self._steps.index(step)
        for i, name in enumerate(self._steps):
            icon, lbl = self._rows[name]
            if i < idx:
                icon.configure(text=self.DONE, text_color=config.COLOR_SUCCESS)
                lbl.configure(text_color=config.COLOR_TEXT)
            elif i == idx:
                icon.configure(text=self.ACTIVE, text_color=config.COLOR_ACCENT)
                lbl.configure(text_color=config.COLOR_ACCENT)
            else:
                icon.configure(text=self.PENDING, text_color=config.COLOR_SUBTLE)
                lbl.configure(text_color=config.COLOR_SUBTLE)

    def mark_all_done(self) -> None:
        for icon, lbl in self._rows.values():
            icon.configure(text=self.DONE, text_color=config.COLOR_SUCCESS)
            lbl.configure(text_color=config.COLOR_TEXT)

class DeveloperBadge(ctk.CTkFrame):
    """A polished developer credit badge with avatar + pulsing 'online' dot."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color=config.COLOR_CARD, corner_radius=14)
        self._t = 0.0

        self.avatar = tk.Canvas(
            self, width=46, height=46, bg=config.COLOR_CARD,
            highlightthickness=0, bd=0,
        )
        self.avatar.grid(row=0, column=0, rowspan=3, padx=(14, 12), pady=12)

        ctk.CTkLabel(
            self, text="DESIGNED & DEVELOPED BY",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=config.COLOR_SUBTLE,
        ).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=(12, 0))

        ctk.CTkLabel(
            self, text=config.AUTHOR_NAME,
            font=ctk.CTkFont(size=15, weight="bold"), text_color=config.COLOR_TEXT,
        ).grid(row=1, column=1, sticky="w", padx=(0, 16))

        # Colorful email emoji instead of a plain symbol.
        ctk.CTkLabel(
            self, text=f"📧  {config.AUTHOR_EMAIL}",
            font=ctk.CTkFont(size=11), text_color=config.COLOR_ACCENT,
        ).grid(row=2, column=1, sticky="w", padx=(0, 16), pady=(0, 12))

        self._animate_badge()

    def _initials(self) -> str:
        parts = config.AUTHOR_NAME.split()
        first = parts[0][0] if parts else "?"
        last = parts[-1][0] if len(parts) > 1 else ""
        return (first + last).upper()

    def _animate_badge(self) -> None:
        if not self.winfo_exists():
            return
        self._t += 0.08
        self._draw_avatar()
        self.after(50, self._animate_badge)

    def _draw_avatar(self) -> None:
        c = self.avatar
        c.delete("all")
        # Deep, mature circular base with a subtle ring.
        c.create_oval(2, 2, 44, 44, fill="#0F1115", outline=config.COLOR_ACCENT, width=2)
        # Crisp "</>" developer code emblem (vector = always sharp).
        # Left chevron  <
        c.create_line(18, 16, 12, 23, fill=config.COLOR_ACCENT, width=2, capstyle="round")
        c.create_line(12, 23, 18, 30, fill=config.COLOR_ACCENT, width=2, capstyle="round")
        # Right chevron  >
        c.create_line(28, 16, 34, 23, fill=config.COLOR_ACCENT, width=2, capstyle="round")
        c.create_line(34, 23, 28, 30, fill=config.COLOR_ACCENT, width=2, capstyle="round")
        # Center slash  /
        c.create_line(25, 14, 21, 32, fill="white", width=2, capstyle="round")
        # Pulsing green 'online' dot, bottom-right.
        pulse = (math.sin(self._t) + 1) / 2
        r = 5 + pulse * 1.6
        c.create_oval(38 - r, 38 - r, 38 + r, 38 + r,
                      fill=config.COLOR_SUCCESS, outline=config.COLOR_CARD, width=2)
class IdleAnimation(tk.Canvas):
    """A looping, on-theme idle animation: twinkling particles, an
    'impressions' equalizer, and a friendly greeting. Fills empty space."""

    def __init__(self, master, width: int = 560, height: int = 300,
                 bg: str = config.COLOR_CARD) -> None:
        super().__init__(master, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0)
        # NOTE: do NOT use self._w / self._h — Tkinter reserves self._w
        # for the widget's path name. Use _cw / _ch instead.
        self._cw, self._ch = width, height
        self._running = False
        self._job = None
        self._t = 0.0

        self._stars = [
            {"x": random.uniform(0, width), "y": random.uniform(0, height * 0.55),
             "r": random.uniform(1.0, 2.4), "ph": random.uniform(0, math.tau),
             "sp": random.uniform(1.5, 3.5)}
            for _ in range(38)
        ]
        self._bars = [random.uniform(0.2, 1.0) for _ in range(11)]
        self._targets = list(self._bars)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        self._cw, self._ch = event.width, event.height

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._loop()

    def stop(self) -> None:
        self._running = False
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def _loop(self) -> None:
        if not self._running or not self.winfo_exists():
            return
        self._t += 0.05
        self._render()
        self._job = self.after(45, self._loop)

    def _render(self) -> None:
        self.delete("all")
        w, h = self._cw, self._ch

        # Twinkling data particles.
        for s in self._stars:
            tw = (math.sin(self._t * s["sp"] + s["ph"]) + 1) / 2
            shade = int(60 + tw * 120)
            b = min(255, shade + 25)
            color = f"#{shade:02x}{shade:02x}{b:02x}"
            self.create_oval(s["x"] - s["r"], s["y"] - s["r"],
                             s["x"] + s["r"], s["y"] + s["r"],
                             fill=color, outline="")

        # Friendly greeting.
        self.create_text(w / 2, h * 0.34, text="Ready when you are  ✨",
                         fill=config.COLOR_TEXT, font=("Helvetica", 16, "bold"))
        self.create_text(w / 2, h * 0.34 + 26,
                         text="Select a raw AdClarity file and press Start Cleaning",
                         fill=config.COLOR_SUBTLE, font=("Helvetica", 11))

        # Pulsing 'impressions' equalizer.
        n = len(self._bars)
        bw = (w * 0.5) / n
        gap = bw * 0.45
        total = n * bw + (n - 1) * gap
        x0 = (w - total) / 2
        base_y = h * 0.86
        max_bh = h * 0.26
        for i in range(n):
            self._bars[i] += (self._targets[i] - self._bars[i]) * 0.15
            if abs(self._bars[i] - self._targets[i]) < 0.03:
                self._targets[i] = random.uniform(0.15, 1.0)
            bh = max_bh * self._bars[i]
            x = x0 + i * (bw + gap)
            self.create_rectangle(x, base_y - bh, x + bw, base_y,
                                  fill=config.COLOR_ACCENT, outline="")