import configparser
import os
import random
from logger import setup_logger

logger = setup_logger('config_manager', 'logs/config_manager.log')

class ConfigManager:
    def __init__(self, accounts_file, schedule_file):
        self.accounts_file = accounts_file
        self.schedule_file = schedule_file

    def get_random_video(self, video_folder):
        if not os.path.exists(video_folder):
            os.makedirs(video_folder)
        video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.mov', '.avi'))]
        if not video_files:
            logger.warning(f"No video files found in {video_folder}")
            return None
        random_video = random.choice(video_files)
        logger.info(f"Selected random video: {random_video}")
        return os.path.abspath(os.path.join(video_folder, random_video))

    def get_accounts(self):
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
        logger.info(f"Retrieved {len(accounts)} accounts")
        return accounts

    def get_account(self, username):
        accounts = self.get_accounts()
        account = accounts.get(username)
        if account:
            logger.info(f"Retrieved account info for: {username}")
        else:
            logger.warning(f"Account not found: {username}")
        return account

    def save_account(self, username, password, post_flag):
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        config[username] = {
            'password': password,
            'postflag': str(post_flag).lower()
        }
        with open(self.accounts_file, 'w') as configfile:
            config.write(configfile)
        logger.info(f"Saved new account: {username}")

    def update_account(self, username, data):
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        if username in config:
            if 'password' in data:
                config[username]['password'] = data['password']
            if 'postFlag' in data:
                config[username]['postflag'] = str(data['postFlag']).lower()
            with open(self.accounts_file, 'w') as configfile:
                config.write(configfile)
            logger.info(f"Updated account: {username}")
        else:
            logger.warning(f"Account not found for update: {username}")

    def delete_account(self, username):
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        if username in config:
            config.remove_section(username)
            with open(self.accounts_file, 'w') as configfile:
                config.write(configfile)
            logger.info(f"Deleted account: {username}")
        else:
            logger.warning(f"Account not found for deletion: {username}")

    def _update_account_file(self, username, account_data):
        config = configparser.ConfigParser()
        config.read(self.accounts_file)
        config[username] = account_data
        with open(self.accounts_file, 'w') as configfile:
            config.write(configfile)
        logger.info(f"Updated account file for: {username}")

    def load_schedule(self):
        config = configparser.ConfigParser()
        config.read(self.schedule_file)
        if 'Schedule' in config:
            schedule = dict(config['Schedule'])
            schedule['accounts'] = schedule['accounts'].split(',')
            schedule['posts'] = eval(schedule['posts'])
            logger.info("Schedule loaded successfully")
            return schedule
        logger.warning("No schedule found")
        return None

    def save_schedule(self, schedule_data):
        config = configparser.ConfigParser()
        config['Schedule'] = {
            'accounts': ','.join(schedule_data['accounts']),
            'caption': schedule_data['caption'],
            'posts': str(schedule_data['posts'])
        }
        with open(self.schedule_file, 'w') as configfile:
            config.write(configfile)
        logger.info("Schedule saved successfully")