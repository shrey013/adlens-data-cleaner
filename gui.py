"""Modern dark-theme dashboard GUI for AdLens Data Cleaner (animated)."""
from __future__ import annotations

import os
import queue
import threading
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk

import config
from animations import Spinner
from cleaner import AdClarityCleaner, CleaningError
from components import (
    BrandLogo, StatCard, StepChecklist, DeveloperBadge, IdleAnimation,
)
from exporter import export_to_excel

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_MONTH_NAME_TO_NUM = {name: i + 1 for i, name in enumerate(_MONTHS)}

_TIPS = [
    "💡 Tip: The month filter keeps creatives active during your selected month.",
    "💡 Tip: Impressions like 5.4M, 235K and <5K are auto-converted to numbers.",
    "💡 Tip: Duplicate creatives (same filename) are removed automatically.",
    "💡 Tip: Your original file is never modified — a fresh cleaned file is created.",
    "💡 Tip: Results are sorted by impressions, largest first.",
    "💡 Tip: Invalid or unreadable dates are dropped so your data stays clean.",
]

def _build_month_options() -> List[str]:
    options: List[str] = []
    for year in range(config.MONTH_START_YEAR, config.MONTH_END_YEAR + 1):
        for month in _MONTHS:
            options.append(f"{month} {year}")
    return options

class AdLensApp(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode(config.APPEARANCE_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

        self.title(config.APP_NAME)
        self.geometry("1040x780")
        self.minsize(960, 720)
        self.configure(fg_color=config.COLOR_BG)

        self._selected_file: Optional[str] = None
        self._month_options = _build_month_options()
        self._queue: "queue.Queue[tuple]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None

        # Animation state.
        self._processing = False
        self._current_step = "Idle"
        self._dot_count = 0
        self._target_progress = 0.0
        self._display_progress = 0.0
        self._tip_index = 0

        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_controls()
        self._build_stat_cards()
        self._build_main_area()
        self._build_progress()

        # Background loops (thread-safe; never block the UI).
        self.after(100, self._poll_queue)
        self.after(16, self._animate_progress)
        self.after(450, self._animate_dots)
        self.after(4000, self._rotate_tip)

    # ------------------------------------------------------------------ UI

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=config.COLOR_PANEL, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        BrandLogo(header, size=46).grid(row=0, column=0, padx=(20, 12), pady=14)

        titlebox = ctk.CTkFrame(header, fg_color="transparent")
        titlebox.grid(row=0, column=1, sticky="w", pady=12)
        ctk.CTkLabel(
            titlebox, text=config.APP_NAME,
            font=ctk.CTkFont(size=23, weight="bold"), text_color=config.COLOR_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            titlebox, text=f"v{config.APP_VERSION}   •   AdClarity Export Cleaner",
            font=ctk.CTkFont(size=12), text_color=config.COLOR_SUBTLE,
        ).pack(anchor="w")

        DeveloperBadge(header).grid(row=0, column=2, sticky="e", padx=16, pady=10)

    def _build_controls(self) -> None:
        card = ctk.CTkFrame(self, fg_color=config.COLOR_PANEL, corner_radius=14)
        card.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 8))
        card.grid_columnconfigure(1, weight=1)

        self.browse_btn = ctk.CTkButton(
            card, text="Browse", width=130, height=40, corner_radius=10,
            fg_color=config.COLOR_ACCENT, hover_color=config.COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"), command=self._on_browse,
        )
        self.browse_btn.grid(row=0, column=0, padx=(16, 12), pady=14, sticky="w")

        self.file_label = ctk.CTkLabel(
            card, text="No file selected", anchor="w",
            text_color=config.COLOR_SUBTLE, font=ctk.CTkFont(size=13),
        )
        self.file_label.grid(row=0, column=1, columnspan=3, padx=(0, 16), pady=14, sticky="ew")

        ctk.CTkLabel(
            card, text="Target Month", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_TEXT,
        ).grid(row=1, column=0, padx=(16, 12), pady=(0, 14), sticky="w")

        self.month_var = ctk.StringVar(value=self._month_options[0])
        self.month_menu = ctk.CTkOptionMenu(
            card, values=self._month_options, variable=self.month_var,
            width=200, height=38, corner_radius=10,
            fg_color=config.COLOR_CARD, button_color=config.COLOR_ACCENT,
            button_hover_color=config.COLOR_ACCENT_HOVER,
        )
        self.month_menu.grid(row=1, column=1, padx=(0, 24), pady=(0, 14), sticky="w")

        ctk.CTkLabel(
            card, text="Minimum Impression", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_TEXT,
        ).grid(row=1, column=2, padx=(0, 12), pady=(0, 14), sticky="w")

        self.min_entry = ctk.CTkEntry(
            card, width=160, height=38, corner_radius=10,
            fg_color=config.COLOR_CARD, font=ctk.CTkFont(size=13),
        )
        self.min_entry.insert(0, str(config.DEFAULT_MIN_IMPRESSION))
        self.min_entry.grid(row=1, column=3, padx=(0, 16), pady=(0, 14), sticky="w")

        self.start_btn = ctk.CTkButton(
            card, text="Start Cleaning", height=44, corner_radius=12,
            fg_color=config.COLOR_SUCCESS, hover_color="#16A34A",
            font=ctk.CTkFont(size=15, weight="bold"), command=self._on_start,
        )
        self.start_btn.grid(row=2, column=0, columnspan=4, padx=16, pady=(0, 16), sticky="ew")

    def _build_stat_cards(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))
        for c in range(4):
            wrap.grid_columnconfigure(c, weight=1, uniform="stats")

        self.card_kept = StatCard(wrap, "Creatives Kept", "🎯", config.COLOR_SUCCESS)
        self.card_top = StatCard(wrap, "Top Impressions", "🔥", config.COLOR_ACCENT)
        self.card_range = StatCard(wrap, "Date Range", "📅", config.COLOR_TEXT)
        self.card_types = StatCard(wrap, "Image / Video", "🖼️", config.COLOR_TEXT)

        for i, card in enumerate(
            (self.card_kept, self.card_top, self.card_range, self.card_types)
        ):
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))

    def _build_main_area(self) -> None:
        self.grid_rowconfigure(3, weight=1)
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=3, column=0, sticky="nsew", padx=20, pady=8)
        main.grid_columnconfigure(0, minsize=230)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Left: pipeline checklist.
        self.checklist = StepChecklist(main, config.PROGRESS_STEPS)
        self.checklist.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Right: log + idle animation (share the same cell).
        log = ctk.CTkFrame(main, fg_color=config.COLOR_PANEL, corner_radius=12)
        log.grid(row=0, column=1, sticky="nsew")
        log.grid_rowconfigure(1, weight=1)
        log.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            log, text="Activity Log", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        # Idle animation (shown before/when nothing is running).
        self.idle_anim = IdleAnimation(log, bg=config.COLOR_CARD)
        self.idle_anim.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.idle_anim.start()

        # Status log (hidden until a run starts).
        self.status_box = ctk.CTkTextbox(
            log, corner_radius=10, fg_color=config.COLOR_CARD,
            font=ctk.CTkFont(size=12), text_color=config.COLOR_TEXT,
        )
        self.status_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.status_box.configure(state="disabled")
        self.status_box.grid_remove()   # hidden initially

    def _build_progress(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=config.COLOR_PANEL, corner_radius=14)
        footer.grid(row=4, column=0, sticky="ew", padx=20, pady=(8, 18))
        footer.grid_columnconfigure(1, weight=1)

        self.spinner = Spinner(
            footer, size=26, thickness=4,
            color=config.COLOR_ACCENT, track=config.COLOR_CARD, bg=config.COLOR_PANEL,
        )
        self.spinner.grid(row=0, column=0, padx=(18, 10), pady=(12, 2))
        self.spinner.grid_remove()

        self.step_label = ctk.CTkLabel(
            footer, text="Idle", anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLOR_SUBTLE,
        )
        self.step_label.grid(row=0, column=1, sticky="w", pady=(12, 2))

        self.pct_label = ctk.CTkLabel(
            footer, text="0%", anchor="e",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=config.COLOR_ACCENT,
        )
        self.pct_label.grid(row=0, column=2, sticky="e", padx=18, pady=(12, 2))

        self.progress = ctk.CTkProgressBar(
            footer, height=16, corner_radius=8, progress_color=config.COLOR_ACCENT,
        )
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(2, 8))
        self.progress.set(0)

        self.tip_label = ctk.CTkLabel(
            footer, text=_TIPS[0], anchor="w",
            font=ctk.CTkFont(size=11), text_color=config.COLOR_SUBTLE,
        )
        self.tip_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=18, pady=(0, 12))

    # -------------------------------------------------------------- helpers

    def _append_status(self, message: str) -> None:
        self.status_box.configure(state="normal")
        self.status_box.insert("end", f"• {message}\n")
        self.status_box.see("end")
        self.status_box.configure(state="disabled")

    def _clear_status(self) -> None:
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.configure(state="disabled")

    def _set_controls_state(self, state: str) -> None:
        for widget in (self.browse_btn, self.month_menu, self.min_entry, self.start_btn):
            widget.configure(state=state)

    def _reset_cards(self) -> None:
        for card in (self.card_kept, self.card_top, self.card_range, self.card_types):
            card.reset()

    # ---------------------------------------------------------- animations

    def _animate_progress(self) -> None:
        diff = self._target_progress - self._display_progress
        if abs(diff) > 0.002:
            self._display_progress += diff * 0.18
            self._display_progress = max(0.0, min(1.0, self._display_progress))
            self.progress.set(self._display_progress)
            self.pct_label.configure(text=f"{int(round(self._display_progress * 100))}%")
        self.after(16, self._animate_progress)

    def _animate_dots(self) -> None:
        if self._processing:
            self._dot_count = (self._dot_count + 1) % 4
            self.step_label.configure(text=self._current_step + "." * self._dot_count)
        self.after(450, self._animate_dots)

    def _rotate_tip(self) -> None:
        self._tip_index = (self._tip_index + 1) % len(_TIPS)
        self.tip_label.configure(text=_TIPS[self._tip_index])
        self.after(4000, self._rotate_tip)

    def _flash_success(self, count: int = 0) -> None:
        shades = [config.COLOR_SUCCESS, "#15803D"]
        self.progress.configure(progress_color=shades[count % 2])
        if count < 5:
            self.after(140, lambda: self._flash_success(count + 1))
        else:
            self.progress.configure(progress_color=config.COLOR_SUCCESS)

    # ------------------------------------------------------------- handlers

    def _on_browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Raw AdClarity Excel",
            filetypes=[("Excel files", "*.xlsx *.xls")],
        )
        if not path:
            return
        if os.path.splitext(path)[1].lower() not in config.ALLOWED_EXTENSIONS:
            messagebox.showerror(config.APP_NAME, "Invalid Excel: please select a .xlsx or .xls file.")
            return
        self._selected_file = path
        self.file_label.configure(text=os.path.basename(path), text_color=config.COLOR_TEXT)

    def _on_start(self) -> None:
        if not self._selected_file:
            messagebox.showerror(config.APP_NAME, "Please select a raw AdClarity Excel file first.")
            return

        month_str = self.month_var.get()
        if month_str not in self._month_options:
            messagebox.showerror(config.APP_NAME, "Invalid Month: please choose a target month.")
            return
        try:
            month_name, year_str = month_str.split()
            target_month = _MONTH_NAME_TO_NUM[month_name]
            target_year = int(year_str)
        except (ValueError, KeyError):
            messagebox.showerror(config.APP_NAME, "Invalid Month: please choose a valid month.")
            return

        raw_min = self.min_entry.get().strip().replace(",", "")
        if not raw_min.isdigit():
            messagebox.showerror(config.APP_NAME, "Invalid Impression: enter a non-negative whole number.")
            return
        min_impression = int(raw_min)

        # Lock UI + reset dashboard, then start animations.
        self._set_controls_state("disabled")
        self._clear_status()
        self._reset_cards()
        self.checklist.reset()

        # Swap idle animation for the live log.
        self.idle_anim.stop()
        self.idle_anim.grid_remove()
        self.status_box.grid()

        self._target_progress = 0.0
        self._display_progress = 0.0
        self.progress.set(0)
        self.progress.configure(progress_color=config.COLOR_ACCENT)
        self.pct_label.configure(text="0%")
        self._processing = True
        self._current_step = "Starting"
        self.step_label.configure(text="Starting", text_color=config.COLOR_ACCENT)
        self.spinner.grid()
        self.spinner.start()

        self._worker = threading.Thread(
            target=self._worker_run,
            args=(self._selected_file, target_year, target_month, min_impression),
            daemon=True,
        )
        self._worker.start()

    # -------------------------------------------------------------- threading

    def _worker_run(self, file_path, target_year, target_month, min_impression) -> None:
        def callback(step: str, status: str, pct: float) -> None:
            self._queue.put(("progress", step, status, pct))

        try:
            cleaner = AdClarityCleaner(progress_callback=callback)
            df = cleaner.clean(file_path, target_year, target_month, min_impression)

            self._queue.put(("progress", "Exporting Excel", "Exporting Excel", 0.96))
            output_path = export_to_excel(df, file_path)

            stats = self._compute_stats(df)
            self._queue.put(("progress", "Completed", "Export Complete", 1.0))
            self._queue.put(("done", output_path, len(df), stats))
        except CleaningError as exc:
            self._queue.put(("error", str(exc)))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", f"Unexpected error: {exc}"))

    @staticmethod
    def _compute_stats(df) -> dict:
        top = int(df["Impressions"].max()) if len(df) else 0
        if len(df):
            d_from = df["First Seen"].min().strftime("%b %Y")
            d_to = df["Last Seen"].max().strftime("%b %Y")
            date_range = f"{d_from} – {d_to}"
        else:
            date_range = "—"
        exts = df["Filename"].astype(str).str.rsplit(".", n=1).str[-1].str.lower()
        images = int(exts.isin(["jpeg", "jpg", "png", "gif", "webp"]).sum())
        videos = int(exts.isin(["mp4", "mov", "avi", "webm"]).sum())
        return {"top": top, "range": date_range, "images": images, "videos": videos}

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self._queue.get_nowait()
                kind = msg[0]

                if kind == "progress":
                    _, step, status, pct = msg
                    self._target_progress = pct
                    self._current_step = step
                    self.checklist.set_active(step)
                    self._append_status(status)

                elif kind == "done":
                    _, output_path, count, stats = msg
                    self._processing = False
                    self.spinner.stop()
                    self.spinner.grid_remove()
                    self.checklist.mark_all_done()
                    self._target_progress = 1.0
                    self._display_progress = 1.0
                    self.progress.set(1.0)
                    self.pct_label.configure(text="100%")
                    self.step_label.configure(text="Completed ✓", text_color=config.COLOR_SUCCESS)
                    self._flash_success()

                    self.card_kept.count_up(count)
                    self.card_top.set_text(f"{stats['top']:,}")
                    self.card_range.set_text(stats["range"])
                    self.card_types.set_text(f"{stats['images']:,} / {stats['videos']:,}")

                    self._set_controls_state("normal")
                    self._append_status(f"Done — {count} creative(s) exported.")
                    messagebox.showinfo(
                        "Cleaning Completed Successfully",
                        "Cleaning Completed Successfully\n\n"
                        f"Output Saved:\n{os.path.basename(output_path)}\n\n"
                        f"Location:\n{output_path}",
                    )

                elif kind == "error":
                    _, message = msg
                    self._processing = False
                    self.spinner.stop()
                    self.spinner.grid_remove()
                    self._target_progress = 0.0
                    self._display_progress = 0.0
                    self.progress.set(0)
                    self.pct_label.configure(text="0%")
                    self.step_label.configure(text="Error", text_color="#EF4444")
                    self._set_controls_state("normal")
                    self._append_status(f"Error: {message}")
                    messagebox.showerror(config.APP_NAME, message)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)