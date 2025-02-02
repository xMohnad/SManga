import curses
import os
import sys
from pathlib import Path

import typer

from ..core import SpiderDataProcessor
from ..interface import UI

# Constants
current_dir = Path.cwd()

# Typer app configuration
app = typer.Typer(
    help="SManga: A tool to scrape manga chapters from various sites.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


# Helper Functions
def change_dir():
    """Change the working directory to the project root."""
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    os.chdir(project_root)


def type_file(file_path: Path) -> Path:
    """Validate if the given path is a file."""
    if not file_path.exists():
        raise typer.BadParameter(f"Path '{file_path}' does not exist.")
    if not file_path.is_file():
        raise typer.BadParameter(f"'{file_path}' is not a file.")
    return file_path


# Commands
@app.command()
def crawl(
    link: str = typer.Argument(None, help="The link to scrape."),
    file: str = typer.Option(
        None,
        "-f",
        "--file",
        help=(
            "The name of the file to save the scraped data. "
            "If not provided, the manga's name will be used as the file name. "
        ),
    ),
    overwrite: bool = typer.Option(
        False, "-o", "--overwrite", help="Overwrite existing file if it exists."
    ),
    user_agent: str = typer.Option(
        None, "-u", "--User-Agent", help="Custom User-Agent for scraping."
    ),
    recent: bool = typer.Option(
        False, "-r", "--recent", help="Display the most recent chapters saved."
    ),
    spider: str = typer.Option(None, "-s", "--spider", help="Spider name (optional)."),
):
    """Crawl a specific manga site to scrape chapter data."""
    if recent:
        item = curses.wrapper(UI)
        if not item:
            return

        link = item.lastchapter
        file = file or Path(item.json_file).name
    elif link is None:
        raise typer.BadParameter("The Link is required unless using --recent.")

    elif not link.startswith("http"):
        raise typer.BadParameter(f"The Link '{link}' is invalid.")

    change_dir()
    from ..core.scraper import SManga  # Maintain this import here

    smanga = SManga(
        url=link,
        user_agent=user_agent,
        dest_path=current_dir,
        file_name=file,
        overwrite=overwrite,
    )
    smanga.start(spider_name=spider)

    if (
        hasattr(smanga, "final_file_path")
        and smanga.final_file_path.suffix.lower() == ".json"
    ):
        smanga.process_spider_data()


@app.command()
def list():
    """List all available spiders."""
    change_dir()
    from ..core.scraper import SManga  # Maintain this import here

    smanga = SManga()
    smanga.print_spiders()


@app.command()
def add(
    json_file: Path = typer.Argument(
        ..., help="JSON file path containing manga data.", callback=type_file
    ),
    spider_name: str = typer.Argument(..., help="The spider used for crawling data."),
):
    """Add a manga for future crawling to enable the -r option later."""
    processor = SpiderDataProcessor(spider_name)
    json_file = current_dir / json_file
    processor.process_data(json_file)


if __name__ == "__main__":
    app()
