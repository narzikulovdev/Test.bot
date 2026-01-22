import logging
import os


LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
LOG_FILE_PATH = os.path.join(os.getcwd(), 'logs', 'bot.log')


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': LOGGING_FORMAT
        },
    },
    'handlers': {
        'default': {
            'level': LOGGING_LEVEL,
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'mode': 'a',
            'encoding': 'utf-8',
        },
        'console': {
            'level': LOGGING_LEVEL,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'console'],
            'level': LOGGING_LEVEL,
            'propagate': True
        },
    }
}


