import logging

class ITAPIALogger:
    LEVEL_MAPPING = {
        'INFO': logging.INFO,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'DEBUG': logging.DEBUG,
        'FATAL': logging.FATAL
    }
    def __init__(self, id: str):
        self._logger: logging.Logger = self._init_logger(id)

    def _init_logger(self, id: str):
        
        _logger = logging.getLogger(id)
        _logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s by %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler ghi vào file
        # file_handler = logging.FileHandler(f'/app/logs/process_{datetime.now().strftime("%Y_%m_%d")}.log')
        # file_handler.setFormatter(formatter)

        # Handler ghi ra console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # _logger.addHandler(file_handler)
        _logger.addHandler(console_handler)
        
        return _logger
    
    def set_level(self, level: str):
        self._logger.setLevel(ITAPIALogger.LEVEL_MAPPING.get(level, logging.INFO))
    
    def info(self, msg: str):         
        self._logger.info(msg)
        
    def warn(self, msg: str):
        self._logger.warning(msg)
        
    def err(self, msg: str):
        self._logger.error(msg)
        
    def debug(self, msg: str):
        self._logger.debug(msg)
    
    