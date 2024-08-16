import json
import os
import random
from datetime import datetime, time
from logger import setup_logger
import configparser
from cryptography.fernet import Fernet
from cryptography.fernet import Fernet, InvalidToken

logger = setup_logger('config_manager', 'logs/config_manager.log')

class ConfigManager:
    def __init__(self, accounts_file, schedule_file):
        self.accounts_file = accounts_file
        self.schedule_file = schedule_file
        logger.info(f"ConfigManagerが初期化されました: accounts_file={accounts_file}, schedule_file={schedule_file}")

        # 暗号化キーの設定
        key_file = 'config_encryption.key'
        self.key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(self.key)
        self.cipher_suite = Fernet(self.key)
        logger.info("新しい設定ファイル暗号化キーが生成されました")


    def get_random_videos(self, video_folder, count=3):
        """指定されたフォルダからランダムに指定された数の異なる動画を選択する"""
        if not os.path.exists(video_folder):
            os.makedirs(video_folder)
            logger.info(f"動画フォルダが存在しないため作成しました: {video_folder}")

        video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.mov', '.avi'))]
        if len(video_files) < count:
            logger.warning(f"フォルダ内の動画ファイルが{count}個未満です。利用可能な全ての動画を返します。")
            return [os.path.abspath(os.path.join(video_folder, f)) for f in video_files]

        selected_videos = random.sample(video_files, count)
        logger.info(f"{count}個の動画がランダムに選択されました: {', '.join(selected_videos)}")
        return [os.path.abspath(os.path.join(video_folder, f)) for f in selected_videos]

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
            try:
                decrypted_password = self._decrypt(account['password'])
            except InvalidToken:
                # 暗号化されていない場合、そのまま使用
                decrypted_password = account['password']
            accounts[section] = {
                'password': decrypted_password,
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
        """新しいアカウントを保存または既存のアカウントを更新"""
        logger.info(f"アカウント {username} の保存を開始")
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        
        if username not in config:
            config.add_section(username)
        
        config[username]['password'] = self._encrypt(password)
        config[username]['postflag'] = str(post_flag).lower()
        
        with open(self.accounts_file, 'w') as configfile:
            config.write(configfile)
        
        logger.info(f"アカウント {username} が正常に保存されました")

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
        """
        新しいスケジュール設定を保存する。
        
        :param schedule_data: 辞書形式のスケジュールデータ
        """
        logger.info("新しいスケジュールの保存を開始")
        try:
            encrypted_data = self._encrypt(json.dumps({
                'post_times': [time.strftime('%H:%M') for time in schedule_data['post_times']],
                'accounts': schedule_data['accounts'],
                'caption': schedule_data['caption']
            }))
            with open(self.schedule_file, 'wb') as file:
                file.write(encrypted_data)
            logger.info(f"新しいスケジュールを保存しました: 投稿時刻 {schedule_data['post_times']}, アカウント数 {len(schedule_data['accounts'])}")
        except Exception as e:
            logger.error(f"スケジュールの保存中にエラーが発生しました: {str(e)}")
            raise

    def load_schedule(self):
        """スケジュール設定を読み込む"""
        logger.info("スケジュールの読み込みを開始")
        try:
            if not os.path.exists(self.schedule_file):
                logger.warning("スケジュールファイルが見つかりません")
                return None

            with open(self.schedule_file, 'rb') as file:
                encrypted_data = file.read()

            decrypted_data = self._decrypt(encrypted_data)
            data = json.loads(decrypted_data)
            schedule = {
                'post_times': [datetime.strptime(t, '%H:%M').time() for t in data['post_times']],
                'accounts': data['accounts'],
                'caption': data['caption']
            }
            logger.info(f"スケジュールを読み込みました: {schedule}")
            return schedule
        except json.JSONDecodeError:
            logger.error("スケジュールファイルの形式が不正です")
            return None
        except Exception as e:
            logger.error(f"スケジュールの読み込み中にエラーが発生しました: {str(e)}")
            return None
        
    def get_random_wait_time(self):
        """1分から60分の間でランダムな待機時間（秒）を生成する"""
        wait_time = random.randint(60, 3600)  # 60秒（1分）から3600秒（60分）の間
        logger.info(f"ランダムな待機時間を生成しました: {wait_time}秒")
        return wait_time

    def _encrypt(self, data):
        """データを暗号化する"""
        return self.cipher_suite.encrypt(data.encode())

    def _decrypt(self, encrypted_data):
        """暗号化されたデータを復号化する"""
        return self.cipher_suite.decrypt(encrypted_data).decode()

# ConfigManagerのインスタンスを作成
config_manager = ConfigManager('accounts.ini', 'schedule.json')