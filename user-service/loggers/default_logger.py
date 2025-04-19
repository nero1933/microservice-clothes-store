import logging


default_logger = logging.getLogger('default_logger')
default_logger.setLevel(logging.INFO)
default_handler = logging.StreamHandler()
default_formatter = logging.Formatter('EXC:    * %(message)s')
default_handler.setFormatter(default_formatter)
default_logger.addHandler(default_handler)