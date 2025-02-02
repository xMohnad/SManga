from .menu import Menu, MenuUI
from .menu_item import MenuItem
from .sections import Sections


def UI(stdscr):
    """Main entry point."""
    ui = MenuUI(stdscr)
    return ui.display_menu()
