import configparser
import os
import random
from datetime import datetime
from logger import setup_logger
import json

logger = setup_logger('config_manager', 'logs/config_manager.log')

class ConfigManager:
    def __init__(self, accounts_file, schedule_file):
        self.accounts_file = accounts_file
        self.schedule_file = schedule_file
        logger.info(f"ConfigManagerが初期化されました: accounts_file={accounts_file}, schedule_file={schedule_file}")

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

    def save_schedule(self, schedule_data):
        logger.info("新しいスケジュールの保存を開始")
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as file:
                json.dump({
                    'post_time': schedule_data['post_time'].strftime('%H:%M'),
                    'accounts': schedule_data['accounts'],
                    'caption': schedule_data['caption']
                }, file, ensure_ascii=False, indent=2)
            logger.info(f"新しいスケジュールを保存しました: 投稿時刻 {schedule_data['post_time']}, アカウント数 {len(schedule_data['accounts'])}")
        except Exception as e:
            logger.error(f"スケジュールの保存中にエラーが発生しました: {str(e)}")
            raise

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

    def load_schedule(self):
        logger.info("スケジュールの読み込みを開始")
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                schedule = {
                    'post_time': datetime.strptime(data['post_time'], '%H:%M').time(),
                    'accounts': data['accounts'],
                    'caption': data['caption']
                }
            logger.info(f"スケジュールを読み込みました: {schedule}")
            return schedule
        except FileNotFoundError:
            logger.warning("スケジュールファイルが見つかりません")
            return None
        except json.JSONDecodeError:
            logger.error("スケジュールファイルの形式が不正です")
            return None
        except Exception as e:
            logger.error(f"スケジュールの読み込み中にエラーが発生しました: {str(e)}")
            return None