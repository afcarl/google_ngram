# Author: Karl Stratos (karlstratos@gmail.com)
"""
This module is used to merge multiple gzipped n-gram files in a directory into a
single text file. In the process, it (a) accumulates n-gram counts over years
and (b) discards redundant counts caused by part-of-speech (POS) tags.

Argument 1: [directory of original gzipped n-gram files]
Argument 2: [output file]
"""
import os
import sys
import gzip

# POS tag types to ignore: pretend that any n-gram count containing any of these
# strings doesn't exist.
pos_tag_types = ("_NOUN", "_VERB", "_ADJ", "_ADV", "_PRON", "_DET", "_ADP",
                 "_NUM", "_CONJ", "_PRT", "_.", "_X")

def merge_files(ngram_directory, output_file):
    """
    Merges multiple gzipped n-gram files in the given directory into a single
    text file. In the process, it (a) accumulates n-gram counts over years
    and (b) discards redundant counts caused by part-of-speech (POS) tags.
    """
    with open(output_file, "w") as out:
        for file_name in os.listdir(ngram_directory):
            if len(file_name) > 11 and file_name[:11] == "googlebooks":
                file_path = os.path.join(ngram_directory, file_name)
                print "Processing gzipped file: {0}".format(file_path)
                with gzip.open(file_path, "rb") as gzipped_file:
                    # Keep track of which n-gram we're in and accumulate counts.
                    current_ngram = ""
                    current_ngram_count = 0
                    for byte_line in gzipped_file:
                        line = byte_line.decode("utf-8")

                        # chunks = [n-gram] [year] [n-gram count] [book count]
                        chunks = line.split("\t")

                        ngram = chunks[0]
                        ngram_count = int(chunks[2])

                        # First of all, check if this n-gram contains any POS
                        # tag and skip if it does.
                        contains_pos_tag = False
                        for token in ngram.split():
                            # If a token contains a POS tag, it has form either
                            # _[tag]_ or [word]_[tag]. So just check if _[tag]
                            # is present in the token.
                            for pos_tag_type in pos_tag_types:
                                if pos_tag_type in token:
                                    contains_pos_tag = True
                                    break
                            if contains_pos_tag:
                                break
                        if contains_pos_tag:  # Skip this n-gram completely.
                            continue

                        # At this point, we account for this n-gram.
                        if ngram != current_ngram:
                            # If this n-gram is different from the previous one,
                            # write the previous n-gram (if not empty) and its
                            # accumulated count and reset.
                            if current_ngram != "":
                                out.write(current_ngram + "\t" +
                                          str(current_ngram_count) + "\n")
                            current_ngram = ngram
                            current_ngram_count = ngram_count
                        else:
                            # If this n-gram is the same as the previous one,
                            # accumulate the count.
                            current_ngram_count += ngram_count

                    if current_ngram != "":  # End-of-the-file handling.
                        out.write(current_ngram + "\t" +
                                  str(current_ngram_count) + "\n")

if __name__ == "__main__":
    # Path to a directory of original gzipped n-gram files.
    NGRAM_DIRECTORY = sys.argv[1]

    # Path to an output text file of n-gram counts.
    OUTPUT_FILE = sys.argv[2]

    merge_files(NGRAM_DIRECTORY, OUTPUT_FILE)
