import scrapy
import json
import requests
from urllib.parse import urljoin
from scrapy_splash import SplashRequest
from scrapy.http import Request
from scrapy.exceptions import CloseSpider


from selenium import webdriver
# from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time



class MensproductSpider(scrapy.Spider):
    name = "mensproduct"
    allowed_domains = ["shop.adidas.jp"]
    start_urls = ["https://shop.adidas.jp/f/v1/pub/product/list?category=wear&gender=mens&order=10&page=1"]
    custom_user_agent = ""

    if custom_user_agent == "":
        print("please give your use agent")
        raise CloseSpider(f"please give your use agent manually here.")

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, headers={'User-Agent': self.custom_user_agent}, callback=self.parse)


    def parse(self, response):
        resp = json.loads(response.body)

        articles = resp.get('articles')
        article_list = resp.get('articles_sort_list')
        api_status = resp.get('api-status')
        http_status = api_status.get('http-status')

        if http_status in ['404', '500']:
            raise CloseSpider(f"HTTP status {http_status} encountered. Crawling terminated.")

        if not articles:
            self.logger.info("No more items to crawl. Crawling terminated.")
            return
        count = 0
        for article in article_list:

            product_details_page = 'https://shop.adidas.jp/products/' + article + "/"

            if product_details_page:
                yield scrapy.Request(
                    url=product_details_page,
                    callback=self.parse_product_details,
                    meta={'product_id': article, "url":product_details_page}
                )
                # count += 1
                # if count > 2:
                #     break

        next_page_url = resp.get('canonical_param_next')
        if next_page_url:
            page_number = next_page_url.split('=')[-1]
            next_page_url_query_params = next_page_url.split('/?')[-1]
            next_page_url_query_part = "?" + next_page_url_query_params
            base_url = "https://shop.adidas.jp/f/v1/pub/product/list/"
            full_next_page_url = urljoin(base_url, next_page_url_query_part)

            yield scrapy.Request(
                url=full_next_page_url,
                callback=self.parse
            )

    def parse_product_details(self, response):
        breadcrumb_urls = response.xpath(
            "//ul[@class='breadcrumbList clearfix test-breadcrumb css-2lfxqg']//li/a/text()").getall()
        breadcrumb_url_xpath = ' / '.join(breadcrumb_urls)
        parts = breadcrumb_url_xpath.split(' / ')
        breadcrumb_url_xpath = ' / '.join(parts[1:])
        product_name = response.xpath("//h1[@class='itemTitle test-itemTitle']/text()").get()
        product_category = response.xpath(
            "//a[@class='groupName']/span[@class='categoryName test-categoryName']/text()").get()
        product_price = response.xpath(
            "//div[contains(@class, 'articlePrice')]//span[contains(@class, 'price-value')]/text()").get()
        size_list = response.xpath("//ul[@class='sizeSelectorList']/li/button/text()").getall()
        tag_list = response.xpath("//div[@class='test-category_link null css-vxqsdw']/div[@class='inner']/a/text()").getall()

        title_of_description = response.xpath("//h4[@class='heading itemFeature test-commentItem-subheading']/text()").get()
        general_description_itemization = response.xpath("//div[@class='description clearfix test-descriptionBlock']/ul[@class='articleFeatures description_part css-1lxspbu']/li/text()").getall()

        # Call parse_size_chart to extract measurements from size chart
        measurements = self.extract_size_chart_measurements(response)


        # Create a dictionary to store the extracted data
        product_details = {
            'Breadcrumb(Category)': breadcrumb_url_xpath,
            'Product Name': product_name,
            'Category': product_category,
            'Pricing': product_price,
            'Available Size': size_list,
            'Title of Description': title_of_description,
            'General Description (Itemization)': general_description_itemization,
            'Tale of SIze': measurements,
            'Keywords': tag_list,

        }

        # API
        product_id = response.meta['product_id']
        api_url = f"https://shop.adidas.jp/f/v2/web/pub/products/article/{product_id}/"
        api_response = requests.get(api_url)
        api_data_json = api_response.json()
        api_data_product = api_data_json['product']['article']['image']['details']
        api_data_product_skus = api_data_json['product']['article']['skus']
        api_data_product_reviews = api_data_json['product']['model']['review']
        api_data_product_reviews_list = api_data_json['product']['model']['review']['reviewSeoLd']
        api_data_product_reviews_count = api_data_product_reviews['reviewCount']

        prefix_url = "https://shop.adidas.jp"
        small_image_urls_with_prefix = [prefix_url + detail["imageUrl"]["small"] for detail in api_data_product]

        # Extract the mainText
        main_text = api_data_json['product']['article']['description']['messages']['mainText']
        main_text = main_text.replace('<br />', '\n')

        # Extract "sizeIndex" and "sizeName" from each item
        sizes = [{"sizeIndex": item["sizeIndex"], "sizeName": item["sizeName"]} for item in api_data_product_skus]

        reviews = []
        for item in api_data_product_reviews_list:
            review = {
                "Reviewer Id": item.get("name", ""),
                "Date": item.get("datePublished", ""),
                "Review Descriptions": item.get("reviewBody", ""),
                "Rating": item.get("reviewRating", {}).get("ratingValue", "")
            }
            reviews.append(review)

        additional_info = {
            'Image URL': small_image_urls_with_prefix,
            'General Description': main_text,
            # 'Tale of Size': sizes,
            'Review Count': api_data_product_reviews_count,
            'Review Details': reviews,
        }

        # Merge additional_info into product_details
        product_details.update(additional_info)

        yield product_details

    def extract_size_chart_measurements(self, response):
        url = response.meta.get('url')
        user_agent = ""

        if user_agent == "":
            print("please give your use agent")
            raise CloseSpider(f"please give your use agent manually here.")

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument('headless')
        chrome_options.add_argument('window-size=1920x1080')

        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(url)
        print("Opened ...")
        # Wait for 10 seconds
        driver.implicitly_wait(5)

        size_table = WebDriverWait(driver, 1).until(
            EC.presence_of_all_elements_located(
                (
                By.XPATH, "//h3[@class='sizeDescriptionWrapHeading js-sizeDescription js-sizeDescription css-nzgyui']"))
        )

        x = 0
        while True:
            x += 1
            driver.execute_script('scrollBy(0,150)')
            time.sleep(.1)
            if x > 32:
                break
        time.sleep(2)

        size_chart_rows = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
            (By.XPATH,
             '//div[@class="sizeChart test-sizeChart css-l7ym9o"]//table[@class="sizeChartTable"][2]//tbody/tr')))
        size_chart_head_elements = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//thead[@class='sizeChartTHeader']/tr/th"))
        )

        size_chart_head_rows = [element.text for element in size_chart_head_elements][1:]
        sizes = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL']
        measurements = {}
        is_first_row = True
        size_chart_data = []

        for row in size_chart_rows:
            row_data = row.text.split()
            if is_first_row:
                headers = row_data
                is_first_row = False
            else:
                row_dict = {}
                for header, value in zip(headers, row_data):
                    row_dict[header] = value
                size_chart_data.append(row_dict)

        measurements = {key: size_chart_data[i] for i, key in enumerate(size_chart_head_rows)}
        return measurements
