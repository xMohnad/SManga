import sys, os
import curses
import typer
from pathlib import Path

from .components import SpiderDataProcessor
from .interface import UI

current_dir = Path.cwd()

app = typer.Typer(
    help="SManga: A tool to scrape manga chapters from various sites.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def change_dir():
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    os.chdir(project_root)


def type_file(file_path: Path) -> Path:
    """Validate if the path is a file."""
    if not file_path.exists():
        raise typer.BadParameter(f"Path '{file_path}' does not exist.")
    if not file_path.is_file():
        raise typer.BadParameter(f"'{file_path}' is not a file.")
    return file_path


@app.command()
def crawl(
    link: str = typer.Argument(None, help="The link to scrape."),
    file: str = typer.Option(
        "chapters.json", "-f", "--file", help="File to save scraped data."
    ),
    user_agent: str = typer.Option(
        None, "-u", "--User-Agent", help="Custom User-Agent for scraping."
    ),
    overwrite: bool = typer.Option(
        False, "-o", "--overwrite", help="Overwrite existing file if it exists."
    ),
    recent: bool = typer.Option(
        False, "-r", "--recent", help="Display the most recent chapters saved."
    ),
    spider: str = typer.Option(
        None, "-s", "--spider", help="The name of the spider to use (optional)."
    ),
):
    """Crawl a specific manga site to scrape chapter data."""

    if recent:
        item = curses.wrapper(UI)
        if not item:
            return

        link = item.lastchapter
        file = file if file == "chapters.json" else Path(item.json_file).name
    elif link is None: 
        raise typer.BadParameter("The Link is required unless using --recent.", param=link)

    elif not link.startswith("http"):
        raise typer.BadParameter(f"The Link {link} is invalid.")
    
    change_dir()
    from .components.manga_scraper import SManga

    smanga = SManga(
        url=link,
        user_agent=user_agent,
        file_name=(current_dir / file),
        overwrite=overwrite,
    )

    smanga.start(spider_name=spider)

    if file.lower().endswith(".json"):
        smanga.fix_spider_data()
        smanga.process_spider_data()

@app.command()
def list():
    """List all available spiders."""
    change_dir()
    from .components.manga_scraper import SManga

    smanga = SManga()
    smanga.print_spiders()


@app.command()
def add(
    json_file: Path = typer.Argument(
        ..., help="JSON file path containing manga data.", callback=type_file
    ),
    spider_name: str = typer.Argument(..., help="The spider used to crawling data "),
):
    """Add a manga for future crawling. This allows you to use the -r option later."""
    processor = SpiderDataProcessor(spider_name)
    json_file = current_dir / json_file
    processor.process_data(json_file)


if __name__ == "__main__":
    app()
