from logging import DEBUG, INFO, NOTSET, WARNING, Formatter, StreamHandler, root
from logging.handlers import WatchedFileHandler
from os import environ

from gitd.config import base_dir

def add_handler(level, handler, target = root):
    handler.setLevel(level)
    handler.setFormatter(Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', '%c'))
    target.addHandler(handler)

is_git = environ.get('GIT_DIR')

def setup_logging(log_dir):
    root.setLevel(NOTSET)

    add_handler(DEBUG, WatchedFileHandler(log_dir / 'verbose.log'))
    add_handler(INFO, WatchedFileHandler(log_dir / 'info.log'))
    add_handler(WARNING, WatchedFileHandler(log_dir / 'errors.log'))
    if not is_git:
        output_level = DEBUG if environ.get('ENV') == 'development' else INFO
        add_handler(output_level, StreamHandler())

setup_logging(base_dir / 'log' / ('git' if is_git else 'api'))
