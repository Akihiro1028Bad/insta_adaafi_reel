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
import random

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

    def upload_to_instagram(self, video_paths, user_input_text, login_user_name, login_password):
        logger.info(f"ユーザー {login_user_name} の3つの動画アップロードプロセスを開始します")
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

            # 3つの動画をアップロード
            for i, video_path in enumerate(video_paths, 1):
                logger.info(f"{i}つ目の動画アップロードを開始します")
                self._upload_single_video(video_path, user_input_text, wait)
                logger.info(f"{i}つ目の動画アップロードが完了しました")

                # 最後の動画以外の場合、次の動画アップロードのために少し待機
                if i < 3:
                    time.sleep(10)
                    logger.info("次の動画アップロードのために10秒待機します")

            logger.info(f"ユーザー {login_user_name} の3つの動画投稿が完了しました")
            return True
        except Exception as e:
            logger.error(f"アップロードプロセス中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.driver.quit()
            logger.info("WebDriverを終了しました")

    def _upload_single_video(self, video_path, user_input_text, wait):
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

        absolute_file_path = os.path.abspath(video_path)
        logger.info(f"ファイルをアップロードします: {absolute_file_path}")
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'input[type="file"]._ac69')))
        file_input.send_keys(absolute_file_path)

        time.sleep(10)  # ファイルのアップロードを待つ

        try:
            button_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button._acan._acap._acaq._acas._acav._aj1-[type="button"]'))
            )
            button_element.click()
            logger.info("「次へ」ボタンをクリックしました")
        except (TimeoutException, NoSuchElementException):
            logger.warning("「次へ」ボタンが見つからないか、クリックできませんでした。この手順をスキップします。")

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
        caption_text = f'{user_input_text}'
        caption_area.send_keys(caption_text)
        logger.info("キャプションを入力しました")

        time.sleep(10)  # キャプションの入力を待つ

        share_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="シェア"]')))
        share_button.click()
        logger.info("「シェア」ボタンをクリックしました")

        try:
            time.sleep(30)
            element = WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located((By.XPATH, '//div[text()="リール動画がシェアされました"]'))
            )
            logger.info("リール動画が正常にシェアされました")

            # ページをリロード
            logger.info("ページをリロードします")
            self.driver.refresh()
            
            # リロード後のページ読み込み完了を待機
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("ページのリロードが完了しました")


        except TimeoutException:
            logger.error("リール動画がシェアされましたの要素が3分以内に見つかりませんでした")
            raise

def get_random_videos(video_folder, count=3):
    """指定されたフォルダからランダムに3つの異なる動画を選択する"""
    video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.mov', '.avi'))]
    if len(video_files) < count:
        logger.warning(f"フォルダ内の動画ファイルが{count}個未満です")
        return video_files
    return random.sample(video_files, count)