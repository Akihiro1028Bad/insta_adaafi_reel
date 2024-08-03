import threading
import time
import random
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

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            logger.info("Scheduler started")

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
            logger.info("Scheduler stopped")

    def update_schedule(self):
        if self.running:
            self.stop()
            self.start()
            logger.info("Schedule updated")

    def run(self):
        while self.running:
            schedule = self.config_manager.load_schedule()
            if schedule:
                now = datetime.now()
                for post in schedule['posts']:
                    start_time = datetime.strptime(post['start_time'], '%H:%M').time()
                    end_time = datetime.strptime(post['end_time'], '%H:%M').time()
                    
                    if start_time <= now.time() <= end_time:
                        post_time = self.get_random_time(start_time, end_time)
                        sleep_seconds = (datetime.combine(now.date(), post_time) - now).total_seconds()
                        
                        if sleep_seconds > 0:
                            logger.info(f"Sleeping for {sleep_seconds} seconds until next post")
                            time.sleep(sleep_seconds)
                        
                        self.make_post(schedule['accounts'], schedule['caption'])
                        break
            
            time.sleep(60)  # Check every minute

    def get_random_time(self, start_time, end_time):
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        random_minutes = random.randint(start_minutes, end_minutes)
        return (datetime.min + timedelta(minutes=random_minutes)).time()

    def make_post(self, accounts, caption):
        for account in accounts:
            account_info = self.config_manager.get_account(account)
            if account_info and account_info['postFlag']:
                video_path = self.config_manager.get_random_video(self.video_folder)
                if video_path:
                    try:
                        uploader = InstagramUploader()
                        success = uploader.upload_to_instagram(video_path, caption, account, account_info['password'])
                        if success:
                            logger.info(f"Scheduled post successful for account: {account}")
                        else:
                            logger.error(f"Scheduled post failed for account: {account}")
                    except Exception as e:
                        logger.exception(f"Error during scheduled post for account {account}: {str(e)}")
                else:
                    logger.error(f"No video found for scheduled post for account: {account}")
            else:
                logger.info(f"Skipping scheduled post for account {account} due to post flag being False")