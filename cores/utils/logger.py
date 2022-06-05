import logging


def setup_logger(name, formatter, log_file, level=logging.INFO):
    """
    Set up a logger
    :param name: str, name of the logger
    :param formatter: format of the logger
    :param log_file:
    :param level:
    :return:
    """
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def clear_logger(log_handle):
    """
    Clear a logger

    :param log_handle:
    :return: None
    """
    logging.shutdown(log_handle)


# global variable for map logger
map_logger = None
map_logger_formatter = \
    logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)s'
                      ' - %(funcName)s] -- %(message)s')



