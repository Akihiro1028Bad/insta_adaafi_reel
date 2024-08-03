import os
from flask import Flask, render_template, request, jsonify
from instagram_uploader import InstagramUploader
from scheduler import Scheduler
from config_manager import ConfigManager
from logger import setup_logger

app = Flask(__name__)

# ロガーのセットアップ
logger = setup_logger('app', 'logs/app.log')

# 定数の定義
VIDEO_FOLDER = os.path.abspath('upload_videos')
ACCOUNTS_FILE = 'accounts.ini'
SCHEDULE_FILE = 'schedule.ini'

config_manager = ConfigManager(ACCOUNTS_FILE, SCHEDULE_FILE)
scheduler = Scheduler(config_manager)

@app.route('/')
def index():
    logger.info("Rendering index page")
    accounts = config_manager.get_accounts()
    schedule_info = config_manager.load_schedule()
    return render_template('index.html', accounts=accounts, schedule=schedule_info)

@app.route('/upload', methods=['POST'])
def upload():
    logger.info("Received upload request")
    accounts = request.form.getlist('account')
    caption = request.form['caption']
    
    all_accounts = config_manager.get_accounts()
    success_count = 0
    error_messages = []

    for account in accounts:
        if account not in all_accounts:
            error_message = f'アカウント {account} が見つかりません'
            logger.error(error_message)
            error_messages.append(error_message)
            continue

        video_path = config_manager.get_random_video(VIDEO_FOLDER)
        if not video_path:
            error_message = f'アカウント {account} の投稿に失敗しました: 動画ファイルが見つかりません'
            logger.error(error_message)
            error_messages.append(error_message)
            continue

        try:
            uploader = InstagramUploader()
            success = uploader.upload_to_instagram(video_path, caption, account, all_accounts[account]['password'])
            if success:
                success_count += 1
                logger.info(f"Successfully uploaded video for account: {account}")
            else:
                error_message = f'アカウント {account} への投稿に失敗しました'
                logger.error(error_message)
                error_messages.append(error_message)
        except Exception as e:
            error_message = f"アカウント {account} でエラーが発生しました: {str(e)}"
            logger.exception(error_message)
            error_messages.append(error_message)

    if success_count == len(accounts):
        message = f'全ての選択されたアカウント ({success_count}個) に動画をアップロードしました'
        logger.info(message)
        return jsonify({'message': message}), 200
    elif success_count > 0:
        message = f'{success_count}個のアカウントに動画をアップロードしました。エラー: {"; ".join(error_messages)}'
        logger.warning(message)
        return jsonify({'message': message}), 207
    else:
        message = f'動画のアップロードに失敗しました。エラー: {"; ".join(error_messages)}'
        logger.error(message)
        return jsonify({'error': message}), 500

@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    logger.info("Received set_schedule request")
    schedule_data = request.json
    config_manager.save_schedule(schedule_data)
    scheduler.update_schedule()
    return jsonify({'message': 'スケジュールが設定されました'}), 200

@app.route('/add_account', methods=['POST'])
def add_account():
    logger.info("Received add_account request")
    username = request.form['username']
    password = request.form['password']
    config_manager.save_account(username, password)
    return jsonify({'message': 'アカウントが追加されました'}), 200

if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True, port=5001)