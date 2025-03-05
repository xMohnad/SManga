"""
Manga Browser Application

This module defines a textual-based manga browser application.
It displays a list of manga entries and allows the user to select one.
The selected manga entry is returned upon exiting the application.
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Generator, List, Optional, Text, Union

from rich import print  # Import rich.print for better console output
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.suggester import SuggestFromList
from textual.validation import ValidationResult, Validator
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from SManga.core.models import LastChapter
from SManga.core.processor import LastChapterManager, TrashManager


# -----------------------------------------------------------------------------
# Manga Class Definition
# -----------------------------------------------------------------------------
@dataclass
class Manga(LastChapter):
    """Represents a manga entry with a site, name, and last chapter link."""

    id: str = field(
        default_factory=lambda: str(uuid.uuid4()), metadata={"exclude": True}
    )
    _name_highlight: Optional[Text] = field(default=None, metadata={"exclude": True})

    def __post_init__(self):
        self.name_lower = self.name.lower()

    def __eq__(self, other):
        if isinstance(other, Manga):
            return self.id == other.id
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.id)

    @property
    def name_highlight(self) -> Optional[Text]:
        """Get the highlighted text for the manga name."""
        return self._name_highlight

    @name_highlight.setter
    def name_highlight(self, text_highlight: Text) -> None:
        """Set the highlighted text for the manga name."""
        self._name_highlight = text_highlight

    @classmethod
    def load_items_from_json(cls, manga: List[Dict]) -> List["Manga"]:
        """
        Load manga items from JSON data.
        Args:
            manga: List of dictionaries containing manga data.

        Returns:
            A list of Manga instances.
        """
        return [cls(**item) for item in manga] if manga else []

    def formatted_text(self) -> str:
        """Return formatted text for display."""
        return f"[{self.site}] {self.name}"

    def formatted_highlight(self) -> Text:
        """Return formatted text with highlighting."""
        if self._name_highlight:
            site_text = Text(f"[{self.site}] ")
            site_text.append(self._name_highlight)
            return site_text
        return Text(self.formatted_text())

    def list_item(self, highlight_name: bool = False) -> ListItem:
        """
        Create a ListItem widget representation of the manga.

        Args:
            highlight_name (bool): If True, the manga name will be displayed with highlighting.
                                  If False, the name will be displayed without highlighting.
                                  Defaults to False.

        Returns:
            ListItem: A ListItem widget containing the formatted manga information.
        """
        text = self.formatted_highlight() if highlight_name else self.formatted_text()
        return ListItem(Label(text))


def create_manga_list_items(
    mangas: List[Manga], highlight_name: bool = False
) -> Generator[ListItem, None, None]:
    """
    Convert a list of manga objects into a tuple of ListItem widgets.

    Args:
        mangas List[Manga]: A list of manga objects.
        highlight_name (bool): If True, highlight the manga name.

    Returns:
        tuple[ListItem, ...]: A tuple containing ListItem widgets for each manga.
    """
    return (manga.list_item(highlight_name) for manga in mangas)


# -----------------------------------------------------------------------------
#  Search Input
# -----------------------------------------------------------------------------
class SearchInput(Input):
    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    search_term = reactive("")
    prev_search_term = reactive("")

    @work(exclusive=True, name="Filter Manga")
    async def filter(self, style: str = "underline bold") -> None:
        """Filter and highlight manga items based on the query."""
        manga_list = self.app.query_one("#manga-list", MangaList)
        query = self.search_term
        target_list = (
            self.app.query_one("#trash-list", TrashList)
            if manga_list.has_class("hidden")
            else manga_list
        )

        # If the query is empty, reset filtered list and return early
        if not query:
            target_list.filtered_manga = target_list.manga.copy()
            target_list.update_message(f"{len(target_list.filtered_manga)} Manga")
            await target_list.update_manga_list()
            return

        # Determine whether to search in the full list or the filtered list
        search_in = (
            target_list.filtered_manga
            if query > self.prev_search_term
            else target_list.manga
        )
        self.prev_search_term = query  # Update the previous search term

        # Filter and highlight items
        target_list.filtered_manga = [
            item
            for item in search_in
            if await self._highlight_and_match(item, query, style)
        ]
        await target_list.update_manga_list(use_highlight=True)

        len_filtered = len(target_list.filtered_manga)
        target_list.update_message(
            f"{len_filtered} Manga • {len(target_list.manga) - len_filtered} filtered"
            if target_list.filtered_manga
            else f"Nothing matched • {len(target_list.manga) - len_filtered} filtered"
        )

    async def _highlight_and_match(self, item, query, style):
        """Helper function to check if the item matches the query and highlight it."""
        highlighted_text = Text(item.name)
        prev_index = -1

        # Try to match the query in the item name
        for char in query:
            if not char.isspace():
                index = item.name_lower.find(char, prev_index + 1)
                if index == -1:
                    return False  # No match

                # Stylize the character at the matched position
                highlighted_text.stylize(style, index, index + 1)
                prev_index = index

        item.name_highlight = highlighted_text  # Store the highlighted name
        return True

    def action_back(self):
        self.add_class("hidden")

    @on(Input.Submitted, "#search-input")
    def on_submitted(self):
        self.action_back()

    @on(Input.Changed, "#search-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes with debounce."""
        # Convert query to lowercase once
        self.search_term = event.value.lower()
        self.filter()


# -----------------------------------------------------------------------------
# Manga Form Edit
# -----------------------------------------------------------------------------
class EditMangaForm(Screen):
    AUTO_FOCUS = "#name"

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def __init__(
        self,
        manga: Manga,
        manager: Union[LastChapterManager, TrashManager],
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.manga = manga
        self.manager = manager

        self.fields = {
            "#name": "name",
            "#site": "site",
            "#last_chapter": "last_chapter",
            "#file_name": "file_name",
        }

    def compose(self) -> ComposeResult:
        """Compose the layout of the screen."""
        yield Header()
        with Vertical():
            yield Label("Name")
            yield Input(
                placeholder="Manga Name",
                value=self.manga.name,
                id="name",
                validators=[self.RequiredValidator("Name is required!")],
                suggester=SuggestFromList([self.manga.name], case_sensitive=False),
            )
            yield Label("Site")
            yield Input(
                placeholder="Site",
                value=self.manga.site,
                id="site",
                validators=[self.RequiredValidator("Source is required!")],
                suggester=SuggestFromList([self.manga.site], case_sensitive=False),
            )
            yield Label("Last Chapter URL")
            yield Input(
                placeholder="Last Chapter URL",
                value=self.manga.last_chapter,
                id="last_chapter",
                validators=[
                    self.RequiredValidator("Last chapter URL is required!"),
                    self.URLValidator("Please enter a valid URL."),
                ],
                suggester=SuggestFromList(
                    ["https://", "http://", self.manga.last_chapter],
                    case_sensitive=False,
                ),
            )
            yield Label("File Name")
            yield Input(
                placeholder="File Name",
                value=self.manga.file_name,
                id="file_name",
                validators=[
                    self.RequiredValidator("File name is required!"),
                    self.JsonFileValidator("File name must end with .json!"),
                ],
                suggester=SuggestFromList(self.generate_filename_variations()),
            )
            with Horizontal():
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", id="cancel-button")
        yield Footer()

    def _update_manga_from_inputs(self) -> Manga:
        """Update the manga object with the values from the input fields."""
        manga = Manga("", "", "", "")
        for field_id, attribute in self.fields.items():
            input_value = self.query_one(field_id, Input).value
            setattr(manga, attribute, input_value)
        return manga

    @on(Button.Pressed, "#save-button")
    def on_save(self) -> None:
        """Handle save button press."""
        # Validate all inputs before saving
        if self._validate_inputs():
            updated_manga = self._update_manga_from_inputs()
            self.manager.update_entry(self.manga, updated_manga)
            self.notify("Manga updated successfully!")
            self.dismiss(updated_manga)

    @on(Button.Pressed, "#cancel-button")
    def on_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(False)

    @on(Input.Submitted, "#name, #site, #last_chapter, #file_name")
    def on_input_submitted(self) -> None:
        """Handle input submission (e.g., pressing Enter)."""
        self.focus_next()

    def action_back(self) -> None:
        self.dismiss(False)

    def _validate_inputs(self) -> bool:
        """Validate all input fields."""
        is_valid = True
        for field_id in self.fields:
            input_field: Input = self.query_one(field_id, Input)
            validation_result: Optional[ValidationResult] = input_field.validate(
                input_field.value
            )

            if validation_result and not validation_result.is_valid:
                is_valid = False
                self.notify(validation_result.failure_descriptions[0], severity="error")
        return is_valid

    class RequiredValidator(Validator):
        """Validator to check if a field is not empty."""

        def __init__(self, error_message: str) -> None:
            self.error_message = error_message
            super().__init__()

        def validate(self, value: str) -> ValidationResult:
            if not value.strip():
                return self.failure(self.error_message)
            return self.success()

    class JsonFileValidator(Validator):
        """Validator to check if the file name ends with .json."""

        def __init__(self, error_message: str) -> None:
            self.error_message = error_message
            super().__init__()

        def validate(self, value: str) -> ValidationResult:
            if not value.lower().endswith(".json"):
                return self.failure(self.error_message)
            return self.success()

    class URLValidator(Validator):
        """Validator to check if the URL is valid"""

        def __init__(self, error_message: str) -> None:
            self.error_message = error_message
            super().__init__()

        def validate(self, value: str) -> ValidationResult:
            regex = re.compile(
                r"^(https?://)?"  # Optional http:// or https://
                r"("
                r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"  # Domain name
                r"|"  # OR
                r"(\d{1,3}\.){3}\d{1,3}"  # IPv4 address
                r")"
                r"(:\d+)?"  # Optional port number
                r"(/[^\s?#]*)?"  # Optional path
                r"(\?[^\s#]*)?"  # Optional query string
                r"(#[^\s]*)?$"  # Optional fragment
            )

            if not regex.match(value):
                return self.failure(self.error_message)
            return self.success()  # Return success if valid

    def generate_filename_variations(self) -> List[str]:
        if not self.manga.name:
            return []

        sanitized = re.sub(r'[<>:"/\\|?*]', "_", self.manga.name.strip())
        sanitized = re.sub(r"\s+", " ", sanitized)
        variations = [
            re.sub(r"\s+", "_", sanitized).lower(),
            re.sub(r"\s+", "-", sanitized).lower(),
            "".join(word.capitalize() for word in sanitized.split()).replace(" ", ""),
            re.sub(r"\s+", "-", sanitized).upper(),
            re.sub(r"\s+", "-", sanitized)[:30].rstrip("-"),
            re.sub(
                r"-+",
                "-",
                re.sub(r"[^a-z0-9-]", "", re.sub(r"\s+", "-", sanitized).lower()),
            ),
            sanitized,
        ]

        return variations


# -----------------------------------------------------------------------------
# Base ListView for Customizable Lists
# -----------------------------------------------------------------------------
class BaseList(ListView):
    """Base ListView with common functionality."""

    BINDINGS = [
        Binding("/", "toggle_search", "Search"),
        Binding("s", "toggle_sort", "Sort"),
        Binding("e", "edit", "Edit"),
        Binding("o", "open_manga", "Open"),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("home, K", "cursor_home", "Cursor First", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("end, J", "cursor_end", "Cursor Last", show=False),
        Binding("g", "scroll_home", "Page Up", show=False),
        Binding("G", "scroll_end", "Page Down", show=False),
    ]

    sort_by_site: reactive[bool] = reactive(False)

    def __init__(
        self,
        initial_index: Optional[int] = 0,
        *children: ListItem,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
        disabled: bool = False,
    ) -> None:
        self.manager = self.get_manager()
        self.data = self.manager.get_all_entries()
        self.manga = Manga.load_items_from_json(self.data)
        self.filtered_manga = self.manga.copy()

        super().__init__(
            *children or create_manga_list_items(self.manga),
            initial_index=initial_index,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def get_manager(self):
        """Override this method to provide the appropriate data manager."""
        raise NotImplementedError

    def _handle_empty_list(self, action: str) -> bool:
        """Handle empty list scenario."""
        if not self.filtered_manga:
            self.notify(f"No manga to {action}!", severity="warning")
            return True
        return False

    def _handle_no_selection(self) -> bool:
        """Handle no selection scenario."""
        if self.index is None:
            self.notify(
                "No manga selected. Please select a manga first.", severity="error"
            )
            return True
        return False

    @work(exclusive=True, name="Sort Manga")
    async def action_toggle_sort(self) -> None:
        """Toggle sorting between manga name and site."""
        if self._handle_empty_list("sort"):
            return

        self.sort_by_site = not self.sort_by_site
        self.filtered_manga.sort(
            key=lambda item: item.site if self.sort_by_site else item.name
        )
        await self.update_manga_list()

        self.notify(f"Sorted by {'site' if self.sort_by_site else 'name'}", timeout=2)

    async def update_manga_list(
        self, use_highlight: bool = False, mangas: Optional[List[Manga]] = None
    ) -> None:
        """Update the manga list widget with the sorted items."""
        mangas = mangas or self.filtered_manga
        selected_index = self.index if self.index is not None else 0

        async with self.batch():
            await self.clear()
            await self.extend(create_manga_list_items(mangas, use_highlight))
            self.index = selected_index

    def action_open_manga(self):
        """Open Manga chapter URL in browser"""
        if self._handle_empty_list("open") or self._handle_no_selection():
            return

        manga = self.filtered_manga[self.index]
        self.app.open_url(manga.last_chapter)
        self.notify(f"The URL for '{manga.name}' has been opened in your browser.")

    def action_toggle_search(self) -> None:
        """Toggle the visibility of the search input."""
        if self._handle_empty_list("search"):
            return

        search_input = self.app.query_one("#search-input", SearchInput)
        search_input.toggle_class("hidden")
        search_input.value = search_input.search_term
        (self if search_input.has_class("hidden") else search_input).focus()

    def update_message(self, message: str):
        """Update the message displayed in the UI."""
        self.app.query_one(".list-message", Static).update(message)

    @work(exclusive=True, name="Move Item Between Lists")
    async def _move_item_between_lists(
        self,
        action: str,
        target_list: Optional["BaseList"],
        manager_action: Callable,
        success_message: str,
        target_list_update_message: str,
    ) -> None:
        """
        Helper function to move an item between lists (e.g., delete, restore, purge).

        :param action: The action being performed (e.g., "delete", "restore", "purge").
        :param target_list: The target list to move the item to.
        :param manager_action: The manager method to call (e.g., delete_entry, restore_entry).
        :param success_message: The notification message to show on success.
        :param target_list_update_message: The message to update in the target list.
        """
        if self._handle_empty_list(action) or self._handle_no_selection():
            return

        manga = self.filtered_manga[self.index]
        manager_action(
            manga
        )  # Call the manager method (e.g., delete_entry, restore_entry)

        async with self.batch():
            self.manga.pop(self.manga.index(manga))
            self.filtered_manga.pop(self.index)
            await self.pop(self.index)
            self.update_message(
                f"{len(self.filtered_manga)} Manga"
                if self.filtered_manga
                else f"No {target_list_update_message}"
            )
            self.notify(f"'{manga.name}' {success_message}", timeout=2)

        if target_list is not None:
            target_list.append(manga.list_item())
            target_list.manga.append(manga)
            target_list.filtered_manga.append(manga)

    @work(exclusive=True, name="Open Edit Screen")
    async def action_edit(self):
        if self._handle_empty_list("edit") or self._handle_no_selection():
            return

        index = self.index
        manga = self.filtered_manga[index]
        updated_manga = await self.app.push_screen(
            EditMangaForm(manga, self.manager), wait_for_dismiss=True
        )
        if updated_manga:
            self.manga[self.manga.index(manga)] = updated_manga
            self.filtered_manga[index] = updated_manga
            try:
                async with self.batch():
                    self.pop(index)
                    await self.insert(index, [updated_manga.list_item(True)])
                    self.index = index
            except ValueError:
                self.notify(
                    "The manga could not be found in the list.", severity="error"
                )

    def action_cursor_home(self) -> None:
        """Move cursor to the first item."""
        self.index = 0

    def action_cursor_end(self) -> None:
        """Move cursor to the last item."""
        self.index = len(self) - 1


# -----------------------------------------------------------------------------
# Manga ListView
# -----------------------------------------------------------------------------
class MangaList(BaseList):
    """Enhanced ListView for Manga with Vim-style navigation and selection controls."""

    BINDINGS = [
        Binding("d", "delete", "Delete"),
        Binding("t", "open_trash", "Trash"),
    ]

    def get_manager(self):
        return LastChapterManager()

    def action_open_trash(self) -> None:
        """Open trash list."""
        trash_list = self.app.query_one("#trash-list", TrashList)
        if trash_list.has_class("hidden"):
            self.add_class("hidden")
            trash_list.remove_class("hidden")
            self.update_message(
                f"{len(trash_list.filtered_manga)} Manga"
                if trash_list.filtered_manga
                else "No Manga in Trash"
            )

    def action_delete(self) -> None:
        """Delete the selected entry."""
        self._move_item_between_lists(
            action="delete",
            target_list=self.app.query_one("#trash-list", TrashList),
            manager_action=self.manager.delete_entry,
            success_message="has been deleted",
            target_list_update_message="Manga available",
        )


# -----------------------------------------------------------------------------
# Trash ListView
# -----------------------------------------------------------------------------
class TrashList(BaseList):
    """Enhanced ListView for Trash with Vim-style navigation and selection controls."""

    BINDINGS = [
        Binding("r", "restore_entry", "Restore"),
        Binding("p", "purge", "Purge"),
        Binding("escape", "back", "Back"),
    ]

    def get_manager(self):
        return TrashManager()

    def action_back(self):
        manga_list = self.app.query_one("#manga-list", MangaList)
        if manga_list.has_class("hidden"):
            manga_list.remove_class("hidden")
            self.add_class("hidden")
            self.update_message(
                f"{len(manga_list.filtered_manga)} Manga"
                if manga_list.filtered_manga
                else "No Manga available."
            )

    def action_restore_entry(self) -> None:
        """Restore the selected entry from the trash."""
        self._move_item_between_lists(
            action="restore",
            target_list=self.app.query_one("#manga-list", MangaList),
            manager_action=self.manager.restore_entry,
            success_message="has been restored",
            target_list_update_message="Manga in Trash",
        )

    def action_purge(self) -> None:
        """Purge the selected entry from the trash."""
        self._move_item_between_lists(
            action="Purge",
            target_list=None,  # No target list for purging
            manager_action=self.manager.delete_permanently,
            success_message="has been Purged",
            target_list_update_message="Manga in Trash",
        )


# -----------------------------------------------------------------------------
# Manga Browser Application
# -----------------------------------------------------------------------------
class MangaBrowser(App):
    """Textual application for browsing fetched manga entry."""

    CSS_PATH = "style.tcss"
    AUTO_FOCUS = "#manga-list"

    def compose(self) -> ComposeResult:
        yield Header(True)
        yield Static(classes="list-message")
        yield SearchInput(placeholder="Search...", id="search-input", classes="hidden")
        yield MangaList(id="manga-list")
        yield TrashList(id="trash-list", classes="hidden")
        yield Footer()

    def on_mount(self) -> None:
        manga_list = self.query_one("#manga-list", MangaList)
        trash_list = self.query_one("#trash-list", TrashList)
        message = self.query_one(".list-message", Static)

        if not manga_list.manga:
            manga_list.add_class("hidden")
            message.add_class("no-manga")
            message.update("No Manga available yet.")
            if not trash_list.manga:
                message.update("No Manga and Trash available yet.")
                trash_list.remove()
                manga_list.remove()
        else:
            message.update(f"{len(manga_list.filtered_manga)} Manga")

    @on(MangaList.Selected, "#manga-list")
    def select_manga(self) -> None:
        """Handle manga selection from the list."""
        manga_list = self.query_one(MangaList)
        selected_index = manga_list.index or 0
        if 0 <= selected_index < len(manga_list.filtered_manga):
            self.exit(manga_list.filtered_manga[selected_index])
        else:
            self.notify("Invalid selection", severity="error")


# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Create an instance of MangaBrowser and run the application
    app = MangaBrowser()
    result = app.run()

    # After exiting the application, display the selected manga entry
    if result:
        print("\nSelected item:", result.asdict)
