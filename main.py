import argparse
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

parser = argparse.ArgumentParser()
parser.add_argument('--url', help='import from file or enter a url', dest='url')
parser.add_argument('--timeout', help='timeout for WebDriver and page loading', dest='timeout', default=30, type=int)
parser.add_argument('--attempts', help='number of attempts to contact a url', dest='attempts', default=2, type=int)
args = parser.parse_args()


def create_chrome_driver(max_retries=3):
    for attempt in range(max_retries):
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            options.add_extension('wappalyzer-chrome.crx')
            options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

            driver = webdriver.Chrome(options=options, service=Service(executable_path='/usr/local/bin/chromedriver'))
            driver.set_window_size(1920, 1080)
            return driver
        except:
            time.sleep(1)
    raise Exception('Failed to create chrome driver')


def process_url(target_url, timeout):
    try:
        driver = create_chrome_driver()
        driver.set_page_load_timeout(timeout)

        driver.get(target_url)
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        time.sleep(5)

        logs = driver.get_log('browser')
        last_ext_log = next((e for e in reversed(logs) if 'chrome-extension' in e['message']), None)
        raw_json_str = last_ext_log['message'].split('"[')[-1].rsplit(']"', 1)[0].replace("\\", '')

        return target_url, json.loads(f'[{raw_json_str}]')
    except Exception as e:
        return target_url, str(e).split('\n')[0]


if __name__ == '__main__':
    if not args.url:
        parser.print_help()
        exit(1)

    url = args.url.lower().strip()
    if not re.match(r'^(http://|https://)', url):
        url = 'https://' + url
    if re.search(r'^https?://', url):
        for i in range(args.attempts):
            url, detections = process_url(url, timeout=args.timeout)
            if isinstance(detections, list) or (i == args.attempts - 1):
                print(json.dumps({'url': url, 'result': detections}))
                break
            else:
                time.sleep(2)
    else:
        print(json.dumps({'url': url, 'result': 'Neither a valid URL nor a file path'}))
