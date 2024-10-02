from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from datetime import datetime


class Scraper:
    def __init__(self, driver):
        self.driver = driver

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

    def click_element(self, locator_type, locator_value, timeout=10):
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
        WebDriverWait(self.driver, 10).until(
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
            time.sleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # Break the loop if no new content is loaded (i.e., list fully loaded)
            if new_height == previous_height:
                break

            previous_height = new_height

        print(f"Done: {datetime.now()}")

    def select_view_buses_and_load_page(self):
        """Method to select view buses button and loads page for selected button"""
        if self.safe_find_element_text(By.XPATH, "(//div[text()='View Buses'])[1]") != "null":
            time.sleep(1)
            self.scroll_to_element(xpath="(//div[text()='View Buses'])[1]")
            time.sleep(1)
            buttons = self.driver.find_elements(By.XPATH, "//div[text()='View Buses']")
            no_of_buttons = len(buttons)
            count = 1
            xpath = "(//ul[@class='bus-items'])[{0}]"  # List element needs to be refreshed
            for z in range(no_of_buttons):
                time.sleep(2)
                self.click_element(By.XPATH, "(//div[text()='View Buses'])[1]")  # Xpath of View Buses
                self.page_load_js(xpath.format(z+1))
                count += 1

    def click_link_and_open_in_new_window(self, element, route_name, route_link):
        """Method for Opening Route link buttons in new page and scrapping data"""
        # Control clicks to open in new window
        ActionChains(self.driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()

        # switching to parent window
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.page_load_js("(//ul[@class='bus-items'])[1]")  # List element needs to be refreshed
        self.select_view_buses_and_load_page()
        # Scraping data and storing in data
        data = self.scrape_data(route_name, route_link)

        # Closing and witching to parent window
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return data

    def navigate_to_pages_and_collect_data(self, page_css):
        """Clicks on page elements specified by CSS selector and collects data from all pages."""
        data = []
        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_all_elements_located((By.CSS_SELECTOR, page_css))
            )
            pages = self.driver.find_elements(By.CSS_SELECTOR, page_css)

            # Loop through the page elements
            for page in pages:
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
                    data += self.click_link_and_open_in_new_window(element, routes[index], urls[index])

        except Exception as e:
            print(f"An error occurred while selecting pages: {str(e)}")
        return data

    def safe_find_element_text(self, by, value, default="null"):
        """Method for handling no such element, returns null value when exception occurs"""
        try:
            return self.driver.find_element(by, value).text
        except NoSuchElementException:
            return default

    def scrape_data(self, route_name, route_link):
        """Custom scrape data method with dynamic xpath, required route_name and route_link"""
        data = []
        xpath = "(//li[contains(@class,'row-sec clearfix')])[{0}]/descendant::div[contains(@class,'{1}')]"
        # Getting length of routes and scrolling to first element in page
        data_size = len(self.driver.find_elements(By.CSS_SELECTOR, ".travels"))
        self.scroll_to_element(xpath.format(1, 'travels'))

        # Looping and scrapping the data using dynamic xpath
        for x in range(1, data_size + 1):
            bus_name = self.safe_find_element_text(By.XPATH, xpath.format(x, 'travels'))
            bus_type = self.safe_find_element_text(By.XPATH, xpath.format(x, 'bus-type'))
            dp_time = self.safe_find_element_text(By.XPATH, xpath.format(x, 'dp-time'))
            duration = self.safe_find_element_text(By.XPATH, xpath.format(x, 'dur'))
            des_time = self.safe_find_element_text(By.XPATH, xpath.format(x, 'bp-time'))
            rating = self.safe_find_element_text(By.XPATH, xpath.format(x, 'rating-sec'))
            price = self.safe_find_element_text(By.XPATH, xpath.format(x, 'fare d-block'))
            seats_available = self.safe_find_element_text(By.XPATH, xpath.format(x, 'seat-left'))
            raw = [route_name, route_link, bus_name, bus_type, dp_time, duration, des_time, rating, price,
                   seats_available]
            data.append(raw)
        return data


if __name__ == "__main__":
    web_driver = webdriver.Chrome()
    web_driver.get("https://www.redbus.in/")
    web_driver.maximize_window()
    web_driver.implicitly_wait(10)
    scraper = Scraper(web_driver)

    scraper.click_element(By.XPATH, "(//div[@class='rtcCards'])[1]")
    scraped_data = scraper.navigate_to_pages_and_collect_data(".DC_117_paginationTable div")
    # print(scraped_data)
    # time.sleep(100)
    web_driver.quit()
