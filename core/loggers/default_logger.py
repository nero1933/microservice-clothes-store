import logging


class CustomFormatter(logging.Formatter):
	def format(self, record):
		level_name = record.levelname.upper() + ':·'
		level_name = level_name.ljust(10)
		log_message = super().format(record)
		return f"{level_name}{log_message}"


log = logging.getLogger('default_logger')
log.setLevel(logging.INFO)
default_handler = logging.StreamHandler()
custom_formatter = CustomFormatter('%(message)s')
default_handler.setFormatter(custom_formatter)
log.addHandler(default_handler)
