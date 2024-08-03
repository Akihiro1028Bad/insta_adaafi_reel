import threading
import time
from datetime import datetime, timedelta
from instagram_uploader import InstagramUploader
from logger import setup_logger

logger = setup_logger('scheduler', 'logs/scheduler.log')

class Scheduler:
    MIN_CHECK_INTERVAL = 30  # 最小チェック間隔（秒）
    MAX_CHECK_INTERVAL = 90  # 最大チェック間隔（秒）

    def __init__(self, config_manager, video_folder):
        self.config_manager = config_manager
        self.video_folder = video_folder
        self.running = False
        self.thread = None
        self.next_post_time = None
        logger.info("Schedulerが初期化されました")

    def get_status(self):
        status = "running" if self.running else "stopped"
        logger.info(f"現在のスケジューラーステータス: {status}")
        return status

    def get_next_post_time(self):
        if self.next_post_time:
            logger.info(f"次回の投稿時間: {self.next_post_time}")
            return self.next_post_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info("次回の投稿時間が設定されていません")
        return None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            logger.info("スケジューラーが開始されました")

    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logger.info("スケジューラーが停止されました")

    def update_schedule(self):
        logger.info("スケジュールの更新を開始")
        self.next_post_time = self.calculate_next_post_time()
        logger.info(f"次回の投稿時間を更新しました: {self.next_post_time}")

    def run(self):
        logger.info("スケジューラーのメインループを開始")
        while self.running:
            now = datetime.now()
            if self.next_post_time and now >= self.next_post_time:
                self.post_content()
                self.update_schedule()
            time.sleep(60)  # 1分ごとにチェック
        logger.info("スケジューラーのメインループを終了")

    def calculate_next_post_time(self):
        logger.info("次回の投稿時間を計算")
        schedule = self.config_manager.load_schedule()
        if not schedule:
            logger.warning("スケジュールが見つかりません")
            return None
        interval_minutes = schedule['interval']
        now = datetime.now()
        next_time = now + timedelta(minutes=interval_minutes)
        logger.info(f"次回の投稿時間を計算しました: {next_time}")
        return next_time

    def post_content(self):
        logger.info("コンテンツの投稿を開始")
        schedule = self.config_manager.load_schedule()
        if not schedule:
            logger.error("スケジュールが見つかりません")
            return

        for account in schedule['accounts']:
            logger.info(f"アカウント {account} の投稿処理を開始")
            video_path = self.config_manager.get_random_video(self.video_folder)
            if not video_path:
                logger.error(f"アカウント {account} の投稿に失敗しました: 動画ファイルが見つかりません")
                continue

            try:
                uploader = InstagramUploader()
                account_info = self.config_manager.get_account(account)
                if not account_info:
                    logger.error(f"アカウント {account} の情報が見つかりません")
                    continue
                success = uploader.upload_to_instagram(video_path, schedule['caption'], account, account_info['password'])
                if success:
                    logger.info(f"アカウント {account} への投稿が成功しました")
                    time.sleep(600)
                else:
                    logger.error(f"アカウント {account} への投稿に失敗しました")
            except Exception as e:
                logger.exception(f"アカウント {account} での投稿中にエラーが発生しました: {str(e)}")

        logger.info("全てのアカウントの投稿処理が完了しました")