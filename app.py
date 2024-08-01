import os
import random
import time
import configparser
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import threading
import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import traceback

app = Flask(__name__)

# 定数の定義
VIDEO_FOLDER = 'upload_videos'
PRESET_FILE = 'presets.txt'
ACCOUNTS_FILE = 'accounts.ini'
SCHEDULE_FILE = 'schedule.ini'

class InstagramUploader:
    def __init__(self):
        try:
            # ChromeDriverを初期化
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            self.driver.delete_all_cookies()
        except Exception as e:
            print(f"ChromeDriverの初期化中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            raise

    def upload_to_instagram(self, file_path, user_input_text, login_user_name, login_password):
        try:
            # インスタグラムのログインページを開く
            self.driver.get('https://www.instagram.com/accounts/login/')

            wait = WebDriverWait(self.driver, 10)

            # ユーザー名とパスワードを入力
            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_input.send_keys(login_user_name)

            password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(login_password)
            password_input.submit()

            wait = WebDriverWait(self.driver, 10)

            # 新規投稿ボタンをクリック
            new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div svg[aria-label="新規投稿"]')))
            new_post_btn.click()

            wait = WebDriverWait(self.driver, 10)

            try:
                # 「投稿」の要素が見つかったらクリック
                new_post_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'span svg[aria-label="投稿"]')))
                new_post_btn.click()
            except TimeoutException:
                print("「投稿」の要素が見つかりませんでした。")

            wait = WebDriverWait(self.driver, 10)

            # ファイルを選択
            file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'input[type="file"]._ac69')))
            absolute_path = os.path.abspath(file_path)
            file_input.send_keys(absolute_path)

            wait = WebDriverWait(self.driver, 10)

            # リールオプションを選択
            button_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'button._acan._acap._acaq._acas._acav._aj1-[type="button"]')))
            button_element.click()

            wait = WebDriverWait(self.driver, 10)

            # 切り取りを選択
            crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1y1aw1k.x1sxyh0.xwib8y2.xurb0ha.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.xl56j7k svg[aria-label='切り取りを選択']"
            div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, crop_selector)))
            div_element.click()

            wait = WebDriverWait(self.driver, 10)

            # 縦型トリミングを選択
            vertical_crop_selector = "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xz9dl7a.xn6708d.xsag5q8.x1ye3gou.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1 svg[aria-label='縦型トリミングアイコン']"
            div_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, vertical_crop_selector)))
            div_element.click()

            wait = WebDriverWait(self.driver, 10)

            # "次へ"ボタンを2回クリック
            for _ in range(2):
                next_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="次へ"]')))
                next_button.click()

            wait = WebDriverWait(self.driver, 10)

            # キャプションを入力
            caption_area = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'div[aria-label="キャプションを入力…"]')))
            caption_area.send_keys('続きは' + ' @' + login_user_name + ' のストーリーから！\n' + user_input_text)

            wait = WebDriverWait(self.driver, 10)

            # シェアボタンをクリック
            share_button = wait.until(EC.presence_of_element_located((By.XPATH,'//div[text()="シェア"]')))
            share_button.click()

            wait = WebDriverWait(self.driver, 10)

            # アップロード完了を確認
            element = WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located((By.XPATH, '//div[text()="リール動画がシェアされました"]'))
            )

            wait = WebDriverWait(self.driver, 60)

            return True
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            return False
        finally:
            self.driver.quit()

def get_random_video():
    # 動画フォルダが存在しない場合は作成
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
    # 動画ファイルのリストを取得
    video_files = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(('.mp4', '.mov', '.avi'))]
    if not video_files:
        return None
    # ランダムに動画を選択
    return os.path.join(VIDEO_FOLDER, random.choice(video_files))

def get_accounts():
    # アカウント情報を設定ファイルから読み込む
    config = configparser.ConfigParser()
    config.read(ACCOUNTS_FILE)
    return {section: dict(config[section]) for section in config.sections()}

def save_account(username, password):
    # 新しいアカウント情報を設定ファイルに保存
    config = configparser.ConfigParser()
    config.read(ACCOUNTS_FILE)
    config[username] = {'password': password}
    with open(ACCOUNTS_FILE, 'w') as configfile:
        config.write(configfile)

def get_presets():
    # 定型文を設定ファイルから読み込む
    if not os.path.exists(PRESET_FILE):
        return []
    with open(PRESET_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_preset(preset):
    # 新しい定型文を設定ファイルに追加
    with open(PRESET_FILE, 'a', encoding='utf-8') as f:
        f.write(preset + '\n')

def save_schedule(accounts, caption, start_time, end_time):
    # スケジュール情報を設定ファイルに保存
    config = configparser.ConfigParser()
    config['Schedule'] = {
        'accounts': ','.join(accounts),
        'caption': caption,
        'start_time': start_time,
        'end_time': end_time,
        'last_post_date': ''  # 最後に投稿した日付を記録
    }
    with open(SCHEDULE_FILE, 'w') as configfile:
        config.write(configfile)

def load_schedule():
    # スケジュール情報を設定ファイルから読み込む
    config = configparser.ConfigParser()
    config.read(SCHEDULE_FILE)
    if 'Schedule' in config:
        schedule = dict(config['Schedule'])
        schedule['accounts'] = schedule['accounts'].split(',')
        return schedule
    return None

def update_last_post_date(date):
    # 最後に投稿した日付を更新
    config = configparser.ConfigParser()
    config.read(SCHEDULE_FILE)
    if 'Schedule' in config:
        config['Schedule']['last_post_date'] = date.strftime('%Y-%m-%d')
        with open(SCHEDULE_FILE, 'w') as configfile:
            config.write(configfile)

def schedule_post():
    try:
        schedule_info = load_schedule()
        if schedule_info:
            start_time = datetime.datetime.strptime(schedule_info['start_time'], '%H:%M').time()
            end_time = datetime.datetime.strptime(schedule_info['end_time'], '%H:%M').time()
            last_post_date = schedule_info.get('last_post_date', '')
            
            now = datetime.datetime.now()
            
            # 今日まだ投稿していない場合のみ処理を続行
            if last_post_date != now.strftime('%Y-%m-%d'):
                if start_time <= now.time() <= end_time:
                    video_path = get_random_video()
                    if video_path:
                        accounts = get_accounts()
                        for account in schedule_info['accounts']:
                            uploader = InstagramUploader()
                            success = uploader.upload_to_instagram(video_path, schedule_info['caption'], account, accounts[account]['password'])
                            if success:
                                update_last_post_date(now)
                                print(f"投稿成功: {now} - アカウント: {account}")
                            else:
                                print(f"投稿失敗: {now} - アカウント: {account}")
    except Exception as e:
        error_message = f"スケジュール投稿でエラーが発生しました: {str(e)}\n{traceback.format_exc()}"
        print(error_message)

def run_schedule():
    while True:
        schedule_info = load_schedule()
        if schedule_info:
            start_time = datetime.datetime.strptime(schedule_info['start_time'], '%H:%M').time()
            end_time = datetime.datetime.strptime(schedule_info['end_time'], '%H:%M').time()
            
            now = datetime.datetime.now()
            
            if start_time <= now.time() <= end_time:
                schedule_post()
            
            # 次の確認までのスリープ時間を計算（1分～30分のランダムな時間）
            sleep_time = random.randint(60, 1800)
            time.sleep(sleep_time)
        else:
            time.sleep(60)  # スケジュールが設定されていない場合は1分後に再確認

@app.route('/')
def index():
    # アカウント情報、定型文、現在のスケジュールを取得してテンプレートに渡す
    accounts = get_accounts()
    presets = get_presets()
    schedule_info = load_schedule()
    return render_template('index.html', accounts=accounts, presets=presets, schedule=schedule_info)

@app.route('/upload', methods=['POST'])
def upload():
    # フォームからデータを取得
    accounts = request.form.getlist('account')
    caption = request.form['caption']
    
    video_path = get_random_video()
    if not video_path:
        return jsonify({'error': '指定されたディレクトリに動画ファイルが見つかりません'}), 400
    
    all_accounts = get_accounts()
    success_count = 0
    error_messages = []

    for account in accounts:
        if account not in all_accounts:
            error_messages.append(f'アカウント {account} が見つかりません')
            continue

        try:
            uploader = InstagramUploader()
            success = uploader.upload_to_instagram(video_path, caption, account, all_accounts[account]['password'])
            if success:
                success_count += 1
            else:
                error_messages.append(f'アカウント {account} への投稿に失敗しました')
        except Exception as e:
            error_message = f"アカウント {account} でエラーが発生しました: {str(e)}"
            print(error_message)
            print(traceback.format_exc())
            error_messages.append(error_message)

    if success_count == len(accounts):
        return jsonify({'message': f'全ての選択されたアカウント ({success_count}個) に動画をアップロードしました'}), 200
    elif success_count > 0:
        return jsonify({'message': f'{success_count}個のアカウントに動画をアップロードしました。エラー: {"; ".join(error_messages)}'}), 207
    else:
        return jsonify({'error': f'動画のアップロードに失敗しました。エラー: {"; ".join(error_messages)}'}), 500

@app.route('/add_account', methods=['POST'])
def add_account():
    # 新しいアカウントを追加
    username = request.form['username']
    password = request.form['password']
    save_account(username, password)
    return jsonify({'message': 'アカウントが追加されました'}), 200

@app.route('/add_preset', methods=['POST'])
def add_preset():
    # 新しい定型文を追加
    preset = request.form['preset']
    save_preset(preset)
    return jsonify({'message': '定型文が追加されました'}), 200

@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    # スケジュールを設定
    accounts = request.form.getlist('account')
    caption = request.form['caption']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    
    save_schedule(accounts, caption, start_time, end_time)
    
    return jsonify({'message': 'スケジュールが設定されました'}), 200

if __name__ == '__main__':
    # スケジュール実行用のスレッドを開始
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
    # Flaskアプリケーションを起動（ポート5001で実行）
    app.run(debug=True, port=5001)