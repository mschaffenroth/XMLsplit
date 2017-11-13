import logging
from logging import handlers
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class FunctionalLogger:
    def __init__(self):
        # create logger
        self._logger = logging.getLogger('logger')
        self._logger.setLevel(logging.INFO)

        # create console handler and set level to debug
        self._ch = logging.StreamHandler()
        self._ch.setLevel(logging.INFO)

        self.log_io = StringIO()
        self.streamhandler = logging.StreamHandler(self.log_io)
        self.memoryhandler = logging.handlers.MemoryHandler(1024 * 10, logging.ERROR, self.streamhandler)
        self.memoryhandler.setLevel(logging.WARN)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        self._ch.setFormatter(formatter)
        self.streamhandler.setFormatter(formatter)  # add ch to logger

        self._logger.addHandler(self._ch)
        self._logger.addHandler(self.memoryhandler)

    def get_log(self):
        self.memoryhandler.flush()
        return self.log_io.getvalue()

    def log(self, loglevel, str):
        # self.technical_log.append(str)
        self._logger.log(loglevel, str)


class TechnicalLogger:
    def __init__(self):
        # create logger
        self._logger = logging.getLogger('technical_logger')
        self._logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        self._ch = logging.StreamHandler()
        self._ch.setLevel(logging.DEBUG)
        self.technical_log_io = StringIO()
        self.streamhandler_technical = logging.StreamHandler(self.technical_log_io)
        self.memoryhandler = logging.handlers.MemoryHandler(1024 * 10, logging.DEBUG, self.streamhandler_technical)
        filehandler = logging.FileHandler("error.log", encoding="utf-8")

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        self._ch.setFormatter(formatter)
        self.streamhandler_technical.setFormatter(formatter)  # add ch to logger  # add ch to logger
        filehandler.setFormatter(formatter)

        self._logger.addHandler(self._ch)
        self._logger.addHandler(self.memoryhandler)
        self._logger.addHandler(filehandler)

    def get_log(self):
        self.memoryhandler.flush()
        return self.log_io.getvalue()

    def log(self, loglevel, str):
        # self.log.append(str)
        self._logger.log(loglevel, str)

class Logger:
    functional_logger = None
    technical_logger = None

    def __init__(self):
        pass

    @staticmethod
    def get_functional():
        if not Logger.functional_logger:
            Logger.functional_logger = FunctionalLogger()
        return Logger.functional_logger

    @staticmethod
    def get_technical():
        if not Logger.technical_logger:
            Logger.technical_logger = TechnicalLogger()
        return Logger.technical_logger

    @staticmethod
    def get_log():
        return Logger.get_functional().get_log()

    @staticmethod
    def get_technical_log():
        return Logger.get_technical().get_log()

    @staticmethod
    def log(loglevel, str):
        Logger.get_functional().log(loglevel, str)

    @staticmethod
    def debug(str):
        Logger.log(logging.DEBUG, str)

    @staticmethod
    def warning(str):
        Logger.log(logging.WARNING, str)

    @staticmethod
    def warn(str):
        Logger.log(logging.WARN, str)

    @staticmethod
    def info(str):
        Logger.log(logging.INFO, str)

    @staticmethod
    def error(str):
        Logger.log(logging.ERROR, str)

    @staticmethod
    def critical(str):
        Logger.log(logging.CRITICAL, str)

    @staticmethod
    def technical_debug(str):
        Logger.technical_log(logging.DEBUG, str)

    @staticmethod
    def technical_warning(str):
        Logger.technical_log(logging.WARNING, str)

    @staticmethod
    def technical_warn(str):
        Logger.technical_log(logging.WARN, str)

    @staticmethod
    def technical_info(str):
        Logger.technical_log(logging.INFO, str)

    @staticmethod
    def technical_error(str):
        Logger.technical_log(logging.ERROR, str)

    @staticmethod
    def technical_critical(str):
        Logger.technical_log(logging.CRITICAL, str)

    @staticmethod
    def technical_log(loglevel, str):
        Logger.get_technical().log(loglevel, str)
