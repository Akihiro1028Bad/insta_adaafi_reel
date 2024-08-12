import threading
import time
from datetime import datetime, timedelta
from instagram_uploader import InstagramUploader
from logger import setup_logger

logger = setup_logger('scheduler', 'logs/scheduler.log')

class Scheduler:
    def __init__(self, config_manager, video_folder):
        self.config_manager = config_manager
        self.video_folder = video_folder
        self.running = False
        self.thread = None
        self.next_post_times = []
        logger.info("スケジューラーが初期化されました")


    def get_status(self):
        status = "running" if self.running else "stopped"
        logger.info(f"現在のスケジューラーステータス: {status}")
        return status

    def get_next_post_times(self):
        if self.next_post_times:
            times_str = ", ".join(t.strftime("%Y-%m-%d %H:%M:%S") for t in self.next_post_times)
            logger.info(f"次回の投稿時間: {times_str}")
            return times_str
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
        self.next_post_times = self.calculate_next_post_times()
        logger.info(f"次回の投稿時間を更新しました: {self.next_post_times}")

    def run(self):
        logger.info("スケジューラーのメインループを開始")
        while self.running:
            now = datetime.now()
            for post_time in self.next_post_times:
                if now >= post_time:
                    wait_time = self.config_manager.get_random_wait_time()
                    logger.info(f"投稿時刻 {post_time} に達しました。{wait_time}秒後に投稿を開始します。")
                    time.sleep(wait_time)
                    self.post_content()
                    self.update_schedule()
                    break
            time.sleep(60)  # 1分ごとにチェック
        logger.info("スケジューラーのメインループを終了")

    def calculate_next_post_times(self):
        logger.info("次回の投稿時間を計算")
        schedule = self.config_manager.load_schedule()
        if not schedule:
            logger.warning("スケジュールが見つかりません")
            return []
        
        now = datetime.now()
        next_times = []
        for post_time in schedule['post_times']:
            next_time = now.replace(hour=post_time.hour, minute=post_time.minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            next_times.append(next_time)
        
        next_times.sort()
        logger.info(f"次回の投稿時間を計算しました: {next_times}")
        return next_times
    
    def post_content(self):
        logger.info("スケジュールされたコンテンツの投稿を開始")
        schedule = self.config_manager.load_schedule()
        if not schedule:
            logger.error("スケジュールが見つかりません")
            return

        for account in schedule['accounts']:
            logger.info(f"アカウント {account} の投稿処理を開始")
            video_paths = self.config_manager.get_random_videos(self.video_folder, 3)
            if len(video_paths) < 3:
                logger.error(f"アカウント {account} の投稿に失敗しました: 十分な数の動画ファイルが見つかりません")
                continue

            try:
                uploader = InstagramUploader()
                account_info = self.config_manager.get_account(account)
                if not account_info:
                    logger.error(f"アカウント {account} の情報が見つかりません")
                    continue
                success = uploader.upload_to_instagram(video_paths, schedule['caption'], account, account_info['password'])
                if success:
                    logger.info(f"アカウント {account} への3つの動画投稿が成功しました")
                else:
                    logger.error(f"アカウント {account} への投稿に失敗しました")
            except Exception as e:
                logger.exception(f"アカウント {account} での投稿中にエラーが発生しました: {str(e)}")

        logger.info("全てのアカウントの投稿処理が完了しました")