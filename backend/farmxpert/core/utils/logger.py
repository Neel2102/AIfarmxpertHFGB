import logging
import structlog
from farmxpert.config.settings import settings


def _configure_structlog() -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "farmxpert") -> structlog.stdlib.BoundLogger:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    _configure_structlog()
    return structlog.get_logger(name)


