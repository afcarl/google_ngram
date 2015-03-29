# Author: Karl Stratos (karlstratos@gmail.com)
"""
This *Python version 2* module is used to collect all file URLs that match
the given regex pattern. It outputs a list of such URLs, which can be fed to
wget -i to initiate a single-pass download process. This is a Python 2 script
because the library mechanize does not support Python 3.

Argument 1: [regex]
Argument 2: [output file of URLs]

The regex expression must respect the Python format. For example, to get a list
of all 5-gram files for English (2012 version), use:

googlebooks-eng-all-5gram-20120701-\(.*\).gz
"""
import os
import sys
import re
import mechanize

# The URL where the Google Ngram data can be found (as of 1/3/2015).
GOOGLE_NGRAM_SITE = \
"http://storage.googleapis.com/books/ngrams/books/datasetsv2.html"

def collect_file_urls(regex_string, output_urls_file):
    """
    Collects file URLs from the Google Ngram site that match the given regex
    pattern, then output a list of these URLs as a file.
    """
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.open(GOOGLE_NGRAM_SITE)
    regex = re.compile(regex_string)

    num_files = 0
    with open(output_urls_file, "w") as output:
        for link in browser.links():
            file_url = os.path.basename(link.url)
            if regex.match(file_url):
                num_files += 1
                output.write(link.url+"\n")
    print("Found {0} files that matched: {1}".format(num_files, regex_string))

if __name__ == "__main__":
    # Path to a regex string.
    REGEX_STRING = sys.argv[1]

    # Path to an output file of URLs.
    OUTPUT_URLS_FILE = sys.argv[2]

    collect_file_urls(REGEX_STRING, OUTPUT_URLS_FILE)
