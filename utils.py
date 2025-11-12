import logging
import argparse


class Log:
    """
    Logging wrapper that supports formatted headers based on predefined templates

    This class wraps a standard Python logger and provides an additional `h`
    parameter that controls header formatting using templates from `log_lines`.
    When specified, the first logged message is overlaid onto the header line
    pattern, producing a visually aligned log section

    Example:
        >>> log = Log(log_lines={1: "=" * 20, 2: "-" * 20})
        >>> log.debug("Header 1", h=1)
        ===== Header 1 =====
        >>> log.debug("Header 2", "Text 1", "Text 2", h=2)
        ----- Header 2 -----
        Text 1
        Text 2

     Supported log levels:
        - debug
        - info
        - warning
        - error
        - critical

    Args:
        *messages (str): Any number of strings to log as separate messages
        h (int, optional): Header template index used to format the first message
    """

    def __init__(self, log_lines: dict[int, str]):
        self.logger = logging.getLogger()
        self.log_lines = log_lines

    def create_header_line(
        self,
        message: str,
        h: int,
        shift: int = 5,
        sep: str = " ",
    ) -> str:
        """
        Build a formatted header line by overlaying the `message` onto a header
        line (selected based on `h` and `log_lines`), replacing part of it
        starting at the given `shift` position (adding `sep` before and after
        the `message`) and padding (if needed) to match the length of the
        original header line
        """
        header_line = self.log_lines.get(h, "")
        target_len = len(header_line)

        result = header_line[:shift] + sep + message + sep
        if len(result) >= target_len:
            return result

        padding = header_line[len(result) :]
        result += padding
        return result

    def _log(
        self,
        level: str,
        *messages: str,
        h: int | None = None,
    ):
        """
        Log one or more messages at the specified level with an optional header

        Args:
            level (str): Logging level name ("debug", "info", "warning",
                "error", "critical")
            *messages (str): One or more messages to be logged in order
            h (int): Optional header template index used to format the first
                message
        """
        log_func = getattr(self.logger, level, None)
        if not log_func:
            raise AttributeError(f"Invalid log level: {level}")

        if not messages and h is not None:
            log_func(self.log_lines.get(h, ""))
            return

        for i, message in enumerate(messages):
            if i == 0 and h is not None:
                log_func(self.create_header_line(message, h=h))
            else:
                log_func(message)

    def debug(self, *args, **kwargs):
        """
        Log debug-level messages with optional header formatting

        Args:
            *args (str): One or more messages to log
            h (int, optional): Header template index from `log_lines` for the
                first message

        """
        self._log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        """
        Log info-level messages with optional header formatting

        Args:
            *args (str): One or more messages to log
            h (int, optional): Header template index from `log_lines` for the
                first message
        """
        self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        """
        Log warning-level messages with optional header formatting

        Args:
            *args (str): One or more messages to log
            h (int, optional): Header template index from `log_lines` for the
                first message
        """
        self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        """
        Log error-level messages with optional header formatting

        Args:
            *args (str): One or more messages to log
            h (int, optional): Header template index from `log_lines` for the
                first message
        """
        self._log("error", *args, **kwargs)

    def critical(self, *args, **kwargs):
        """
        Log critical-level messages with optional header formatting

        Args:
            *args (str): One or more messages to log
            h (int, optional): Header template index from `log_lines` for the
                first message
        """
        self._log("critical", *args, **kwargs)


def make_parser(description: str) -> argparse.ArgumentParser:
    """
    Create a common argument parser with the provided description
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "project_name",
        nargs="?",
        default=None,
        help="Project name (default: demo)",
    )
    return parser
