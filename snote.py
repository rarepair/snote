#!/usr/bin/env python
import logging, util, os, re, signal, code
from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch
from natsort import os_sorted

this_script_path     = Path(__file__).resolve()
this_script_filename = this_script_path.name
work_dir_path        = Path("/Users/wtk/notes/").resolve()
srch_filename        = "notes.txt"

# List of directories to skip searching through. Entries must not end in "/" for the match to work. Supports globbing.
skip_dirs = [
    "*/54_Apple_Backup",
]

def sigint_handler(signum, frame):
    logger = logging.getLogger(name=this_script_filename)
    logger.critical("Received SIGINT. Exiting")
    exit()
signal.signal(signal.SIGINT, sigint_handler)

def parse_args():
    desc_str = ("Searches through plaintext files under /Users/notes/ named notes.txt for lines matching the provided pattern.\n\n")
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter, description=desc_str)
    parser.add_argument("pattern", type=str, help="The regular expression search pattern to match against within files")
    parser.add_argument("-f", "--filename", type=str, default=srch_filename, help="The filename pattern to match against. Supports globbing. (default=%(default)s)")
    parser.add_argument("-p", "--searchpath", type=str, default=work_dir_path, help="The path to recursively search through (default=%(default)s)")
    parser.add_argument("--debug", action="store_true", help="If specified, log messages at DEBUG level and higher will be printed to the console")
    return parser.parse_args()

if (__name__ == "__main__"):
    args = parse_args()
    util.init_logging(console_level=(logging.DEBUG if args.debug else logging.INFO))
    logger = logging.getLogger(name=this_script_filename)
    logger_verbatim = logging.getLogger(name="verbatim")

    # Compile the regex pattern
    try:
        pattern = re.compile(args.pattern)
    except Exception as err:
        logger.error("A %s exception was raised while trying to compile the provided pattern '%s'" % (type(err).__name__, args.pattern))
        exit(1)

    # Capture the current time in order to measure the total execution time of the search
    start_time = datetime.now()

    # Get a list of all the existing paths for filenames matching srch_filename
    srch_filelist = []
    for root, dirs, files in os.walk(args.searchpath):
        # Remove any directories that are match a pattern in skip_dirs so that they aren't traversed
        for i, dir in enumerate(dirs):
            for skip_dir in skip_dirs:
                if fnmatch(os.path.join(root, dir), skip_dir):
                    del dirs[i]

        # Iterate through the files in the current directory and append any that match args.filename
        for file in files:
            if fnmatch(file, args.filename):
                srch_filelist.append(os.path.join(root, file))
    logger.info("Found %d file(s) in search directory %s" % (len(srch_filelist), str(args.searchpath)))
    logger.debug("Contents of srch_filelist:\n%s" % (os.linesep.join([str(s) for s in srch_filelist])))

    # Search through each file for lines matching the provided pattern
    red   = util.term_colors["bold_red"]
    cyan  = util.term_colors["cyan"]
    green = util.term_colors["green"]
    off   = util.term_colors["off"]
    total_matched_lines = 0
    for file in srch_filelist:
        try:
            f = open(file, mode="r")
        except Exception as err:
            logger.error("A %s exception was raised while trying to open file '%s'. Continuing..." % (type(err).__name__, str(file)))
            continue

        # for Each file, build a list of (line_num,line) tuples with the matched text highlighted in red
        matched_lines = []
        with f:
            colourize_len = len(red) + len(off)

            # For each line in the file, check if the line has one or more matches and highlight the matching substring
            for line_num, line in enumerate(f):
                line_highlighted = line
                colourize_offset = 0

                # For each match in a line, insert ANSI colour sequences to highlight the matched substring and store in matched_lines
                for match in re.finditer(pattern, line):
                    span = match.span()
                    span_strt = span[0] + colourize_offset
                    span_stop = span[1] + colourize_offset
                    line_highlighted = line_highlighted[:span_strt] + red + line_highlighted[span_strt:span_stop] + off + line_highlighted[span_stop:]
                    colourize_offset += colourize_len
                    matched_lines.append((line_num + 1, line_highlighted.strip()))

        # If matches were found in the file, print the line number and (highlighted) line to the console
        num_matched_lines = len(matched_lines)
        if (num_matched_lines > 0):
            banner_msg = "Found %d matching line(s) in %s" % (num_matched_lines, str(file))
            logger_verbatim.info(cyan + util.generate_banner(msg=banner_msg, prefix="\n", suffix="") + off)
            for line_num, line in matched_lines:
                logger_verbatim.info(green + "%d" % line_num + off + ":\t%s" % line)
            total_matched_lines += num_matched_lines

    # Print a line with a summary of the search statistics
    run_time = datetime.now() - start_time
    if (total_matched_lines > 0): logger_verbatim.info("")
    logger.info("Completed search in %s and found %d total matching line(s) across %d file(s)" % (run_time, total_matched_lines, len(srch_filelist)))

    if args.debug:
        code.interact(banner="\n", local=locals()) # Enter interactive Python interpreter
