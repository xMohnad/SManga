import curses

from SManga.core import SpiderDataProcessor

from .menu_item import MenuItem
from .sections import Sections


class ColorScheme:
    """Class to define and manage color schemes."""

    def __init__(self):
        self.colors = {}

    def setup_colors(self):
        """Initialize and define color pairs for curses."""
        curses.start_color()
        # Define some color pairs (you can customize these)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)  # Title
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default text
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Selected item
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Highlighted
        curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Warnings
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Search
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Sorting
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Footer
        curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLUE)  #

    def get_color(self, color_id):
        """Get the color pair by ID."""
        return curses.color_pair(color_id)


class Menu:
    """Handles menu display and interactions."""

    def __init__(self, color_scheme):
        self.color_scheme = color_scheme
        self.items = MenuItem.load_menu_items_from_json()
        self.filtered_items = sorted(self.items, key=lambda item: item.manganame)
        self.search_mode = False
        self.search_query = ""
        self.current_row = 0
        self.offset = 0
        self.sort_by_site = False
        self.last_height, self.last_width = 0, 0

    def render(self, stdscr):
        """Renders the menu with items, search bar, and footer."""
        height, width = stdscr.getmaxyx()
        if self.last_height != height or self.last_width != width:
            stdscr.clear()
            self.last_height, self.last_width = height, width
            self._render_footer(stdscr, height, width)

        self._render_items(stdscr, height, width)
        self._render_search_bar(stdscr, width)
        stdscr.refresh()

    #
    def handle_navigation(self, key, stdscr):
        """Handle navigation keys."""
        height, width = stdscr.getmaxyx()
        if key == curses.KEY_DOWN:
            self._move_down(stdscr, height, width)
        elif key == curses.KEY_UP:
            self._move_up(stdscr, height, width)

        elif key == curses.KEY_HOME:  # Home
            self._wrap_top()
        elif key == curses.KEY_END:  # End
            self._wrap_bottom(height)

        elif key == ord("/") and not self.search_mode:
            self.search_mode = True
            self.search_query = ""

        elif key == 4:  # Ctrl + D
            return True  # Indicates delete selected

    def handle_search_mode(self, key, stdscr):
        """Handle search mode input."""
        if key == 27:  # Escape and ALT
            next_key = stdscr.getch()
            if next_key == ord("q"):
                self._cancel_search_mode()
                stdscr.clear()
        elif key in [127, curses.KEY_BACKSPACE]:
            self._delete_search_char()
            stdscr.clear()
        elif 32 <= key < 256:
            stdscr.clear()
            self._append_search_char(chr(key))

    def select_item(self):
        """Select the currently highlighted item."""
        if 0 <= self.current_row < len(self.filtered_items):
            selected_item = self.filtered_items[self.current_row]
            return selected_item
        else:
            return None

    def delete_item(self, item):
        """Delete the selected item."""
        self.items.remove(item)
        self.filtered_items.remove(item)
        self._save_data()

    def toggle_sort(self):
        """Toggle sorting between manga name and site."""
        self.sort_by_site = not self.sort_by_site
        key = (
            (lambda item: item.site)
            if self.sort_by_site
            else (lambda item: item.manganame)
        )
        self.filtered_items = sorted(self.items, key=key)
        self.current_row = 0
        self.offset = 0

    # Private methods for rendering
    def _render_footer(self, stdscr, height, width):
        """Render the footer with instructions."""
        help_text = " • More guidance? Ctrl + H."
        available_width = width - 1

        if self.search_mode:
            footer_text = "[ALT + Q & Esc & Q: Exit]"
        else:
            footer_text = (
                "↑ up • ↓ down • / filter • Enter Select "
                "• Ctrl + S sort • Ctrl + D Delete • Ctrl + Q Quit "
                "• Home: Top. • End: Bottom."
            )

        if len(footer_text) > available_width:
            footer_text = footer_text[: available_width - len(help_text) - 3] + "..."
            final_footer_text = footer_text + help_text
        else:
            final_footer_text = footer_text  # Only show footer_text if it fits

        try:
            stdscr.attron(self.color_scheme.get_color(3))
            stdscr.addstr(
                height - 1,
                0,
                final_footer_text.ljust(available_width),
                self.color_scheme.get_color(3),
            )
            stdscr.attroff(self.color_scheme.get_color(3))
        except curses.error:
            pass

    def _render_items(self, stdscr, height, width):
        """Render the menu items with navigation and ensure visibility of the current row."""
        max_items = self._max_visible_items(height)
        if not self.filtered_items:
            stdscr.addstr(
                height // 2,
                (width - len("No items found.")) // 2,
                "No items found.",
                self.color_scheme.get_color(3),
            )
            return

        # Ensure current row stays within bounds of the filtered list
        self.current_row = min(self.current_row, len(self.filtered_items) - 1)

        # Adjust the offset to ensure the current row is visible
        if self.current_row < self.offset:
            self.offset = self.current_row
        elif self.current_row >= self.offset + max_items:
            self.offset = self.current_row - max_items + 1

        # Calculate the visible range of items to be displayed on screen
        visible_range = range(
            self.offset, min(self.offset + max_items, len(self.filtered_items))
        )

        # Render each visible item box in the computed range
        for idx in visible_range:
            self._render_item_box(stdscr, idx, height, width)

        stdscr.refresh()

    def _render_item_box(self, stdscr, idx, height, width):
        """Render a single item box with proper alignment for borders."""
        item = self.filtered_items[idx]
        y_pos = 3 + (idx - self.offset) * 3
        box_width = width - 4
        color_pair = 3 if idx == self.current_row else 6  # Highlight current item

        if y_pos + 2 >= height:
            return

        try:
            # Clear the full line to avoid leftover characters
            stdscr.addstr(y_pos + 1, 2, " " * box_width)

            stdscr.attron(self.color_scheme.get_color(color_pair))
            truncated_item = self._get_truncated_item(idx, item, box_width)

            if self.search_mode and self.search_query:
                self._render_search_highlight(
                    stdscr, truncated_item, y_pos, box_width, color_pair
                )
            else:
                stdscr.addstr(
                    y_pos + 1, 4, truncated_item
                )  # Not in search mode, render normally

            self._render_box(stdscr, y_pos, box_width)
            stdscr.attroff(self.color_scheme.get_color(color_pair))

        except (curses.error, ValueError):
            pass

    def _render_search_highlight(
        self, stdscr, truncated_item, y_pos, box_width, color_pair
    ):
        """Highlight the matching part of the item in search mode with underline."""
        # Get the query in lowercase for case-insensitive matching
        query = self.search_query.lower()
        item_lower = truncated_item.lower()
        start_idx = item_lower.find(query)

        if start_idx == -1:
            return stdscr.addstr(
                y_pos + 1, 4, truncated_item
            )  # No match, render normally

        # Before match
        stdscr.addstr(y_pos + 1, 4, truncated_item[:start_idx])

        # Match highlight with underline and bold
        stdscr.attron(curses.A_UNDERLINE)  # Enable underline attribute
        stdscr.attron(curses.A_BOLD)  # Enable bold attribute
        stdscr.addstr(
            y_pos + 1, 4 + start_idx, truncated_item[start_idx : start_idx + len(query)]
        )
        stdscr.attroff(curses.A_BOLD)  # Disable bold attribute
        stdscr.attroff(curses.A_UNDERLINE)  # Disable underline attribute

        # Restore the original color for the text after the match
        stdscr.attron(self.color_scheme.get_color(color_pair))
        stdscr.addstr(
            y_pos + 1,
            4 + start_idx + len(query),
            truncated_item[start_idx + len(query) :],
        )

    def _render_box(self, stdscr, y_pos, box_width):
        """Render the border of the item box."""
        stdscr.addstr(y_pos, 2, f"╭{'─' * (box_width - 2)}╮")
        stdscr.addstr(y_pos + 1, box_width + 1, "│")
        stdscr.addstr(y_pos + 1, 2, "│")
        stdscr.addstr(y_pos + 2, 2, f"╰{'─' * (box_width - 2)}╯")

    def _get_truncated_item(self, idx, item, box_width):
        """Get the truncated item display string."""
        item_display = item.display(box_width - 5)
        item_name = (
            f"#{idx + 1} {item_display}" if idx == self.current_row else item_display
        )
        return item_name[: box_width - 5]

    def _render_search_bar(self, stdscr, width):
        """Render the search bar if in search mode."""
        if self.search_mode:
            title = "Filter: "
            query = self.search_query

            max_query_length = width - len(title) - 6
            if len(query) > max_query_length:
                query = query[: max_query_length - 3] + "..."

            # Render the title of the search bar
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(1, 3, title, self.color_scheme.get_color(6))
            stdscr.addstr(1, len(title) + 3, query, self.color_scheme.get_color(6))

            # Clear the remaining space in the search bar
            remaining_space = width - len(title) - len(query) - 4
            if remaining_space > 0:
                stdscr.addstr(
                    1,
                    len(title) + len(query) + 3,
                    " " * remaining_space,
                    self.color_scheme.get_color(4),
                )

            # Display a blinking cursor (indicator)
            cursor_position = len(title) + len(query) + 3
            stdscr.addstr(
                1, cursor_position, " ", self.color_scheme.get_color(9) | curses.A_BOLD
            )
            stdscr.attroff(curses.A_BOLD)

    # Private methods for handling search
    def _delete_search_char(self):
        if self.search_query:
            self.search_query = self.search_query[:-1]
            self.filtered_items = self._filter_items()

    def _append_search_char(self, char):
        if char:
            self.search_query += char
            self.filtered_items = self._filter_items()

    def _cancel_search_mode(self):
        """Cancel search mode and preserve the current selection."""
        if self.filtered_items:
            current_item = self.filtered_items[self.current_row]

            # Find the index of the current item in the original list
            if current_item in self.items:
                self.current_row = self.items.index(current_item)

        # Reset search mode and query
        self.search_mode = False
        self.search_query = ""
        self.filtered_items = self._filter_items()

    # Additional helper methods
    def _max_visible_items(self, height):
        """Calculate maximum visible items based on screen height."""
        return (height - 6) // 3

    def _filter_items(self):
        """Filter items based on the search query."""
        query_lower = self.search_query.lower()
        if not query_lower:
            return self.items
        return [item for item in self.items if query_lower in item.manganame.lower()]

    def _move_down(self, stdscr, height, width):
        """Move down in the menu with wrap-around."""
        if self.current_row < len(self.filtered_items) - 1:
            # Only update the current and previous row when moving down
            previous_row = self.current_row
            self.current_row += 1

            # If we scroll past the visible area, adjust the offset
            if self.current_row - self.offset >= self._max_visible_items(height):
                self.offset += 1

            # Update the rendering only for the changed rows
            self._render_item_box(stdscr, previous_row, height, width)
            self._render_item_box(stdscr, self.current_row, height, width)
            stdscr.refresh()

    def _move_up(self, stdscr, height, width):
        """Move up in the menu with wrap-around."""
        if self.current_row > 0:
            # Only update the current and previous row when moving up
            previous_row = self.current_row
            self.current_row -= 1

            # If we scroll above the visible area, adjust the offset
            if self.current_row < self.offset:
                self.offset -= 1

            # Update the rendering only for the changed rows
            self._render_item_box(stdscr, previous_row, height, width)
            self._render_item_box(stdscr, self.current_row, height, width)
            stdscr.refresh()

    def _wrap_top(self):
        # Wrap around to the top
        self.current_row = 0
        self.offset = 0

    def _wrap_bottom(self, height):
        # Wrap around to the bottom
        self.current_row = len(self.filtered_items) - 1
        self.offset = max(0, self.current_row - self._max_visible_items(height) + 1)

    def _save_data(self):
        """Save the current items to JSON."""
        processor = SpiderDataProcessor()
        processor._save_data(
            processor.processed_data_path, [item.__dict__ for item in self.items]
        )


class MenuUI:
    """Main UI handler for displaying the menu."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self._init_curses()
        self.color_scheme = ColorScheme()
        self.color_scheme.setup_colors()
        self.sections = Sections(stdscr, self.color_scheme)
        self.menu = Menu(self.color_scheme)

    def display_menu(self):
        """Main loop to display the menu and handle user interactions."""
        while True:
            self.menu.render(self.stdscr)

            key = self.stdscr.getch()
            if self.menu.search_mode:
                self.menu.handle_search_mode(key, self.stdscr)

            if self.menu.handle_navigation(key, self.stdscr):
                self._confirm_deletion()
                self.stdscr.clear()
            elif key == ord("\n"):
                selected = self.menu.select_item()
                if selected:
                    return selected
            elif key == 263:  # Ctrl + H
                self.sections.show_help()
                self.stdscr.clear()
            elif key == 19:  # Ctrl + S
                self.menu.toggle_sort()
                self.stdscr.clear()
            elif key == 17:  # Ctrl + Q
                break

    def _confirm_deletion(self):
        """Ask the user to confirm the deletion of the selected item."""
        selected_item = self.menu.filtered_items[self.menu.current_row]
        if self.sections.display_confirmation(selected_item):
            self.menu.delete_item(selected_item)

    def _init_curses(self):
        """Initialize curses settings."""
        curses.curs_set(0)
        self.stdscr.timeout(100)


if __name__ == "__main__":

    def UI(stdscr):
        """Main entry point."""
        ui = MenuUI(stdscr)
        return ui.display_menu()

    try:
        item = curses.wrapper(UI)
        if item:
            import json

            print(json.dumps(item.__dict__, indent=4, ensure_ascii=False))
    except Exception as e:
        print(e)
