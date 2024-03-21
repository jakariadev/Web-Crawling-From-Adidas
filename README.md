# Adidas-Product-Scraping

- Used Scrapy, Splash, Python and Selenium

# Saved Data
data.xlsx


## We can collect easily Thousands of data from Adidas

# Instructions to Run

### Create and Active Virtualenvironment 

Stay in Project level and Run
 
1. ```python3 -m venv scraping```

2. ```source scraping/bin/activate```

### install dependencies

``` pip3 install -r requirements.txt```

### Go to "Adidas" directory

```scrapy crawl mensproduct```

### To make a CSV or XLSX File

```scrapy crawl mensproduct -o data.csv ```

```python3 -c 'import pandas as pd; pd.read_csv("data.csv").to_excel("data.xlsx", index=False)' ```

