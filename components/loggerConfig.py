# this file shall do the basic logging configuration.
import logging
import sys

def loggerConfig() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s : %(name)s  : %(funcName)s : %(levelname)s : %(message)s',
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("Logger configured")