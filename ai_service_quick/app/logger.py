import logging

_logger: logging.Logger = None

def _init_logger():
    global _logger
    
    _logger = logging.getLogger('AI Service Quick')
    _logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
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
    
def info(msg: str):
    global _logger
    if _logger is None:
        _init_logger()
        
    _logger.info(msg)
    
def warn(msg: str):
    global _logger
    if _logger is None:
        _init_logger()
    
    _logger.warning(msg)
    
def err(msg: str):
    global _logger
    if _logger is None:
        _init_logger()
    
    _logger.error(msg)