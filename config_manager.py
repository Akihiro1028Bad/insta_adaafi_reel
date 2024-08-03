import configparser
import os
import random
from logger import setup_logger

logger = setup_logger('config_manager', 'logs/config_manager.log')

class ConfigManager:
    def __init__(self, accounts_file, schedule_file):
        self.accounts_file = accounts_file
        self.schedule_file = schedule_file
        logger.info(f"ConfigManagerが初期化されました: accounts_file={accounts_file}, schedule_file={schedule_file}")

    def get_random_video(self, video_folder):
        if not os.path.exists(video_folder):
            os.makedirs(video_folder)
            logger.info(f"動画フォルダが存在しないため作成しました: {video_folder}")

        video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.mov', '.avi'))]
        if not video_files:
            logger.warning(f"動画ファイルが見つかりません: {video_folder}")
            return None

        random_video = random.choice(video_files)
        logger.info(f"ランダムに選択された動画: {random_video}")
        return os.path.abspath(os.path.join(video_folder, random_video))

    def get_accounts(self):
        logger.info("全アカウント情報の取得を開始")
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        accounts = {}
        for section in config.sections():
            account = dict(config[section])
            if 'postflag' not in account:
                account['postflag'] = 'true'
                self._update_account_file(section, account)
            accounts[section] = {
                'password': account['password'],
                'postFlag': account['postflag'].lower() == 'true'
            }
        logger.info(f"{len(accounts)}個のアカウント情報を取得しました")
        return accounts

    def get_account(self, username):
        logger.info(f"アカウント {username} の情報取得を開始")
        accounts = self.get_accounts()
        account = accounts.get(username)
        if account:
            logger.info(f"アカウント情報を取得しました: {username}")
        else:
            logger.warning(f"アカウントが見つかりません: {username}")
        return account

    def save_account(self, username, password, post_flag):
        logger.info(f"新しいアカウント {username} の保存を開始")
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        config[username] = {
            'password': password,
            'postflag': str(post_flag).lower()
        }
        with open(self.accounts_file, 'w') as configfile:
            config.write(configfile)
        logger.info(f"新しいアカウントを保存しました: {username}")

    def update_account(self, username, data):
        logger.info(f"アカウント {username} の更新を開始")
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        if username in config:
            if 'password' in data:
                config[username]['password'] = data['password']
            if 'postFlag' in data:
                config[username]['postflag'] = str(data['postFlag']).lower()
            with open(self.accounts_file, 'w') as configfile:
                config.write(configfile)
            logger.info(f"アカウント情報を更新しました: {username}")
        else:
            logger.warning(f"更新対象のアカウントが見つかりません: {username}")

    def delete_account(self, username):
        logger.info(f"アカウント {username} の削除を開始")
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        if username in config:
            config.remove_section(username)
            with open(self.accounts_file, 'w') as configfile:
                config.write(configfile)
            logger.info(f"アカウントを削除しました: {username}")
        else:
            logger.warning(f"削除対象のアカウントが見つかりません: {username}")

    def _update_account_file(self, username, account_data):
        logger.info(f"アカウント {username} のファイル更新を開始")
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        config[username] = account_data
        with open(self.accounts_file, 'w') as configfile:
            config.write(configfile)
        logger.info(f"アカウントファイルを更新しました: {username}")

    def save_schedule(self, schedule_data):
        logger.info("新しいスケジュールの保存を開始")
        config = configparser.ConfigParser()
        config['Schedule'] = {
            'interval': str(schedule_data['interval']),
            'accounts': ','.join(schedule_data['accounts']),
            'caption': schedule_data['caption']
        }
        with open(self.schedule_file, 'w') as configfile:
            config.write(configfile)
        logger.info("新しいスケジュールを保存しました")

    def load_schedule(self):
        logger.info("スケジュールの読み込みを開始")
        config = configparser.ConfigParser()
        config.read(self.schedule_file)
        if 'Schedule' in config:
            schedule = {
                'interval': config.getint('Schedule', 'interval'),
                'accounts': config.get('Schedule', 'accounts').split(','),
                'caption': config.get('Schedule', 'caption')
            }
            logger.info(f"スケジュールを読み込みました: {schedule}")
            return schedule
        logger.warning("スケジュールが見つかりません")
        return None