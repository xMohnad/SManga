import curses


# curses.start_color()
# curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
# curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
# curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE) # select item

# curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
# curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
# curses.init_pair(7, curses.COLOR_CYAN, curses.COLOR_BLACK)
# curses.init_pair(8, curses.COLOR_YELLOW, curses.COLOR_BLACK) # 
 
class Sections:
    def __init__(self, stdscr, color_scheme):
        self.stdscr = stdscr
        self.color_scheme = color_scheme

    def display_centered_text_in_box(self, content):
        """Display text centered within a box on the screen."""
        stdscr = self.stdscr
        height, width = stdscr.getmaxyx()
        stdscr.clear()

        # Define the size of the box
        box_width = width - 4
        box_height = len(content) + 5

        box_x = (width - box_width) // 2
        box_y = (height - box_height) // 2

        # Draw the border for the help box
        self._draw_box(stdscr, box_y, box_x, box_height, box_width)

        # Display the help content centered within the box
        self._display_centered_text_in_box(
            stdscr, content, box_y + 2, box_x + 2, box_width
        )
        stdscr.refresh()

    def _display_centered_text_in_box(self, stdscr, content, start_y, start_x, box_width):
        for i, (message, color_pair) in enumerate(content):
            # Calculate position to center the text inside the box
            x_position = start_x + (box_width - 4 - len(message)) // 2
            y_position = start_y + i

            # Display the text with the defined color pair
            stdscr.attron(self.color_scheme.get_color(color_pair))
            stdscr.addstr(y_position, x_position, message)
            stdscr.attroff(self.color_scheme.get_color(color_pair))

    def _draw_box(self, stdscr, start_y, start_x, height, width):
        """Draw a box with borders on the screen."""
        stdscr.addch(start_y, start_x, curses.ACS_ULCORNER)
        stdscr.addch(start_y, start_x + width - 1, curses.ACS_URCORNER)
        stdscr.addch(start_y + height - 1, start_x, curses.ACS_LLCORNER)
        stdscr.addch(start_y + height - 1, start_x + width - 1, curses.ACS_LRCORNER)

        for x in range(start_x + 1, start_x + width - 1):
            stdscr.addch(start_y, x, curses.ACS_HLINE)
            stdscr.addch(start_y + height - 1, x, curses.ACS_HLINE)

        for y in range(start_y + 1, start_y + height - 1):
            stdscr.addch(y, start_x, curses.ACS_VLINE)
            stdscr.addch(y, start_x + width - 1, curses.ACS_VLINE)

    def display_confirmation(self, selected_item):
        _, width = self.stdscr.getmaxyx()

        messages = [
            ("Are you sure you want to delete the following item?", 4), 
            ("", 0),
            (f"'{selected_item.display(width - 9)}'", 1), 
            ("", 0),
            ("(y)es / (n)o [default: n]", 7),  
        ]

        self.display_centered_text_in_box(messages)
        while True:
            key = self.stdscr.getch()
            if key == -1:
                pass
            elif key == ord("y"):
                return True
            else:
                break
        return False

    def show_help(self):
        """Show help section with colors and proper alignment."""
        help_content = [
            ("Help", 1), 
            ("-------------", 2),  
            ("Use ↑ UP and ↓ DOWN arrows to navigate the menu.", 3),
            ("", 0),
            ("Press ENTER to select an item.", 3),
            ("", 0),
            ("/ filter: Filter items", 3), 
            ("", 0),
            ("Ctrl + D: Delete item", 3),
            ("", 0),
            ("Ctrl + S: Sort items", 3), 
            ("", 0),
            ("Home: Go to the first item.", 3),
            ("", 0),
            ("End: Go to the last item.", 3),
            ("", 0),
            ("Ctrl + H: Show this help screen.", 3),
            ("", 0),
            ("Ctrl + Q: Quit.", 3),  
            ("", 0),
            ("", 0),
            ("Press any key to go back to the menu...", 7), 
        ]

        self.display_centered_text_in_box(help_content)
        while True:
            key = self.stdscr.getch()
            if key == -1:
                pass
            else:
                break
