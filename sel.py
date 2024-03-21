from selenium import webdriver
# from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

website = 'https://shop.adidas.jp/products/II5763/'
user_agent = ""

if user_agent == "":
    print("please give your use agent")
    raise Exception(f"please give your use agent manually here.")

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument('headless')
chrome_options.add_argument('window-size=1920x1080')

chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

driver.get(website)
print("Opened ...")
# Wait for 10 seconds
driver.implicitly_wait(5)

size_table = WebDriverWait(driver, 1).until(
    EC.presence_of_all_elements_located(
        (By.XPATH, "//h3[@class='sizeDescriptionWrapHeading js-sizeDescription js-sizeDescription css-nzgyui']"))
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
    (By.XPATH, '//div[@class="sizeChart test-sizeChart css-l7ym9o"]//table[@class="sizeChartTable"][2]//tbody/tr')))
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

print(measurements)
