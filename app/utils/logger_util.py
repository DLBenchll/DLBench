import logging
import os

_logger = None

def get_logger(log_path=None, to_console=True):
    global _logger
    if _logger is not None:
        return _logger

    if log_path is None:
        log_path = "./logs/default.log"

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger("dlbench_logger")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt='%(levelname)s %(asctime)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S'
    )

    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _logger = logger
    return _logger
