import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from logger import setup_logger
import time

logger = setup_logger('instagram_uploader', 'logs/instagram_uploader.log')

class InstagramUploader:
    def __init__(self):
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            self.driver.delete_all_cookies()
            logger.info("ChromeDriver initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromeDriver: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def upload_to_instagram(self, file_path, user_input_text, login_user_name, login_password):
        try:
            logger.info(f"Starting upload process for user: {login_user_name}")
            self.driver.get('https://www.instagram.com/accounts/login/')

            wait = WebDriverWait(self.driver, 10)

            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_input.send_keys(login_user_name)

            password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(login_password)
            password_input.submit()

            logger.info("Logged in successfully")

            new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div svg[aria-label="新規投稿"]')))
            new_post_btn.click()

            try:
                new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'span svg[aria-label="投稿"]')))
                new_post_btn.click()
            except TimeoutException:
                logger.warning("「投稿」の要素が見つかりませんでした。")

            time.sleep(10)

            # ファイルパスを絶対パスに変換
            absolute_file_path = os.path.abspath(file_path)
            logger.info(f"Uploading file: {absolute_file_path}")
            file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'input[type="file"]._ac69')))
            file_input.send_keys(absolute_file_path)

            time.sleep(10)

            button_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'button._acan._acap._acaq._acas._acav._aj1-[type="button"]')))
            button_element.click()

            time.sleep(10)

            crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1y1aw1k.x1sxyh0.xwib8y2.xurb0ha.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.xl56j7k svg[aria-label='切り取りを選択']"
            div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, crop_selector)))
            div_element.click()

            time.sleep(10)

            vertical_crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xz9dl7a.xn6708d.xsag5q8.x1ye3gou.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1 svg[aria-label='縦型トリミングアイコン']"
            div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, vertical_crop_selector)))
            div_element.click()

            

            for _ in range(2):
                time.sleep(10)

                next_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="次へ"]')))
                next_button.click()

            time.sleep(10)

            caption_area = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'div[aria-label="キャプションを入力…"]')))
            caption_area.send_keys('続きは' + ' @' + login_user_name + ' のストーリーから！\n' + user_input_text)

            time.sleep(10)

            share_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="シェア"]')))
            share_button.click()

            element = WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located((By.XPATH, '//div[text()="リール動画がシェアされました"]'))
            )

            logger.info(f"Upload completed successfully for user: {login_user_name}")
            return True
        except Exception as e:
            logger.error(f"Error during upload process: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.driver.quit()
            logger.info("WebDriver closed")