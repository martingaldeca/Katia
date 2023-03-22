import logging.config
import os

import yaml


def setup_logger():
    """
    This will be the method in charge of set up the logging configuration for the project.
    :return:
    """
    with open(
        f"{os.path.dirname(__file__)}/log_config.yaml", "r", encoding="utf8"
    ) as config_file:
        config = yaml.safe_load(config_file.read())
        logging.config.dictConfig(config)
