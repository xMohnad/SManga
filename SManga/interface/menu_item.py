from SManga.core import SpiderDataProcessor


class MenuItem:
    """Represents a menu item for a manga."""

    def __init__(self, manganame="", site="", lastchapter="", json_file=""):
        self.manganame = manganame
        self.site = site
        self.lastchapter = lastchapter
        self.json_file = json_file

    @classmethod
    def load_menu_items_from_json(cls):
        """Load menu items from processed JSON data."""
        processor = SpiderDataProcessor()
        processed_data = processor.load_processed_data()

        if not processed_data:
            return []

        return [cls(**item) for item in processed_data]

    def display(self, max_width):
        """Format the display text for a menu item, truncating if necessary."""
        text = self.manganame.replace(f"({self.site})", "").strip()
        available_width = max_width - len(f" - {self.site}")

        # Truncate the text if it exceeds the available width, and append '...' if truncated
        if len(text) > available_width:
            text = text[: available_width - 3] + "..."

        return f"{text} - {self.site}"

    def _clean_text(self, text):
        """Remove any text within parentheses to clean up the display text."""
        if "(" in text and ")" in text:
            return text[: text.rfind("(")].strip() + text[text.rfind(")") + 1 :].strip()
        return text
