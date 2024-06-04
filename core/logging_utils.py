import logging


def setup_logging(log_file="app.log"):
    """Sets up logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_logger(name):
    """Gets a logger with the specified name."""
    return logging.getLogger(name)
