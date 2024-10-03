import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from datetime import datetime


class Scraper:
    def __init__(self, url, headless=False):
        if headless:
            self.driver = self.setup_driver_with_headless(url)
        else:
            self.driver = self.setup_driver(url)

    def scroll_to_element(self, xpath=None, element=None):
        """Scroll to an element using its XPath and WebElement."""
        try:
            if element:
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center'});",
                                           element)
            elif xpath:
                scroll_element = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center'});",
                                           scroll_element)
        except Exception as e:
            print(f"An error occurred while scrolling: {str(e)}")

    def click_element(self, locator_type, locator_value, timeout=20):
        """Click an element after waiting for it to be clickable."""
        clickable_element = WebDriverWait(self.driver, timeout).until(
            ec.element_to_be_clickable((locator_type, locator_value))
        )
        self.scroll_to_element(element=clickable_element)
        clickable_element.click()

    def page_load_js(self, xpath):
        """method to reload a dynamic list on a page using XPath."""
        print(f"Start: {datetime.now()}")

        # Wait for the list to be present using XPath
        WebDriverWait(self.driver, 20).until(
            ec.presence_of_element_located((By.XPATH, xpath))
        )

        # Disable CSS animations for faster rendering
        disable_animations_script = """
        var style = document.createElement('style');
        style.innerHTML = '* { transition: none !important; animation: none !important; }';
        document.head.appendChild(style);
        """
        self.driver.execute_script(disable_animations_script)

        # Adjust the list's height restrictions and load all items using XPath
        js_script = """
        var list = document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, 
        null).singleNodeValue;
        if (list) {
            list.style.height = 'auto';
            list.style.maxHeight = 'none';
        }
        """
        self.driver.execute_script(js_script, xpath)
        previous_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(.1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # Break the loop if no new content is loaded (i.e., list fully loaded)
            if new_height == previous_height:
                break

            previous_height = new_height

        print(f"Done: {datetime.now()}")

    def select_view_buses_and_load_page(self):
        """Method to select view buses button and loads page for selected button"""
        if self.safe_find_element_text(By.XPATH, "(//div[text()='View Buses'])[1]", timeout=1) != "null":
            self.scroll_to_element(xpath="(//div[text()='View Buses'])[1]")
            time.sleep(1)
            buttons = self.driver.find_elements(By.XPATH, "//div[text()='View Buses']")
            no_of_buttons = len(buttons)
            list_xpath = "(//ul[@class='bus-items'])[{0}]"  # List element needs to be refreshed
            for z in range(no_of_buttons):
                time.sleep(1)
                self.click_element(By.XPATH, "(//div[text()='View Buses'])[1]")  # Xpath of View Buses
                self.page_load_js(list_xpath.format(z + 1))

    def click_link_and_open_in_new_window(self, element, route_name, route_link):
        """Method for Opening Route link buttons in new page and scrapping data"""
        # Control clicks to open in new window
        ActionChains(self.driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()

        # switching to parent window
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.page_load_js("(//ul[@class='bus-items'])[1]")  # List element needs to be refreshed
        self.select_view_buses_and_load_page()
        # Scraping data and storing in data
        page_data = self.scrape_data(route_name, route_link)

        # Closing and witching to parent window
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return page_data

    def check_results(self):
        try:
            element = WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, ".oops-wrapper"))
            )
            self.click_element(By.CSS_SELECTOR, element)
        except (TimeoutException, NoSuchElementException):
            pass

    def navigate_to_pages_and_collect_data(self, page_css):
        """Clicks on page elements specified by CSS selector and collects data from all pages."""
        pages_data = []
        try:
            WebDriverWait(self.driver, 20).until(
                ec.presence_of_all_elements_located((By.CSS_SELECTOR, page_css))
            )
            pages = self.driver.find_elements(By.CSS_SELECTOR, page_css)

            # Loop through the page elements
            for page in pages[:1]:
                self.scroll_to_element(element=page)  # Scrolling to page element
                time.sleep(1)
                page.click()
                # Element of Route names to fetch href and text attribute
                url_elements = self.driver.find_elements(By.CSS_SELECTOR, ".route_details a")
                urls = [elem.get_attribute('href') for elem in url_elements]
                routes = [elem.text for elem in url_elements]
                # Scrolling to first route
                self.scroll_to_element(xpath="(//div[@class='route_details']/a)[1]")

                for index, element in enumerate(url_elements):
                    pages_data += self.click_link_and_open_in_new_window(element, routes[index], urls[index])

        except Exception as e:
            print(f"An error occurred while selecting pages: {str(e)}")
        return pages_data

    def safe_find_element_text(self, by, value, default="null", timeout=3):
        """
        Method for handling no such element, returns default value when exception occurs.
        Uses a short explicit wait to reduce wait time.
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located((by, value))
            )
            return element.text
        except (TimeoutException, NoSuchElementException):
            return default

    def scrape_data(self, route_name, route_link):
        """Custom scrape data method with dynamic xpath, required route_name and route_link"""
        page_data = []
        d_xpath = "(//li[contains(@class,'row-sec clearfix')])[{0}]/descendant::div[contains(@class,'{1}')]"
        # Getting length of routes and scrolling to first element in page
        data_size = len(self.driver.find_elements(By.CSS_SELECTOR, ".travels"))
        self.scroll_to_element(d_xpath.format(1, 'travels'))

        # Looping and scrapping the data using dynamic xpath
        for x in range(1, data_size + 1):
            bus_name = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'travels'))
            bus_type = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'bus-type'))
            dp_time = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'dp-time'))
            duration = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'dur'))
            des_time = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'bp-time'))
            rating_text = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'rating-sec'))
            if rating_text and rating_text.replace('.', '', 1).isdigit():  # Handle float values like '3.5'
                rating = round(float(rating_text), 1)  # Convert to float and round to 1 decimal place
            else:
                rating = None
            price_value = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'fare d-block'))
            price = format(float(re.sub(r'[^\d\.]+', '', price_value)), '.2f')
            seats_value = self.safe_find_element_text(By.XPATH, d_xpath.format(x, 'seat-left'))
            seats_available = int(re.sub(r'[^\d\.]+', '', seats_value))
            raw = [route_name, route_link, bus_name, bus_type, dp_time, duration, des_time, rating, price,
                   seats_available]
            page_data.append(raw)
        return page_data

    @staticmethod
    def setup_driver_with_headless(url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                    "like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disk-cache-size=33554432')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(options=chrome_options)

        driver.implicitly_wait(30)
        driver.set_page_load_timeout(30)
        driver.get(url)
        return driver

    @staticmethod
    def setup_driver(url):
        chrome_options = Options()
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--profile-directory=Default')
        chrome_options.add_argument('--disable-smooth-scrolling')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disk-cache-size=33554432')

        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        driver.implicitly_wait(20)
        driver.get(url)
        return driver

    def quit_driver(self):
        self.driver.quit()

    def scrape_element(self, count):
        print(f"Scraping from element: {count}")
        xpath = f"(//div[@class='rtcCards'])[{count}]"
        self.click_element(By.XPATH, xpath)
        datas = self.navigate_to_pages_and_collect_data(".DC_117_paginationTable div")
        self.click_element(By.XPATH, "//a[@title='redBus_home']")
        return datas


def scrape_data_for_element(count):
    scraper = Scraper("https://www.redbus.in/", headless=False)  # Open a new browser for each thread
    try:
        scrape_data = scraper.scrape_element(count)
    finally:
        scraper.quit_driver()  # Ensure the browser is closed after task completion
    return scrape_data


if __name__ == "__main__":
    # scraper = Scraper("https://www.redbus.in/", headless=False)
    # scraper.click_element(By.XPATH, "(//div[@class='rtcCards'])[1]")
    # scraped_data = scraper.navigate_to_pages_and_collect_data(".DC_117_paginationTable div")
    # print(scraped_data)
    # scraper.quit_driver()

    print(f"Start: {datetime.now()}")

    scraped_data = []
    max_threads = 4
    num_elements = 4

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_element = {executor.submit(scrape_data_for_element, count): count for count in
                             range(1, num_elements + 1)}

        # Process results as they complete
        for future in as_completed(future_to_element):
            count = future_to_element[future]
            try:
                data = future.result()
                scraped_data += data
            except Exception as exc:
                print(f"Element {count} generated an exception: {exc}")

    print(f"End: {datetime.now()}")
    print(scraped_data)

    # print(f"Start: {datetime.now()}")
    # count = 6
    # xpath = "(//div[@class='rtcCards'])[{0}]"
    # scraped_data = []
    # while count < 9:
    #     print("Scraping from element: ", count)
    #     scraper.click_element(By.XPATH, xpath.format(count))
    #     scraped_data += scraper.navigate_to_pages_and_collect_data(".DC_117_paginationTable div")
    #     count += 1
    #     scraper.click_element(By.XPATH, "//span[text()='Home']/parent::a")
    # print(f"End: {datetime.now()}")
    # print(scraped_data)
    # time.sleep(100)
    # scraper.quit_driver()
