from SManga.core.interface.menu import Menu, MenuUI
from SManga.core.interface.sections import Sections
from SManga.core.interface.menu_item import MenuItem


def UI(stdscr):
    """Main entry point."""
    ui = MenuUI(stdscr)
    return ui.display_menu()
