import os
from flask import Flask, render_template, request, jsonify
from instagram_uploader import InstagramUploader
from scheduler import Scheduler
from config_manager import ConfigManager
from logger import setup_logger

# アプリケーションの初期化
app = Flask(__name__)

# ロガーのセットアップ
logger = setup_logger('app', 'logs/app.log')

# 定数の定義
VIDEO_FOLDER = os.path.abspath('upload_videos')
ACCOUNTS_FILE = 'accounts.ini'
SCHEDULE_FILE = 'schedule.ini'

# ConfigManagerとSchedulerのインスタンス化
config_manager = ConfigManager(ACCOUNTS_FILE, SCHEDULE_FILE)
scheduler = Scheduler(config_manager, VIDEO_FOLDER)

@app.route('/')
def index():
    logger.info("メインページの表示リクエストを受信")
    accounts = config_manager.get_accounts()
    schedule_info = config_manager.load_schedule()
    auto_post_status = scheduler.get_status()
    next_post_time = scheduler.get_next_post_time()
    
    logger.debug(f"アカウント数: {len(accounts)}, 自動投稿状態: {auto_post_status}, 次回投稿時間: {next_post_time}")
    
    return render_template('index.html', 
                           accounts=accounts, 
                           schedule=schedule_info, 
                           auto_post_status=auto_post_status, 
                           next_post_time=next_post_time)

@app.route('/account_management')
def account_management():
    logger.info("アカウント管理ページの表示リクエストを受信")
    return render_template('account_management.html')

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    logger.info("全アカウント情報の取得リクエストを受信")
    accounts = config_manager.get_accounts()
    logger.debug(f"取得したアカウント数: {len(accounts)}")
    return jsonify([{'username': username, 'postFlag': account['postFlag']} for username, account in accounts.items()])

@app.route('/api/accounts', methods=['POST'])
def add_account():
    logger.info("新規アカウント追加リクエストを受信")
    data = request.json
    username = data['username']
    password = data['password']
    post_flag = data['postFlag']
    
    try:
        config_manager.save_account(username, password, post_flag)
        logger.info(f"アカウント {username} を正常に追加しました")
        return jsonify({'message': 'アカウントが追加されました'}), 201
    except Exception as e:
        logger.error(f"アカウント {username} の追加中にエラーが発生しました: {str(e)}")
        return jsonify({'error': 'アカウントの追加に失敗しました'}), 500

@app.route('/api/accounts/<username>', methods=['PUT'])
def update_account(username):
    logger.info(f"アカウント {username} の更新リクエストを受信")
    data = request.json
    try:
        config_manager.update_account(username, data)
        logger.info(f"アカウント {username} を正常に更新しました")
        return jsonify({'message': 'アカウント情報が更新されました'}), 200
    except Exception as e:
        logger.error(f"アカウント {username} の更新中にエラーが発生しました: {str(e)}")
        return jsonify({'error': 'アカウントの更新に失敗しました'}), 500

@app.route('/api/accounts/<username>', methods=['DELETE'])
def delete_account(username):
    logger.info(f"アカウント {username} の削除リクエストを受信")
    try:
        config_manager.delete_account(username)
        logger.info(f"アカウント {username} を正常に削除しました")
        return jsonify({'message': 'アカウントが削除されました'}), 200
    except Exception as e:
        logger.error(f"アカウント {username} の削除中にエラーが発生しました: {str(e)}")
        return jsonify({'error': 'アカウントの削除に失敗しました'}), 500

@app.route('/upload', methods=['POST'])
def upload():
    logger.info("動画アップロードリクエストを受信")
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

        if not all_accounts[account]['postFlag']:
            logger.info(f"アカウント {account} は投稿フラグがFalseのためスキップします")
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
                logger.info(f"アカウント {account} への動画アップロードが成功しました")
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
    logger.info("スケジュール設定リクエストを受信")
    schedule_data = request.json
    interval = schedule_data.get('interval')
    
    if not 1 <= interval <= 600:
        error_message = '投稿間隔は1分から600分の間で設定してください。'
        logger.error(error_message)
        return jsonify({'error': error_message}), 400
    
    try:
        config_manager.save_schedule(schedule_data)
        scheduler.update_schedule()
        logger.info("スケジュールが正常に設定されました")
        return jsonify({'message': 'スケジュールが設定されました'}), 200
    except Exception as e:
        logger.error(f"スケジュール設定中にエラーが発生しました: {str(e)}")
        return jsonify({'error': 'スケジュールの設定に失敗しました'}), 500

@app.route('/api/auto_post_status', methods=['GET', 'POST'])
def auto_post_status():
    if request.method == 'GET':
        logger.info("自動投稿状態の取得リクエストを受信")
        status = scheduler.get_status()
        logger.debug(f"現在の自動投稿状態: {status}")
        return jsonify({'status': status}), 200
    elif request.method == 'POST':
        logger.info("自動投稿状態の変更リクエストを受信")
        new_status = request.json.get('status')
        if new_status not in ['start', 'stop']:
            logger.error(f"無効な状態が指定されました: {new_status}")
            return jsonify({'error': '無効な状態です。"start"または"stop"を指定してください。'}), 400
        try:
            if new_status == 'start':
                scheduler.start()
            else:
                scheduler.stop()
            logger.info(f"自動投稿状態を {new_status} に変更しました")
            return jsonify({'message': f'自動投稿を{new_status}しました', 'status': new_status}), 200
        except Exception as e:
            logger.error(f"自動投稿状態の変更中にエラーが発生しました: {str(e)}")
            return jsonify({'error': '自動投稿状態の変更に失敗しました'}), 500

@app.route('/api/next_post_time', methods=['GET'])
def next_post_time():
    logger.info("次回投稿時間の取得リクエストを受信")
    try:
        next_time = scheduler.get_next_post_time()
        logger.debug(f"次回の投稿時間: {next_time}")
        return jsonify({'next_post_time': next_time}), 200
    except Exception as e:
        logger.error(f"次回投稿時間の取得中にエラーが発生しました: {str(e)}")
        return jsonify({'error': '次回投稿時間の取得に失敗しました'}), 500

if __name__ == '__main__':
    logger.info("アプリケーションを起動します")
    scheduler.start()
    app.run(debug=True, port=5001)
    logger.info("アプリケーションを終了します")