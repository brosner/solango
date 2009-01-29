#
# Copyright 2008 Optaros, Inc.
#

"""
This module provides unified logging via the logging module.
"""
import logging
import settings

class LogManager:
    """
    A helper class which instantiates and configures the default Logger.
    """
    def __init__(self):
        """
        Instantiate the default logger.
        """
        self.logger = logging.getLogger(globals()['__name__'])
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        formatter = logging.Formatter(settings.LOG_FORMAT)
        
        file_handler = logging.FileHandler(settings.LOG_FILENAME)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def get_levels(self):
        """
        Returns a dictionary associating names to logging levels.
        """
        return {
            'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING,
            'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL
        }

log_manager = LogManager()
logger = log_manager.logger