import curses
from pathlib import Path
from typing import Annotated, Optional

import typer

from ..core import MangaDataProcessor
from ..interface import UI

# Typer app configuration
app = typer.Typer(
    help="SManga: A tool to scrape manga chapters from various sites.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def validate_link(link: Optional[str]) -> str:
    """Validate the provided link."""
    if link is None:
        raise typer.BadParameter("The Link is required unless using --recent.")
    if not link.startswith("http"):
        raise typer.BadParameter(f"The Link '{link}' is invalid.")
    return link


@app.command()
def crawl(
    link: Optional[str] = typer.Argument(
        None, help="The link to scrape.", show_default=False
    ),
    file: Optional[Path] = typer.Option(
        None,
        "-f",
        "--file",
        help=(
            "The name of the file to save the scraped data. "
            "If not provided, the manga's name will be used as the file name."
        ),
        dir_okay=False,
        resolve_path=True,
        writable=True,
    ),
    dest: Optional[Path] = typer.Option(
        None,
        "-d",
        "--dest",
        help="Destination directory to save the scraped data.",
        file_okay=False,
        resolve_path=True,
        writable=True,
        exists=True,
    ),
    overwrite: bool = typer.Option(
        False, "-o", "--overwrite", help="Overwrite existing file if it exists."
    ),
    recent: bool = typer.Option(
        False, "-r", "--recent", help="Display the most recent chapters saved."
    ),
    spider: Optional[str] = typer.Option(
        None, "-s", "--spider", help="Spider name (optional)."
    ),
    user_agent: Optional[str] = typer.Option(
        None, "-u", "--User-Agent", help="Custom User-Agent for scraping."
    ),
):
    """Crawl a specific manga site to scrape chapter data."""
    if recent:
        item = curses.wrapper(UI)
        if not item:
            return

        link = item.lastchapter
        file = file or Path(item.json_file)
        if isinstance(file, str):
            file = Path(file.name)
    else:
        link = validate_link(link)
    from ..core.scraper import SManga

    smanga = SManga(
        url=link,
        user_agent=user_agent,
        dest_path=dest,
        file_name=file,
        overwrite=overwrite,
    )
    smanga.start(spider_name=spider)


@app.command()
def list():
    """List all available spiders."""
    from ..core.scraper import SManga

    smanga = SManga()
    smanga.print_spiders()


@app.command()
def add(
    scraped_file_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            resolve_path=True,
            help="JSON file path containing manga data.",
            show_default=False,
        ),
    ],
):
    """Add a manga for future crawling to enable the -r option later."""
    processor = MangaDataProcessor()
    processor.process_scraped_data(scraped_file_path=scraped_file_path)


if __name__ == "__main__":
    app()
