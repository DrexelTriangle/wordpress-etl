import threading

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, Label, ListItem, ListView, RichLog


class _EditScreen(ModalScreen):
    def __init__(self, field: str, current: str) -> None:
        super().__init__()
        self._field = field
        self._current = current

    def compose(self) -> ComposeResult:
        yield Label(f"Edit {self._field}:")
        yield Input(value=self._current)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class _ConflictScreen(ModalScreen):
    """Resolve differing fields between two author records."""

    BINDINGS = [
        Binding("l", "pick_left", "Left"),
        Binding("r", "pick_right", "Right"),
        Binding("e", "edit", "Edit"),
        Binding("enter", "confirm", "Confirm", priority=True),
        Binding("q", "cancel", "Cancel"),
    ]

    def __init__(self, diffs: list, left: dict, right: dict, index: int, total: int) -> None:
        super().__init__()
        self._diffs = diffs
        self._left = left
        self._right = right
        self._index = index
        self._total = total
        self._choices: dict = {}
        self._keys = [k for k, _, _ in diffs]

    def compose(self) -> ComposeResult:
        yield Label(
            f"Conflict {self._index + 1}/{self._total}"
            "  —  L: left  R: right  E: edit  Enter: confirm"
        )
        yield DataTable(cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("FIELD", key="field")
        table.add_column("LEFT", key="left")
        table.add_column("CHOSEN", key="chosen")
        table.add_column("RIGHT", key="right")
        for key, lval, rval in self._diffs:
            table.add_row(key, lval, "", rval, key=key)

    def _active_key(self) -> str | None:
        idx = self.query_one(DataTable).cursor_row
        return self._keys[idx] if 0 <= idx < len(self._keys) else None

    def _advance(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row < len(self._keys) - 1:
            table.move_cursor(row=table.cursor_row + 1)

    def action_pick_left(self) -> None:
        key = self._active_key()
        if key is None:
            return
        lval = next((l for k, l, _ in self._diffs if k == key), "")
        self._choices[key] = self._left.get(key)
        self.query_one(DataTable).update_cell(key, "chosen", lval or "")
        self._advance()

    def action_pick_right(self) -> None:
        key = self._active_key()
        if key is None:
            return
        rval = next((r for k, _, r in self._diffs if k == key), "")
        self._choices[key] = self._right.get(key)
        self.query_one(DataTable).update_cell(key, "chosen", rval or "")
        self._advance()

    def action_edit(self) -> None:
        key = self._active_key()
        if key is None:
            return
        current = str(self._choices.get(key) or "")

        def apply(value) -> None:
            if value is not None:
                self._choices[key] = value
                self.query_one(DataTable).update_cell(key, "chosen", value)

        self.app.push_screen(_EditScreen(key, current), apply)

    def action_confirm(self) -> None:
        missing = [k for k, _, _ in self._diffs if k not in self._choices]
        if missing:
            self.notify(f"Unresolved: {', '.join(missing)}", severity="error")
            return
        self.dismiss(self._choices)

    def action_cancel(self) -> None:
        self.dismiss(None)


class _SelectScreen(ModalScreen):
    """Pick one candidate from a list."""

    BINDINGS = [
        Binding("u", "unknown", "Unknown"),
    ]

    def __init__(self, prompt: str, options: list, fmt=None) -> None:
        super().__init__()
        self._prompt = prompt
        self._options = options
        self._fmt = fmt or (lambda i, o: str(o))

    def compose(self) -> ComposeResult:
        yield Label(self._prompt)
        yield ListView(*[ListItem(Label(self._fmt(i, opt))) for i, opt in enumerate(self._options)])
        yield Label("↑↓: navigate  Enter: select  U: unknown")

    def on_mount(self) -> None:
        self.query_one(ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(self.query_one(ListView).index)

    def action_unknown(self) -> None:
        self.dismiss(-1)


class ETLApp(App):
    """Runs the ETL pipeline in a worker thread and displays progress."""

    BINDINGS = [Binding("q", "quit", "Quit")]

    CSS = """
    RichLog { height: 1fr; }
    #status { height: 1; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, pipeline_fn) -> None:
        super().__init__()
        self._pipeline_fn = pipeline_fn

    def compose(self) -> ComposeResult:
        yield RichLog(id="log", highlight=True, markup=True)
        yield Label("Starting...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._run, thread=True, exclusive=True)

    def _run(self) -> None:
        try:
            self._pipeline_fn(self)
        except SystemExit:
            pass
        except Exception as exc:
            self.call_from_thread(self._write, f"[red]✗[/] [dim]Fatal: {exc}[/]")
        finally:
            self.call_from_thread(self._set_status, "Done — press Q to exit")

    # ── called from the worker thread ────────────────────────────────────────

    def step_start(self, msg: str) -> None:
        self.call_from_thread(self._set_status, f"⋯ {msg}")

    def step_done(self, msg: str) -> None:
        self.call_from_thread(self._write, f"[green]✓[/] [dim]{msg}[/]")
        self.call_from_thread(self._set_status, "")

    def step_error(self, msg: str) -> None:
        self.call_from_thread(self._write, f"[red]✗[/] [dim]{msg}[/]")
        self.call_from_thread(self._set_status, "")

    def show_conflict(self, diffs: list, left: dict, right: dict, index: int, total: int) -> dict | None:
        return self._show_screen(_ConflictScreen(diffs, left, right, index, total))

    def show_select(self, prompt: str, options: list, fmt=None) -> int:
        result = self._show_screen(_SelectScreen(prompt, options, fmt))
        return result if result is not None else -1

    def _show_screen(self, screen):
        """Push a modal screen from the worker thread and block until dismissed."""
        event = threading.Event()
        result = [None]

        def cb(value) -> None:
            result[0] = value
            event.set()

        self.call_from_thread(self.push_screen, screen, cb)
        event.wait()
        return result[0]

    # ── main-thread UI updates ────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        self.query_one("#status", Label).update(msg)

    def _write(self, markup: str) -> None:
        self.query_one(RichLog).write(markup)
