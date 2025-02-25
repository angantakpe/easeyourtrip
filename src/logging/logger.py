import logging
import logging.handlers
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# function to provide configuration of logging
def logger_handle(path):
    logger = logging.getLogger(__name__)

    # check if log handle already exist in the progam if yes no need to follow configuration. Prevents multiple instance of same log.
    if len(logger.handlers) == 0:
        logger.setLevel(logging.DEBUG)
        # line will create a Roatating Log which gets appended untill the size limit defined is filled.
        # max log size can be 20mb
        path = os.path.join(path, "Log_" + str(datetime.now().date()) + ".log")
        handler = logging.handlers.RotatingFileHandler(path, mode='a', maxBytes=1024 * 1024 * 20, backupCount=2,
                                                       encoding=None, delay=0)
        handler.setLevel(logging.DEBUG)
        # setting a fixed format for the logs 
        formatter = logging.Formatter('{Log Time:%(asctime)s, Type:%(levelname)s, %(message)s}')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
            
    # return above mentioned log var with all configurations
    return logger

# function to generate log based on status and send the success status log  file
def success_log(status_code, message, function_name, request_id=None, path=None):
    l = logger_handle(os.getenv("LOGPATH"))
    message_final = "Message:" + message + ", Status Code: " + str(status_code) + ", Function Name: " + str(function_name)
    if request_id is not None:
        message_final = "Message:" + message + ", Status Code: " + str(status_code) + ", Function Name: " + str(function_name) + ", Request: " + str(request_id)    
    l.debug(message_final)

# function to generate log based on status and send fail status the log file
def error_log(status_code, message, function_name, request_id=None, path=None):
    l = logger_handle(os.getenv("LOGPATH"))
    message_final = "Message:" + message + ", Status Code: " + str(status_code) + ", Function Name: " + str(function_name)
    if request_id is not None:
        message_final = "Message:" + message + ", Status Code: " + str(status_code) + ", Function Name: " + str(function_name) + ", Request: " + str(request_id)
    l.debug(message_final)

# function to generate log based on status and send fail status the log file
def debug_log(message, function_name, request_id=None):
    l = logger_handle(os.getenv("LOGPATH"))
    message_final = "Message:" + message + ", Function Name: " + str(function_name)
    if request_id is not None:
        message_final = "Message:" + message + ", Function Name: " + str(function_name) + ", Request: " + str(request_id)
    l.debug(message_final)