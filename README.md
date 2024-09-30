# SManga

SManga is a command-line tool for scraping manga chapters from various websites using Scrapy. 

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/xMohnad/SManga.git
   cd SManga
   ```

2. Install the package:
    ```sh
    pip install dist/SManga-x.x.tar.gz
    ```
    
    -   or `.whl`
    
    ```sh
    pip install dist/SManga-x.x-py3-none-any.whl
    ```

## Usage

To use the `SManga` CLI, you can run the following commands:

```bash
smanga [OPTIONS] [LINK]
```

### Options
```bash
❯ SManga -h
Usage: smanga [OPTIONS] [LINK]

  SManga: A tool to scrape manga chapters from various sites.

Options:
  -h, --help                Show this message and exit.
  -s, --spider TEXT         The name of the spider to use (optional).
  -f, --file TEXT           File to save scraped data (with extension),
                            default: `chapters.json`.
  -o, --overwrite           Overwrite existing file if it exists.
  -l, --list                List all available spiders.
  -r, --recent              Display the most recent chapters saved from
                            previous scrapes.
  -a, --add <TEXT PATH>...  Add a manga for future crawling. Provide the
                            spider name and JSON file path containing manga
                            data. Example: -a my_spider data.json. This allows
                            you to use the -r option later.
```

### Examples

#### Scraping a manga

   ```bash
   smanga https://example-manga-site.com/manga-title/1 -f filename.ext
   ```

#### Listing available spiders

   ```bash
   smanga --list
   ```

#### Viewing the most recent chapters

   ```bash
   smanga --recent
   ```

#### Adding a manga for future crawling

   ```bash
   smanga --add my_spider manga_data.json
   ```

## License

SManga is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT). This means you can freely use, modify, and distribute the tool, provided you include the original license and copyright notice in any distributions or derivative works.
