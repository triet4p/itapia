import logging


class ITAPIALogger:
    """Custom logger implementation for ITAPIA applications."""

    LEVEL_MAPPING = {
        "INFO": logging.INFO,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "DEBUG": logging.DEBUG,
        "FATAL": logging.FATAL,
    }

    def __init__(self, id: str):
        """Initialize the logger with a specific ID.

        Args:
            id: Unique identifier for this logger instance
        """
        self._logger: logging.Logger = self._init_logger(id)

    def _init_logger(self, id: str) -> logging.Logger:
        """Initialize the underlying logger with formatting and handlers.

        Args:
            id: Logger identifier

        Returns:
            Configured logger instance
        """
        _logger = logging.getLogger(id)
        _logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s by %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler (commented out for now)
        # file_handler = logging.FileHandler(f'/app/logs/process_{datetime.now().strftime("%Y_%m_%d")}.log')
        # file_handler.setFormatter(formatter)

        # Console handler for output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # _logger.addHandler(file_handler)
        _logger.addHandler(console_handler)

        return _logger

    def set_level(self, level: str):
        """Set the logging level for this logger.

        Args:
            level: String representation of logging level (INFO, ERROR, WARNING, DEBUG, FATAL)
        """
        self._logger.setLevel(ITAPIALogger.LEVEL_MAPPING.get(level, logging.INFO))

    def info(self, msg: str):
        """Log an informational message.

        Args:
            msg: Message to log
        """
        self._logger.info(msg)

    def warn(self, msg: str):
        """Log a warning message.

        Args:
            msg: Message to log
        """
        self._logger.warning(msg)

    def err(self, msg: str):
        """Log an error message.

        Args:
            msg: Message to log
        """
        self._logger.error(msg)

    def debug(self, msg: str):
        """Log a debug message.

        Args:
            msg: Message to log
        """
        self._logger.debug(msg)
