import logging
import os

def setup_logger(name, log_file, level=logging.INFO):
    # ログディレクトリが存在しない場合は作成
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # フォーマッターの設定
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')

    # ファイルハンドラーの設定
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # ロガーの設定
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"ロガー '{name}' がセットアップされました。ログファイル: {log_file}")

    return logger

def set_log_level(logger, level):
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    if level.upper() in level_map:
        logger.setLevel(level_map[level.upper()])
        logger.info(f"ログレベルを {level.upper()} に設定しました")
    else:
        logger.warning(f"無効なログレベル: {level}。ログレベルは変更されません。")