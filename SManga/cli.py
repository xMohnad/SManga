import os
import sys
import click
import validators

from SManga.lib import SManga

use_dir = os.getcwd()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)
os.chdir(project_root)


def is_valid_url(url):
    return validators.url(url)


@click.command()
@click.help_option("-h", "--help")
@click.argument(
    "link",
    required=False,
)
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
    help="The name of the file where the scraped data will be saved (with extension).",
)
@click.option(
    "-o",
    "--overwrite",
    is_flag=True,
    help="Overwrite the file if it already exists.",
)
@click.option(
    "--list",
    "-l",
    is_flag=True,
    help="List all available spiders.",
)
def cli(link, spider, file, overwrite, list):
    """SManga CLI: A tool to scrape manga chapters from various sites."""

    if list:
        smanga = SManga(url="")
        smanga.print_spiders()
        return

    if not link:
        click.echo("Error: Missing argument 'LINK'.")
        click.echo("For help, try 'smanga --help or -h'.")
        return

    if not is_valid_url(link):
        click.echo(f"The Link '{link}' is invalid.")

    try:
        output_file_path = os.path.join(use_dir, file)
        smanga = SManga(url=link, file_name=output_file_path, overwrite=overwrite)
        smanga.start(spider_name=spider)
    except Exception as e:
        click.echo(e, err=True)


if __name__ == "__main__":
    cli()
