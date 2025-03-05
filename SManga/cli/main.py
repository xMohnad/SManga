import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from SManga.core.models import LastChapter
from SManga.core.processor import LastChapterManager
from SManga.interface import MangaBrowser

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
        last_chapter: Optional[LastChapter] = MangaBrowser().run()
        if not last_chapter:
            return

        link = last_chapter.last_chapter
        file = file or Path(last_chapter.file_name)
        spider = spider or last_chapter.site
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
    manager = LastChapterManager()
    data = json.loads(scraped_file_path.read_text())
    scraped_details = data["details"]
    last_chapter = data["chapters"][-1]

    last_chapter_data = LastChapter(
        site=scraped_details.get("source"),
        name=scraped_details.get("manganame"),
        last_chapter=last_chapter.get("document_location"),
        file_name=scraped_file_path.name,
    )

    manager.add_or_update_entry(last_chapter_data)


if __name__ == "__main__":
    app()
