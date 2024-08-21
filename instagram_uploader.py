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
from session_manager import session_manager

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
            # セッション情報を取得
            session_data = session_manager.load_session(login_user_name)
            
            if session_data and session_manager.is_session_valid(session_data):
                logger.info(f"有効なセッションが見つかりました: {login_user_name}")
                self._restore_session(session_data)
            else:
                logger.info(f"有効なセッションが見つからないため、ログインを実行します: {login_user_name}")
                self._login(login_user_name, login_password)
                
                # 新しいセッション情報を保存
                #new_session_data = self._get_current_session()
                #session_manager.save_session(login_user_name, new_session_data)

            # 3つの動画をアップロード
            for i, video_path in enumerate(video_paths, 1):
                logger.info(f"{i}つ目の動画アップロードを開始します")
                self._upload_single_video(video_path, user_input_text)
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

    def _restore_session(self, session_data):
        """
        保存されたセッション情報を復元
        
        :param session_data: 復元するセッションデータ
        """
        logger.info("保存されたセッション情報を復元します")
        self.driver.get('https://www.instagram.com')
        for cookie in session_data['cookies']:
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        logger.info("セッション情報が正常に復元されました")

    def _login(self, username, password):
        """
        Instagramにログイン
        
        :param username: ユーザー名
        :param password: パスワード
        """
        logger.info(f"ユーザー {username} のログインを開始します")
        self.driver.get('https://www.instagram.com/accounts/login/')
        
        wait = WebDriverWait(self.driver, 10)
        
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_input.send_keys(username)
        logger.info("ユーザー名を入力しました")

        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(password)
        password_input.submit()
        logger.info("パスワードを入力し、ログインを試みました")
        
        # ログイン成功の確認
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div svg[aria-label="新規投稿"]')))
            logger.info("ログインに成功しました")
        except TimeoutException:
            logger.error("ログインに失敗しました")
            raise Exception("ログインに失敗しました")

    def _get_current_session(self):
        """
        現在のセッション情報を取得
        
        :return: セッションデータ（辞書形式）
        """
        cookies = self.driver.get_cookies()
        expiry = time.time() + 3600 * 24  # 24時間後に有効期限切れ
        return {
            'cookies': cookies,
            'expiry': expiry
        }

    def _upload_single_video(self, video_path, user_input_text):
        """
        単一の動画をアップロード
        
        :param video_path: アップロードする動画のパス
        :param user_input_text: 投稿のキャプション
        """
        logger.info(f"動画のアップロードを開始します: {video_path}")
        
        wait = WebDriverWait(self.driver, 10)

        self.random_wait()  # UIの読み込みを待つ

        # 「後で」ボタンを探してクリック
        try:
            later_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "_a9--") and contains(@class, "ap36") and contains(@class, "a9_1") and contains(text(), "後で")]'))
            )
            later_button.click()
            logger.info("「後で」ボタンをクリックしました")
        except TimeoutException:
            logger.info("「後で」ボタンが見つかりませんでした。処理を続行します。")
        except Exception as e:
            logger.error(f"「後で」ボタンのクリック中にエラーが発生しました: {str(e)}")

        self.random_wait()  # UIの読み込みを待つ
        
        # 新規投稿ボタンをクリック
        new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div svg[aria-label="新規投稿"]')))
        new_post_btn.click()
        logger.info("新規投稿ボタンをクリックしました")

        self.random_wait()  # UIの読み込みを待つ

        # 投稿ボタンを探してクリック
        try:
            post_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "x9f619") and contains(@class, "xjbqb8w")]//span[contains(text(), "Post") or contains(text(), "投稿")]'))
            )
            post_button.click()
            logger.info("投稿ボタンをクリックしました")
        except TimeoutException:
            logger.warning("投稿ボタンが見つかりませんでした。処理を続行します。")
        except Exception as e:
            logger.error(f"投稿ボタンのクリック中にエラーが発生しました: {str(e)}")

        self.random_wait()  # UIの読み込みを待つ

        # ファイルをアップロード
        absolute_file_path = os.path.abspath(video_path)
        logger.info(f"ファイルをアップロードします: {absolute_file_path}")
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]._ac69')))
        file_input.send_keys(absolute_file_path)

        self.random_wait()  # ファイルのアップロードを待つ

        # 次へボタンをクリック
        try:
            button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button._acan._acap._acaq._acas._acav._aj1-[type="button"]')))
            button_element.click()
            logger.info("「次へ」ボタンをクリックしました")
        except (TimeoutException, NoSuchElementException):
            logger.warning("「次へ」ボタンが見つからないか、クリックできませんでした。この手順をスキップします。")

        self.random_wait()  # 次の画面の読み込みを待つ

        # トリミングオプションを選択
        crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1y1aw1k.x1sxyh0.xwib8y2.xurb0ha.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.xl56j7k svg[aria-label='切り取りを選択']"
        div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, crop_selector)))
        div_element.click()
        logger.info("トリミングオプションを選択しました")

        self.random_wait()  # トリミングオプションの適用を待つ

        # 縦型トリミングを選択
        vertical_crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xz9dl7a.xn6708d.xsag5q8.x1ye3gou.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1 svg[aria-label='縦型トリミングアイコン']"
        div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, vertical_crop_selector)))
        div_element.click()
        logger.info("縦型トリミングを選択しました")

        # 「次へ」ボタンを2回クリック
        for _ in range(2):
            self.random_wait()  # UIの更新を待つ
            next_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[text()="次へ"]')))
            next_button.click()
            logger.info("「次へ」ボタンをクリックしました")

        self.random_wait()  # 最終画面の読み込みを待つ

        # キャプションを入力
        caption_area = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="キャプションを入力…"]')))
        caption_text = f'{user_input_text}'
        caption_area.send_keys(caption_text)
        logger.info("キャプションを入力しました")

        self.random_wait()  # キャプションの入力を待つ

        # 共有ボタンをクリック
        share_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[text()="シェア"]')))
        share_button.click()
        logger.info("「シェア」ボタンをクリックしました")

        try:
            self.random_wait(30, 60)  # 投稿完了を待つ時間を長めに設定
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

    def random_wait(self, min_time=10, max_time=30):
        """指定された範囲内でランダムな秒数待機する"""
        wait_time = random.uniform(min_time, max_time)
        logger.info(f"{wait_time:.2f}秒間待機します")
        time.sleep(wait_time)

# インスタンスの作成部分は削除し、必要に応じて他のファイルで作成するように変更