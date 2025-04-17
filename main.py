import argparse
import re
import json
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

parser = argparse.ArgumentParser()
parser.add_argument('--target', help='import from file or enter a target url or domain', dest='target')
parser.add_argument('--timeout', help='timeout for WebDriver and page loading', dest='timeout', default=30, type=int)
parser.add_argument('--attempts', help='number of attempts to contact a url', dest='attempts', default=2, type=int)
args = parser.parse_args()

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'


def obtain_dns_information(target_domain):
    record_types = ['A', 'AAAA', 'CNAME', 'NS', 'TXT']
    dns_records = {'dns': {}}
    times = {}
    for record_type in record_types:
        start_time = time.perf_counter()
        try:
            dns_response = subprocess.run(['dig', target_domain, record_type],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=True,
                                          check=True,
                                          timeout=10)
            dns_response = dns_response.stdout

            status = None
            for line in dns_response.splitlines():
                if line.startswith(';; ->>HEADER<<-'):
                    if 'status:' in line:
                        status = line.split('status: ')[1].split(',')[0]
            dns_records['dns'][record_type] = {'status': status, 'response': dns_response, 'error': None}
        except subprocess.TimeoutExpired:
            dns_records['dns'][record_type] = {'error': 'Timeout expired'}
        except Exception as e:
            dns_records['dns'][record_type] = {'error': str(e)}
        finally:
            end_time = time.perf_counter()
            times[record_type] = round((end_time - start_time) * 1000, 3)
    for record_type in record_types:
        dns_records['dns'][record_type]['time'] = times[record_type]
    return dns_records


def run_curl(target_url, timeout):
    curl_print = {'curl': {}}
    start_time = time.perf_counter()
    try:
        curl_result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-H', f'User-Agent: {USER_AGENT}', target_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        curl_print['curl'] = {'exit_code': int(curl_result.returncode), 'http_code': int(curl_result.stdout.strip())}
    except subprocess.TimeoutExpired:
        curl_print['curl'] = {'exit_code': -1, 'error': 'Timeout expired'}
    except Exception as e:
        curl_print['curl'] = {'exit_code': -1, 'error': str(e)}
    finally:
        end_time = time.perf_counter()
        curl_print['curl']['time'] = round((end_time - start_time) * 1000, 3)
    return curl_print


def process_url(target_url, timeout):
    detections = {}
    start_time = time.perf_counter()
    try:
        driver = create_chrome_driver()
        driver.set_page_load_timeout(timeout)

        driver.get(target_url)
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        time.sleep(5)

        logs = driver.get_log('browser')
        last_ext_log = next((e for e in reversed(logs) if 'chrome-extension' in e['message']), None)
        if last_ext_log:
            raw_json_str = last_ext_log['message'].split('"[')[-1].rsplit(']"', 1)[0].replace("\\", '')
            detections['detections'] = json.loads(f'[{raw_json_str}]')
        else:
            detections['detections'] = []
    except Exception as e:
        detections['error'] = str(e).split('\n')[0]
    finally:
        end_time = time.perf_counter()
        detections['time'] = round((end_time - start_time) * 1000, 3)
    return detections


def create_chrome_driver(max_retries=3):
    for attempt in range(max_retries):
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_argument(f'user-agent={USER_AGENT}')

            options.add_extension('wappalyzer-chrome.crx')
            options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

            driver = webdriver.Chrome(options=options, service=Service(executable_path='/usr/local/bin/chromedriver'))
            driver.set_window_size(1920, 1080)
            return driver
        except:
            time.sleep(1)
    raise Exception('Failed to create chrome driver')


if __name__ == '__main__':
    if not args.target:
        parser.print_help()
        exit(1)

    target = args.target.strip()
    if re.match(r'^(http://|https://)', target):
        url = target
        domain = target.split('://')[-1]
    else:
        url = 'https://' + target
        domain = target

    dns_data = obtain_dns_information(domain)
    if dns_data['dns']['A'].get('status') == 'NXDOMAIN':
        print(json.dumps({'target': target} | dns_data))
        exit(0)

    curl_data = run_curl(url, args.timeout)
    if curl_data['curl']['exit_code'] != 0 or not str(curl_data['curl'].get('http_code', '')).startswith(('2', '3')):
        print(json.dumps({'target': target} | dns_data | curl_data))
        exit(0)

    for i in range(args.attempts):
        result = process_url(url, args.timeout)
        if 'error' not in result or (i == args.attempts - 1):
            print(json.dumps({'target': target} | result | dns_data | curl_data))
            break
        else:
            time.sleep(1)
