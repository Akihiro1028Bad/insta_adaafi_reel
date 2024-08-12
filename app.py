from flask import Flask, render_template, request, jsonify
from instagram_uploader import InstagramUploader
from scheduler import Scheduler
from config_manager import ConfigManager
from logger import setup_logger
from datetime import datetime, timedelta

app = Flask(__name__)

logger = setup_logger('app', 'logs/app.log')

VIDEO_FOLDER = 'upload_videos'
ACCOUNTS_FILE = 'accounts.ini'
SCHEDULE_FILE = 'schedule.json'

config_manager = ConfigManager(ACCOUNTS_FILE, SCHEDULE_FILE)
scheduler = Scheduler(config_manager, VIDEO_FOLDER)

@app.route('/')
def index():
    logger.info("メインページの表示リクエストを受信")
    accounts = config_manager.get_accounts()
    schedule_info = config_manager.load_schedule()
    auto_post_status = scheduler.get_status()
    next_post_times = scheduler.get_next_post_times()
    
    logger.debug(f"アカウント数: {len(accounts)}, 自動投稿状態: {auto_post_status}, 次回投稿時間: {next_post_times}")
    
    return render_template('index.html', 
                           accounts=accounts, 
                           schedule=schedule_info, 
                           auto_post_status=auto_post_status, 
                           next_post_times=next_post_times)

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

        video_paths = config_manager.get_random_videos(VIDEO_FOLDER, 3)
        if len(video_paths) < 3:
            error_message = f'アカウント {account} の投稿に失敗しました: 十分な数の動画ファイルが見つかりません'
            logger.error(error_message)
            error_messages.append(error_message)
            continue

        try:
            uploader = InstagramUploader()
            success = uploader.upload_to_instagram(video_paths, caption, account, all_accounts[account]['password'])
            if success:
                success_count += 1
                logger.info(f"アカウント {account} への3つの動画アップロードが成功しました")
            else:
                error_message = f'アカウント {account} への投稿に失敗しました'
                logger.error(error_message)
                error_messages.append(error_message)
        except Exception as e:
            error_message = f"アカウント {account} でエラーが発生しました: {str(e)}"
            logger.exception(error_message)
            error_messages.append(error_message)

    if success_count == len(accounts):
        message = f'全ての選択されたアカウント ({success_count}個) に3つずつ動画をアップロードしました'
        logger.info(message)
        return jsonify({'message': message}), 200
    elif success_count > 0:
        message = f'{success_count}個のアカウントに3つずつ動画をアップロードしました。エラー: {"; ".join(error_messages)}'
        logger.warning(message)
        return jsonify({'message': message}), 207
    else:
        message = f'動画のアップロードに失敗しました。エラー: {"; ".join(error_messages)}'
        logger.error(message)
        return jsonify({'error': message}), 500

# 他のルートやメソッドは変更なし
# 既存のルートの後に以下を追加
@app.route('/account_management')
def account_management():
    logger.info("アカウント管理ページの表示リクエストを受信")
    accounts = config_manager.get_accounts()
    return render_template('account_management.html', accounts=accounts)

# アカウント関連のAPIエンドポイントも追加
@app.route('/api/accounts', methods=['GET', 'POST'])
def api_accounts():
    if request.method == 'GET':
        accounts = config_manager.get_accounts()
        return jsonify([{"username": username, "postFlag": info['postFlag']} for username, info in accounts.items()])
    elif request.method == 'POST':
        data = request.json
        config_manager.save_account(data['username'], data['password'], data['postFlag'])
        return jsonify({"message": "アカウントが追加されました"})

@app.route('/api/accounts/<username>', methods=['PUT', 'DELETE'])
def api_account(username):
    if request.method == 'PUT':
        data = request.json
        config_manager.update_account(username, data)
        return jsonify({"message": "アカウントが更新されました"})
    elif request.method == 'DELETE':
        config_manager.delete_account(username)
        return jsonify({"message": "アカウントが削除されました"})
    
@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    data = request.json
    logger.info(f"受信したスケジュールデータ: {data}")  # 追加
    try:
        if 'post_times' not in data or 'accounts' not in data or 'caption' not in data:
            raise ValueError("必要なデータが不足しています")
        
        # 最大3つの投稿時間を受け付ける
        post_times = data['post_times'][:3]
        if not post_times:
            raise ValueError("少なくとも1つの投稿時間を指定してください")
        
        post_times = [datetime.strptime(t, '%H:%M').time() for t in post_times]
        
        schedule_data = {
            'post_times': post_times,
            'accounts': data['accounts'],
            'caption': data['caption']
        }
        
        logger.info(f"保存するスケジュールデータ: {schedule_data}")  # 追加
        config_manager.save_schedule(schedule_data)
        scheduler.update_schedule()
        return jsonify({"message": "スケジュールが設定されました"}), 200
    except ValueError as ve:
        logger.error(f"スケジュール設定中にバリデーションエラーが発生しました: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"スケジュール設定中にエラーが発生しました: {str(e)}")
        return jsonify({"error": "スケジュールの設定に失敗しました"}), 500

if __name__ == '__main__':
    logger.info("アプリケーションを起動します")
    scheduler.start()
    app.run(debug=True, port=5001)
    logger.info("アプリケーションを終了します")