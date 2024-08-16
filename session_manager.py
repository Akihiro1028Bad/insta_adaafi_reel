import os
import json
import time
from cryptography.fernet import Fernet
from logger import setup_logger

logger = setup_logger('session_manager', 'logs/session_manager.log')

class SessionManager:
    def __init__(self, session_dir='sessions'):
        """
        セッションマネージャーの初期化
        
        :param session_dir: セッション情報を保存するディレクトリ
        """
        self.session_dir = session_dir
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        logger.info(f"SessionManager initialized with session directory: {session_dir}")
        
        # 暗号化キーの設定
        key_file = os.path.join(session_dir, 'encryption_key.key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)
        self.cipher_suite = Fernet(self.key)
        logger.info("Encryption key set up successfully")

    def save_session(self, username, session_data):
        """
        セッション情報を暗号化して保存
        
        :param username: ユーザー名
        :param session_data: 保存するセッションデータ（辞書形式）
        """
        filename = os.path.join(self.session_dir, f"{username}.session")
        encrypted_data = self.cipher_suite.encrypt(json.dumps(session_data).encode())
        with open(filename, 'wb') as f:
            f.write(encrypted_data)
        logger.info(f"Session saved for user: {username}")

    def load_session(self, username):
        """
        保存されたセッション情報を読み込み、復号化
        
        :param username: ユーザー名
        :return: セッションデータ（辞書形式）、存在しない場合はNone
        """
        filename = os.path.join(self.session_dir, f"{username}.session")
        if not os.path.exists(filename):
            logger.info(f"No saved session found for user: {username}")
            return None
        
        with open(filename, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            session_data = json.loads(decrypted_data.decode())
            logger.info(f"Session loaded successfully for user: {username}")
            return session_data
        except Exception as e:
            logger.error(f"Error decrypting session data for user {username}: {str(e)}")
            return None

    def delete_session(self, username):
        """
        保存されたセッション情報を削除
        
        :param username: ユーザー名
        """
        filename = os.path.join(self.session_dir, f"{username}.session")
        if os.path.exists(filename):
            os.remove(filename)
            logger.info(f"Session deleted for user: {username}")
        else:
            logger.info(f"No session file found to delete for user: {username}")

    def is_session_valid(self, session_data):
        """
        セッションが有効かどうかを確認
        
        :param session_data: チェックするセッションデータ
        :return: 有効な場合はTrue、それ以外はFalse
        """
        if not session_data or 'expiry' not in session_data:
            return False
        
        current_time = time.time()
        if current_time > session_data['expiry']:
            logger.info("Session has expired")
            return False
        
        logger.info("Session is valid")
        return True

# セッションマネージャーのインスタンスを作成
session_manager = SessionManager()