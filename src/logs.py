from datetime import datetime
import logging
from typing import Optional


def configure_log(
		log_name: str = "main",
		log_file_name: Optional[str] = None,
		log_file_encoding: str = "utf-8",
		log_format: str = "%(asctime)s %(levelname)s [%(name)s] %(message)s"):
	log_formatter = logging.Formatter(log_format)

	log = logging.getLogger(log_name)
	log.setLevel(logging.DEBUG)

	console_handler = logging.StreamHandler()
	console_handler.setFormatter(log_formatter)
	console_handler.setLevel(logging.INFO)
	log.addHandler(console_handler)

	if log_file_name is None:
		log_file_name = datetime.today().strftime('%Y-%m-%d') + ".log"
	file_handler = logging.FileHandler(log_file_name, encoding = log_file_encoding)
	file_handler.setFormatter(log_formatter)
	file_handler.setLevel(logging.DEBUG)
	log.addHandler(file_handler)
	
	return log
