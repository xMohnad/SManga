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
    pip install dist/SManga-*.tar.gz
    ```
    
    -   or `.whl`
    
    ```sh
    pip install dist/SManga-*-py3-none-any.whl
    ```

### **Commands Overview**  

#### 1. **crawl**: Scrape manga chapters from a given link  
```bash
smanga crawl <link> [OPTIONS]
```

- **Description:**  
  Scrapes chapters from the provided link and saves the data in a JSON file.

- **Parameters:**
  - `link`: The link to scrape chapters from.
  - `-f, --file`: The output file to save the data (default: `chapters.json`).
  - `-u, --User-Agent`: A custom User-Agent to use during scraping.
  - `-o, --overwrite`: Overwrite the existing file if it already exists.
  - `-r, --recent`: Display the most recent saved chapters.
  - `-s, --spider`: The spider to use (optional).

- **Examples:**
  ```bash
  smanga crawl https://example-manga-site.com/manga-title/1 -f data.json -o -u "Custom-Agent"
  ```

---

#### 2. **list**: List all available spiders  
```bash
smanga list
```

- **Description:**  
  Displays a list of all **available spiders** that can be used for scraping.

- **Examples:**
  ```bash
  smanga list
  ```

---

#### 3. **add**: Add manga data for future scraping  
```bash
smanga add <json_file> <spider_name>
```

- **Description:**  
  Adds manga data from a **JSON file** to be used later with the `-r` option in the `crawl` command.

- **Parameters:**
  - `json_file`: The path to the JSON file containing manga data.
  - `spider_name`: The name of the spider used for scraping the data.

- **Examples:**
  ```bash
  smanga add manga_data.json "example_spider"
  ```

---


### **To use the `SManga`**
```bash
smanga [COMMAND] [OPTIONS]
```

---

### **Notes**  
- Some websites may reject scraper requests, so using an appropriate **User-Agent** is recommended.  
- Use the `--overwrite` option cautiously to avoid losing important data.

---

## License

SManga is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT). This means you can freely use, modify, and distribute the tool, provided you include the original license and copyright notice in any distributions or derivative works.


