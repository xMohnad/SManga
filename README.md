# SManga

SManga is a command-line tool for scraping manga chapters from various websites using Scrapy and Typer.

______________________________________________________________________

## **Installation**

### **From Source**

To install SManga from the source, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/xMohnad/SManga.git
   cd SManga
   ```

1. **Install SManga as a CLI tool:**

   ```bash
   pip install .
   ```

1. **Verify installation:**

   ```bash
   smanga --help
   ```

______________________________________________________________________

## **Commands Overview**

### 1. **crawl** - Scrape manga chapters from a given link

```bash
smanga crawl <link> [OPTIONS]
```

- **Description:**\
  Scrapes chapters from the provided link and saves the data in a JSON file.

- **Options:**

  - `link` (positional): The link to scrape chapters from.
  - `-f, --file <FILE>`: Output file name for saving the scraped data. Defaults to the manga title.
  - `-d, --dest <DIRECTORY>`: Destination directory to save the scraped file.
  - `-o, --overwrite`: Overwrites the existing file if it already exists.
  - `-r, --recent`: Fetch the most recent saved chapters instead of scraping.
  - `-s, --spider <name>`: Choose a specific spider to use.
  - `-u, --User-Agent <string>`: Custom User-Agent for the scraper.

- **Example:**

  ```bash
  smanga crawl "https://example-manga-site.com/manga-title/1" -f data.json -o -u "Custom-Agent"
  ```

______________________________________________________________________

### 2. **list** - List all available spiders

```bash
smanga list
```

- **Description:**\
  Displays a list of all **available spiders** that can be used for scraping.

- **Example:**

  ```bash
  smanga list
  ```

______________________________________________________________________

### 3. **add** - Add manga data for future scraping

```bash
smanga add <json_file>
```

- **Description:**\
  Adds manga data from a **JSON file** for later use with the `-r` option in the `crawl` command.

- **Options:**

  - `json_file`: The path to the JSON file containing manga data.

- **Example:**

  ```bash
  smanga add manga_scraped_data.json
  ```

______________________________________________________________________

## **Notes**

- Some websites may reject scraper requests. It is recommended to use a valid **User-Agent**.
- The `-r` option allows fetching previously scraped data without making a new request.

______________________________________________________________________

## **License**

SManga is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT). You can freely use, modify, and distribute the tool, provided you retain the original license and copyright.
