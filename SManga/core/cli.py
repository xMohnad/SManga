import os
import sys
import click
from click_completion import init

# Initialize the click-completion
init()

use_dir = os.getcwd()


def change_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    sys.path.append(project_root)
    os.chdir(project_root)


@click.command()
@click.help_option("-h", "--help")
@click.argument("link", required=False)
@click.option(
    "-s",
    "--spider",
    default=None,
    help="The name of the spider to use (optional).",
)
@click.option(
    "-f",
    "--file",
    default="chapters.json",
    help="File to save scraped data (with extension), default: `chapters.json`.",
)
@click.option(
    "-o",
    "--overwrite",
    is_flag=True,
    help="Overwrite existing file if it exists.",
)
@click.option(
    "--list",
    "-l",
    is_flag=True,
    help="List all available spiders.",
)
@click.option(
    "--recent",
    "-r",
    is_flag=True,
    help="Display the most recent chapters saved from previous scrapes.",
)
@click.option(
    "-a",
    "--add",
    nargs=2,
    type=(str, click.Path(exists=True)),
    help=(
        "Add a manga for future crawling. "
        "Provide the spider name and JSON file path containing manga data. "
        "Example: -a my_spider data.json. "
        "This allows you to use the -r option later."
    ),
    required=False,
)
def cli(link, spider, file, overwrite, list, recent, add):
    """SManga: A tool to scrape manga chapters from various sites."""

    if add:
        from .components import SpiderDataProcessor

        spider_name, json_file = add
        processor = SpiderDataProcessor(spider_name)
        json_file = os.path.join(use_dir, json_file)
        processor.process_data(json_file)
        return

    if recent:
        import curses
        from .interface import UI

        item = curses.wrapper(UI)
        if not item:
            return
        link = item.lastchapter
        file = os.path.basename(item.json_file)

    change_dir()

    from .components.manga_scraper import SManga

    if list:
        smanga = SManga()
        smanga.print_spiders()
        return

    if not link:
        click.echo("Error: Missing argument 'LINK'.")
        click.echo("For help, try 'smanga --help or -h'.")
        return

    if not link.startswith("http"):
        click.echo(f"The Link '{link}' is invalid.", err=True)
        return

    try:
        output_file_path = os.path.join(use_dir, file)
        smanga = SManga(url=link, file_name=output_file_path, overwrite=overwrite)
        smanga.start(spider_name=spider)

        if file.lower().endswith(".json"):
            smanga.fix_spider_data()
            smanga.process_spider_data()
    except Exception as e:
        click.echo(e, err=True)


if __name__ == "__main__":
    cli()
