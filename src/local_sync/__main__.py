import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .local_sync import main


def setup_logger(script_dir: Path):

    logger = logging.getLogger()

    log_path = script_dir / 'sync_log.txt'

    logger.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter('[%(asctime)s]%(name)s:%(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    shell_formatter = logging.Formatter('%(levelname)s: %(message)s')

    file_handler = RotatingFileHandler(log_path, maxBytes=5_242_880, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(shell_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

if __name__ == "__main__":

    if getattr(sys, 'frozen', False):
        script_dir = Path(sys.executable).parent
    else:
        script_dir = Path(__file__).parent.parent.parent.absolute()

    setup_logger(script_dir)

    try:
        main(script_dir)

    except Exception:
        logging.exception("The application crashed due to an unhandled exception:")
        sys.exit(1)
