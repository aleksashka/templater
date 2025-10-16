import logging

from config import Config


class Log:
    """
    Logging wrapper that adds support for pre- and post-log lines

    This class wraps the standard Python logging interface and allows the use of
    special `b` (before) and `a` (after) keyword arguments to insert additional
    lines from a predefined dictionary (`Config.log_lines`) before
    and after the main log messages

    Usage:
        log = Log()
        log.warning("Main message", b=1, a=2)

    Output (assuming Config.log_lines = {1: "=" * 20, 2: "-" * 20}):
        WARNING: ====================
        WARNING: Main message
        WARNING: --------------------

    Supported log levels:
        - debug
        - info
        - warning
        - error
        - critical

    Positional arguments:
        *messages: Any number of strings to log as separate messages

    Keyword arguments:
        b (int, optional): Key for Config.log_lines to insert before messages
        a (int, optional): Key for Config.log_lines to insert after messages
    """

    def __init__(self):
        self.logger = logging.getLogger()

    def _log(
        self,
        level: str,
        *messages: str,
        b: int | None = None,
        a: int | None = None,
    ):
        """
        Internal method to log multiple messages at a given logging level, with
        optional pre- and post-log lines based on Config.log_lines

        Args:
            level (str): The logging level to use ('debug', 'info', 'warning', 'error', 'critical')

            *messages: One or more strings to be logged individually at the specified level

            b (int, optional): Key into Config.log_lines. If provided and found,
                the corresponding line will be logged before the messages

            a (int, optional): Key into Config.log_lines. If provided and found,
                the corresponding line will be logged after the messages

        Behavior:
            - Logs the "before" line (if `b` is provided and valid)
            - Logs each message in `*messages` separately at the given level
            - Logs the "after" line (if `a` is provided and valid)

        Raises:
            AttributeError: If the specified log level does not exist in the logger
        """
        log_func = getattr(self.logger, level, None)
        if not log_func:
            raise AttributeError(f"Invalid log level: {level}")

        if b is not None:
            before_msg = Config.log_lines.get(b)
            if before_msg:
                log_func(before_msg)

        for msg in messages:
            log_func(msg)

        if a is not None:
            after_msg = Config.log_lines.get(a)
            if after_msg:
                log_func(after_msg)

    def debug(self, *args, **kwargs):
        """
        Log debug-level messages with optional before/after lines

        Args:
            *args: Strings to log as separate messages
            b (int, optional): Key from Config.log_lines to insert before
            a (int, optional): Key from Config.log_lines to insert after
        """
        self._log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        """
        Log info-level messages with optional before/after lines

        Args:
            *args: Strings to log as separate messages
            b (int, optional): Key from Config.log_lines to insert before
            a (int, optional): Key from Config.log_lines to insert after
        """
        self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        """
        Log warning-level messages with optional before/after lines

        Args:
            *args: Strings to log as separate messages
            b (int, optional): Key from Config.log_lines to insert before
            a (int, optional): Key from Config.log_lines to insert after
        """
        self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        """
        Log error-level messages with optional before/after lines

        Args:
            *args: Strings to log as separate messages
            b (int, optional): Key from Config.log_lines to insert before
            a (int, optional): Key from Config.log_lines to insert after
        """
        self._log("error", *args, **kwargs)

    def critical(self, *args, **kwargs):
        """
        Log critical-level messages with optional before/after lines

        Args:
            *args: Strings to log as separate messages
            b (int, optional): Key from Config.log_lines to insert before
            a (int, optional): Key from Config.log_lines to insert after
        """
        self._log("critical", *args, **kwargs)
