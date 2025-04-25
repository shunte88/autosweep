import time
import yaml
import os
import re
import sys
import json
import logging
import requests
from datetime import datetime
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

sweep_opts = {
    'profile_dir': os.path.join(os.getcwd(), "chrome_profile"),
    'chromeProfilePath': os.path.join(os.getcwd(), "chrome_profile", "scene_profile"),
    'log_dir': os.path.join(os.getcwd(), "logs"),
    'logging_verbose': True,
    'webdriver_logging': 3,
    'FOOD_ngxFrame': '284415',
}

def ensure_log_dir():
    if not os.path.exists(sweep_opts['log_dir']):
        os.makedirs(sweep_opts['log_dir'])

def _get_timestamp():
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def _init_logging(**kwargs):
    ensure_log_dir()
    _ = logging.getLogger(__name__)
    logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    handlers = [
        logging.FileHandler(os.path.join(sweep_opts['log_dir'], f'autosweeps_log_{_get_timestamp()}.log')),
        logging.StreamHandler(sys.stdout)
    ])
    # Set the formatter for the handler
    logging.info(f"Setting log directory at {sweep_opts['log_dir']}")
    if sweep_opts['logging_verbose']:
        sweep_opts['webdriver_logging'] = 0

# Load user data from config.yml
def load_user_config(path='config.yml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def ensure_chrome_profile(sweep_opts):
    if not os.path.exists(sweep_opts['profile_dir']):
        os.makedirs(sweep_opts['profile_dir'])
    if not os.path.exists(sweep_opts['chromeProfilePath']):
        os.makedirs(sweep_opts['chromeProfilePath'])
    return sweep_opts['chromeProfilePath']

def chrome_browser_options(sweep_opts):
    ensure_chrome_profile(sweep_opts)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920x1080")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-autofill")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-animations")
    options.add_argument("--disable-cache")
    options.add_argument(f"user-agent={UserAgent().random}")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    prefs = {
        "profile.default_content_setting_values.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)

    if len(chromeProfilePath) > 0:
        initial_path = os.path.dirname(chromeProfilePath)
        profile_dir = os.path.basename(chromeProfilePath)
        sys.path.append(chromeProfilePath)
        sys.path.append(profile_dir)
        options.add_argument(f'--user-data-dir={initial_path}')
        options.add_argument(f'--profile-directory={profile_dir}')
    else:
        options.add_argument("--incognito")

    return options

def init_browser(chrome_options) -> webdriver.Chrome:
    try:
        options = chrome_options
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        #setup_request_session()
        return driver
    except Exception as e:
        logging.critical(f"Failed to initialize browser: {str(e)}")
        sys.exit(1)

# email submittal - and that's that
def fill_sweepstake_form(driver, config, url):

    logging.info(f"Load page {sweep_url}")
    driver.get(sweep_url)
    WebDriverWait(driver, 10)
    time.sleep(2)
    try:
        logging.info("Locate iFrame and hidden gotchas")
        sweep_source = driver.page_source
        _ngxFrame = re.findall("ngxFrame\d\w+", sweep_source)[0]
        logging.info(f"iFrame found -> {_ngxFrame}")
        driver.switch_to.frame(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, _ngxFrame))
            )
        )
        time.sleep(3)
        logging.info(f"Email entry --> {config['setup']['email']}")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "xReturningUserEmail"))
        )
        email_input.clear()
        email_input.send_keys(config['setup']['email'])
        time.sleep(2)
        logging.info("Navigate entry submission")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
        driver.switch_to.default_content()
        driver.switch_to.frame(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, _ngxFrame))
            )
        )
        for _ in range(2):
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except:
                pass
            time.sleep(2)
        action = ActionChains(driver)
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.ENTER)
        action.perform()
        time.sleep(3)
        logging.info("Done, Bye")

    except Exception as e:
        print("Exception occurred:", e)


if __name__ == "__main__":

    _init_logging()
    config = load_user_config()

    chromeProfilePath = os.path.join(os.getcwd(), "chrome_profile", "scene_profile")
    sys.path.append(sweep_opts['chromeProfilePath'])
    profile_dir = os.path.basename(chromeProfilePath)
    sys.path.append(sweep_opts['profile_dir'])
    
    # enter all active sweepstakes
    for sweep_url in [
        'https://www.hgtv.com/sweepstakes/get-outside?xp=sistersite',
        'https://www.hgtv.com/sponsored/sweeps/valspar-made-for-more-sweepstakes',
        'https://www.hgtv.com/sweepstakes/5k-grocery-giveaway?xp=sistersite',
        'https://www.foodnetwork.com/sponsored/sweepstakes/get-outside?xp=sistersite',
        'https://www.foodnetwork.com/sponsored/sweepstakes/5k-grocery-giveaway?xp=sistersite',
        'https://www.foodnetwork.com/sponsored/sweepstakes/spring-it-forward?xp=sistersite',
        'https://www.tlc.com/sweepstakes/spring-it-forward?xp=sistersite',
    ]:
        logging.info(f"Init browser for {sweep_url}")
        # re-init each time - think???
        driver = init_browser(
            chrome_browser_options(sweep_opts)
        )
        try:
            fill_sweepstake_form(driver, config, sweep_url)
        except:
            pass
        finally:
            time.sleep(5)
            driver.quit()
