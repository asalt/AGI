import logging

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Set the minimum level of logs to capture

    # File handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Stream handler (console)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(file_format)
    logger.addHandler(stream_handler)

    return logger

from concurrent_log_handler import ConcurrentRotatingFileHandler

def get_logger_async(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Set up a specific handler to handle multi-process logging
    log_filename = 'app.log'
    rotate_handler = ConcurrentRotatingFileHandler(log_filename, "a", 512*1024, 5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    rotate_handler.setFormatter(formatter)
    logger.addHandler(rotate_handler)

    logger.propagate = False
    return logger
