import logging, os, datetime, math, shutil
from colorama import just_fix_windows_console

term_colors = {
    "off":     "\033[0m"    ,
    "black":   "\033[30;21m", "bold_black":   "\033[30;1m",
    "red":     "\033[31;21m", "bold_red":     "\033[31;1m",
    "green":   "\033[32;21m", "bold_green":   "\033[32;1m",
    "yellow":  "\033[33;21m", "bold_yellow":  "\033[33;1m",
    "blue":    "\033[34;21m", "bold_blue":    "\033[34;1m",
    "magenta": "\033[35;21m", "bold_magenta": "\033[35;1m",
    "cyan":    "\033[36;21m", "bold_cyan":    "\033[36;1m",
    "white":   "\033[37;21m", "bold_white":   "\033[37;1m",
}

# This SixLevelLogger class replaces the default one to add an additional logging level, TRACE. The replacement occurs during module importing
# so that it happens before any logging calls are made.
logging.TRACE = 5
class SixLevelLogger(logging.getLoggerClass()):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        logging.addLevelName(logging.TRACE, "TRACE")

    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.TRACE):
            self._log(logging.TRACE, msg, args, **kwargs)
logging.setLoggerClass(SixLevelLogger)

class LogFormatter(logging.Formatter):
    def __init__(self, en_colors=False, en_bracket=True, en_timestamps=False, en_filenames=False, en_linenums=False):
        self.pre_bracket_template  = ("{asctime} "   if en_timestamps else "")

        def get_bracket_str(level):
            if not en_bracket: return ""
            level_color_map = {
                logging.TRACE:    term_colors["magenta"],
                logging.DEBUG:    term_colors["cyan"],
                logging.INFO:     "",
                logging.WARNING:  term_colors["yellow"],
                logging.ERROR:    term_colors["red"],
                logging.CRITICAL: term_colors["bold_red"],
            }
            if en_colors:
                return "[{name:>15.15} " + level_color_map[level] + "{levelname:3.3}" + term_colors["off"] + "]: "
            else:
                return "[{name:>15.15} {levelname:3.3}]: "

        self.post_bracket_template = ("{message}"                            ) + \
                                     (" ({filename}" if en_filenames  else "") + \
                                     (":{lineno}"    if en_linenums   else "") + \
                                     (")"            if en_filenames  else "")

        self.regular_formats = {
            logging.TRACE:    self.pre_bracket_template + get_bracket_str(logging.TRACE)    + self.post_bracket_template,
            logging.DEBUG:    self.pre_bracket_template + get_bracket_str(logging.DEBUG)    + self.post_bracket_template,
            logging.INFO:     self.pre_bracket_template + get_bracket_str(logging.INFO)     + self.post_bracket_template,
            logging.WARNING:  self.pre_bracket_template + get_bracket_str(logging.WARNING)  + self.post_bracket_template,
            logging.ERROR:    self.pre_bracket_template + get_bracket_str(logging.ERROR)    + self.post_bracket_template,
            logging.CRITICAL: self.pre_bracket_template + get_bracket_str(logging.CRITICAL) + self.post_bracket_template,
        }

        self.verbatim_colored_formats = {
            logging.TRACE:    (term_colors["magenta"]  if en_colors else "") + "{message}" + (term_colors["off"] if en_colors else ""),
            logging.DEBUG:    "{message}",
            logging.INFO:     (term_colors["green"]    if en_colors else "") + "{message}" + (term_colors["off"] if en_colors else ""),
            logging.WARNING:  (term_colors["yellow"]   if en_colors else "") + "{message}" + (term_colors["off"] if en_colors else ""),
            logging.ERROR:    (term_colors["red"]      if en_colors else "") + "{message}" + (term_colors["off"] if en_colors else ""),
            logging.CRITICAL: (term_colors["bold_red"] if en_colors else "") + "{message}" + (term_colors["off"] if en_colors else ""),
        }

    def format(self, record):
        if (record.name == "verbatim"):
            # If the special 'verbatim' logger is used, it will emit a message as-is with no format modifications
            return logging.Formatter("{message}", style="{").format(record)
        elif (record.name == "verbatim_colored"):
            # If the special 'verbatim_colored' logger is used, it will emit a message whose only format modifcation is the text color
            # which is set depending on severity level.
            return logging.Formatter(self.verbatim_colored_formats[record.levelno], style="{").format(record)
        else:
            return logging.Formatter(self.regular_formats[record.levelno], style="{").format(record)

# This function is intended to be called before any messages have been logged. It sets up the root logger and creates two handlers,
# one for the console, and one for the log file that the test run will record to.
def init_logging(console_level=logging.INFO, logfile=False, logfile_level=logging.DEBUG, logfile_dir=None, logfile_name=None):
    # Configure the root logger to record all messages.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.TRACE)

    # Add log handler to emit messages to the given logfile.
    if (logfile):
        if not logfile_name: logfile_name = "snote_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
        if logfile_dir:
            logfile_full_path = os.path.join(logfile_dir, logfile_name)
        else:
            logfile_full_path = os.path.join(os.path.abspath(os.getcwd()), logfile_name)
        logfile_handler = logging.FileHandler(filename=logfile_full_path, mode="w")
        logfile_handler.setLevel(logfile_level)
        logfile_handler.setFormatter(LogFormatter(en_colors=False, en_timestamps=True, en_filenames=True, en_linenums=True))
        root_logger.addHandler(logfile_handler)

    # Add log handler to emit messages to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(LogFormatter(en_colors=True, en_timestamps=False, en_filenames=False, en_linenums=False))
    root_logger.addHandler(console_handler)

# Generates a 'banner', which is a string composed of repeated separator characters with text centered in the middle. The width of
# the banner is equal to the current terminal width. Example:
# <prefix> ========= <msg> ========= <suffix>
def generate_banner(msg, separator="=", prefix="\n", suffix="\n"):
    term_width, _ = shutil.get_terminal_size(fallback=(80, 24)) # Capture the width of the current terminal
    if not msg:
        return prefix + (separator * term_width) + suffix
    else:
        sep_len = (term_width - len(msg) - 2) / 2.0
        return prefix + separator * math.floor(sep_len) + " " + msg + " " + separator * math.ceil(sep_len) + suffix

# Return a string with some body text between header and footer 'banners'. The header and footer text are centered in the line with
# a given separator character filling the space on either side. It's use to clearly delineate the trigger action output in the stdout.
# Example:
# <prefix> ========= <header> ========= <suffix>
#                     <body>
# <prefix> ========= <footer> ========= <suffix>
def wrap_with_banners(header="", body="", footer="", separator="=", prefix="\n", suffix="\n"):
    banners = ["", ""]
    for i, hdr_ftr in enumerate([header, footer]):
        banners[i] = generate_banner(msg=hdr_ftr, separator=separator, prefix=prefix, suffix=suffix)
    return banners[0] + body + banners[1]
