import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures

class SearchResult:
    def __init__(self, title, link):
        self.title = title
        self.link = link
        self.summary = None
        self.full_content = None

    def to_dict(self):
        return {
            'title': self.title,
            'link': self.link,
            'summary': self.summary,
            'full_content': self.full_content
        }

def fetch_content(url, responseTooLarge, summary=False):
    """
    Fetches the content of the given URL.
    Returns a summary if the summary parameter is set to True.
    """
    try:
        if url.lower().endswith(('.pdf', '.doc', '.ppt')):
            print(f"Error fetching content: {e}")
            return None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        # Use Selenium to fetch conten
        options = Options()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')


        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options)
        driver.set_page_load_timeout(20)

        try:
            driver.get(url)
            html_content = driver.page_source
        except TimeoutException:
            print("Timed out waiting for page to load")
            html_content = "This url is giving page fetch timeout change the query."
        finally:
            driver.quit()
        soup = BeautifulSoup(html_content, 'lxml')
        text = ' '.join(soup.stripped_strings)
        words = text.split()
        fall = 2000/responseTooLarge
        if len(words) > fall:
            words = words[:fall]
            text = ' '.join(words)

        if summary:
            return text[:fall] + '...'
        else:
            return text
    except Exception as e:
        print(f"Error fetching content: {e}")
        return None

def process_results(results, responseTooLarge):
    formatted_results = [SearchResult(res['title'], res['link']) for res in results]
    
    # Initialize a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a future for each result
        futures = {executor.submit(fetch_content, result.link, responseTooLarge, summary=False): result for result in formatted_results[:10]}

        for future in concurrent.futures.as_completed(futures):
            result = futures[future]
            try:
                result.full_content = future.result() or "Error fetching content"
            except Exception as e:
                print(f"Error in fetch_content: {e}")
                result.full_content = "Error fetching content"

    return [res.to_dict() for res in formatted_results]
