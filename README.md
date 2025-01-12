# snote
A simple command line tool to search through text files for a pattern. By default, text files named 'notes.txt' located in ~/notes/ are searched through, but the filename and directory can be overriden by passing in arguments. Supports regular expressions for the pattern and globbing for the filename. Matches are presented with accompanying file paths, line numbers, and the line of text where the match was found.

Usage: 
  [python] snote 'pattern to search'
  [python] snote --filename '*.txt' 'pattern to search'
  [python] snote --searchpath ~/mysearchdirectory/ 'pattern to search'
