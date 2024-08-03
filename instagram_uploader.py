import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from logger import setup_logger

logger = setup_logger('instagram_uploader', 'logs/instagram_uploader.log')

class InstagramUploader:
    def __init__(self):
        logger.info("InstagramUploaderの初期化を開始")
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            self.driver.delete_all_cookies()
            logger.info("ChromeDriverが正常に初期化されました")
        except Exception as e:
            logger.error(f"ChromeDriverの初期化中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def upload_to_instagram(self, file_path, user_input_text, login_user_name, login_password):
        logger.info(f"ユーザー {login_user_name} のアップロードプロセスを開始します")
        try:
            self.driver.get('https://www.instagram.com/accounts/login/')
            logger.info("Instagramのログインページにアクセスしました")

            wait = WebDriverWait(self.driver, 10)

            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_input.send_keys(login_user_name)
            logger.info("ユーザー名を入力しました")

            password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(login_password)
            password_input.submit()
            logger.info("パスワードを入力し、ログインを試みました")

            new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div svg[aria-label="新規投稿"]')))
            new_post_btn.click()
            logger.info("新規投稿ボタンをクリックしました")

            try:
                new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'span svg[aria-label="投稿"]')))
                new_post_btn.click()
                logger.info("「投稿」ボタンをクリックしました")
            except TimeoutException:
                logger.warning("「投稿」の要素が見つかりませんでした。処理を続行します。")

            time.sleep(10)  # UIの読み込みを待つ

            absolute_file_path = os.path.abspath(file_path)
            logger.info(f"ファイルをアップロードします: {absolute_file_path}")
            file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'input[type="file"]._ac69')))
            file_input.send_keys(absolute_file_path)

            time.sleep(10)  # ファイルのアップロードを待つ

            button_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'button._acan._acap._acaq._acas._acav._aj1-[type="button"]')))
            button_element.click()
            logger.info("「次へ」ボタンをクリックしました")

            time.sleep(10)  # 次の画面の読み込みを待つ

            crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1y1aw1k.x1sxyh0.xwib8y2.xurb0ha.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.xl56j7k svg[aria-label='切り取りを選択']"
            div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, crop_selector)))
            div_element.click()
            logger.info("トリミングオプションを選択しました")

            time.sleep(10)  # トリミングオプションの適用を待つ

            vertical_crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xz9dl7a.xn6708d.xsag5q8.x1ye3gou.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1 svg[aria-label='縦型トリミングアイコン']"
            div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, vertical_crop_selector)))
            div_element.click()
            logger.info("縦型トリミングを選択しました")

            for _ in range(2):
                time.sleep(10)  # UIの更新を待つ
                next_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="次へ"]')))
                next_button.click()
                logger.info("「次へ」ボタンをクリックしました")

            time.sleep(10)  # 最終画面の読み込みを待つ

            caption_area = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'div[aria-label="キャプションを入力…"]')))
            caption_text = f'続きは @{login_user_name} のストーリーから！\n{user_input_text}'
            caption_area.send_keys(caption_text)
            logger.info("キャプションを入力しました")

            time.sleep(10)  # キャプションの入力を待つ

            share_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="シェア"]')))
            share_button.click()
            logger.info("「シェア」ボタンをクリックしました")

            try:
                element = WebDriverWait(self.driver, 180).until(
                    EC.presence_of_element_located((By.XPATH, '//div[text()="リール動画がシェアされました"]'))
                )
            except TimeoutException:
                logger.error("リール動画がシェアされましたの要素が3分以内に見つかりませんでした")
                raise

            logger.info(f"ユーザー {login_user_name} の投稿が完了しました")
            return True
        except Exception as e:
            logger.error(f"アップロードプロセス中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.driver.quit()
            logger.info("WebDriverを終了しました")