# Author: Karl Stratos (karlstratos@gmail.com)
"""
This module is used to create an output directory for word representations. The
directory will contain statistics required for computing word representations.
"""
import argparse
from collections import Counter
import os
import shutil
import sys

output_path = None # Global output directory path.
logf = None  # Global log file.
RARE_SYMBOL = "<?>"  # Representation for rare word types.

def extract_sorted_word_types(unigram_path):
    """Extracts a sorted list of count-word pairs."""
    assert(os.path.exists(unigram_path))

    # Read count-unigram pairs.
    wordcounts = []
    with open(unigram_path, "r") as unigram_file:
        for line in unigram_file:
            toks = line.split()
            if len(toks) != 2:
                print("Skipping a faulty line: ", line[:-1])
                continue
            word = toks[0]
            assert(word != RARE_SYMBOL)
            count = int(toks[1])
            wordcounts.append((count, word))

    # Sort count-unigram pairs.
    print("Sorting {0} word types...".format(len(wordcounts)))
    wordcounts.sort(reverse=True)
    num_words = 0
    with open(os.path.join(output_path, "sorted_word_types"), "w") as out_file:
        for (count, word) in wordcounts:
            num_words += count
            out_file.write(word + " " + str(count) + "\n")

    # Return sorted count-unigram pairs.
    return wordcounts

def create_vocab(sorted_wordcounts, rare_cutoff):
    """Create a vocabulary of non-rare word types based on the cutoff value."""
    rare = {}
    vocab = {}
    rare_file_name = "rare_words_rare" + str(rare_cutoff)
    num_words = 0
    num_rare = 0
    with open(os.path.join(output_path, rare_file_name), "w") as rare_file:
        for (count, word) in sorted_wordcounts:
            num_words += count
            if count <= rare_cutoff:
                rare[word] = True
                num_rare += count
                rare_file.write(word + " " + str(count) + "\n")
            else:
                vocab[word] = True


    print("{0} / {1} word types rare (cutoff <= {2})".format(
            len(rare), len(sorted_wordcounts), rare_cutoff))
    reduced_vocab_size = len(sorted_wordcounts) if len(rare) == 0 else \
        len(sorted_wordcounts) - len(rare) + 1
    logf.write("[Corpus]\n")
    logf.write("   {0} unigram counts\n".format(num_words))
    logf.write("   Cutoff {0}: {1} => {2} word types\n".format(
            rare_cutoff, len(sorted_wordcounts), reduced_vocab_size))
    logf.write("   Preserved word types: {0:.2f}% unigram mass\n".format(
            (float(num_words) - num_rare) / num_words * 100))
    return vocab

def process_ngrams(ngram_path, vocab, bow):
    count_word = {}
    count_context = {}
    count_word_context = {}
    window_size = -1
    with open(ngram_path, "r") as ngram_file:
        for line in ngram_file:
            toks = line.split("\t")
            if len(toks) != 2:
                print("Skipping a faulty line: ", line[:-1])
                continue
            count = int(toks[1])
            words = toks[0].split()
            window_size = len(words)
            center = int((window_size - 1) / 2)  # Right biased.
            word = words[center] if words[center] in vocab else RARE_SYMBOL
            if not word in count_word:
                count_word[word] = 0
            count_word[word] += count
            for i in range(window_size):
                if i == center: continue
                context = words[i] if words[i] in vocab else RARE_SYMBOL
                if not bow:
                    context = "w({0})={1}".format(center - i, context)
                if not context in count_context:
                    count_context[context] = 0
                count_context[context] += count
                if not context in count_word_context:
                    count_word_context[context] = {}
                if not word in count_word_context[context]:
                    count_word_context[context][word] = 0
                count_word_context[context][word] += count  # Column-major.

    assert(len(count_word_context) == len(count_context))

    return count_word_context, count_word, count_context, window_size

def write_counts(count_word_context, count_word, count_context,
                 rare_cutoff, window_size, bow):
    word_str2num = {}
    word_num2str = {}
    context_str2num = {}
    context_num2str = {}

    signature0 = "rare{0}".format(rare_cutoff)
    signature1 = signature0 + "_window{0}".format(window_size)
    if bow:
        signature1 += "_bow"
    signature1 += "_spl"

    # Write filtered word dictionary.
    word_str2num_file_path = \
        os.path.join(output_path, "word_str2num_" + signature0)
    with open(word_str2num_file_path, "w") as word_str2num_file:
        for word in count_word:
            if not word in word_str2num:
                new_index = len(word_str2num)
                word_str2num[word] = new_index
                word_num2str[new_index] = word
            word_num = word_str2num[word]
            word_str2num_file.write(word + " " + str(word_num) + "\n")

    # Write filtered word counts.
    count_word_file_path = \
        os.path.join(output_path, "count_word_" + signature0)
    with open(count_word_file_path, "w") as count_word_file:
        # Write counts in order of word number.
        for word_num in range(len(count_word)):
            word = word_num2str[word_num]
            count_word_file.write(str(count_word[word]) + "\n")

    # Write filtered context dictionary.
    context_str2num_file_path = \
        os.path.join(output_path, "context_str2num_" + signature1)
    with open(context_str2num_file_path, "w") as context_str2num_file:
        for context in count_context:
            if not context in context_str2num:
                new_index = len(context_str2num)
                context_str2num[context] = new_index
                context_num2str[new_index] = context
            context_num = context_str2num[context]
            context_str2num_file.write(context + " " + str(context_num) + "\n")

    # Write filtered context counts.
    count_context_file_path = \
        os.path.join(output_path, "count_context_" + signature1)
    with open(count_context_file_path, "w") as count_context_file:
        # Write counts in order of context number.
        for context_num in range(len(count_context)):
            context = context_num2str[context_num]
            count_context_file.write(str(count_context[context]) + "\n")

    # Write co-occurrence counts.
    count_word_context_file_path = \
        os.path.join(output_path, "count_word_context_" + signature1)
    dim1 = len(word_str2num)
    dim2 = len(context_str2num)
    num_nonzeros = sum([len(count_word_context[context]) for context in
                        count_word_context])
    with open(count_word_context_file_path, "w") as count_word_context_file:
        # First line.
        count_word_context_file.write(str(dim1) + " " +
                                      str(dim2) + " " +
                                      str(num_nonzeros) + "\n")

        # For each column, write the number of nonzero entries followed by
        # (row, value) pairs.
        for context_num in range(len(context_str2num)):
            # Write columns in order of context number.
            context = context_num2str[context_num]
            count_word_context_file.write(str(len(count_word_context[context]))
                                          + "\n")
            for word in count_word_context[context]:
                word_num = word_str2num[word]
                cocount = count_word_context[context][word]
                count_word_context_file.write(str(word_num) + " " + str(cocount)
                                              + "\n")

    logf.write("\n[Matrix]\n")
    logf.write("   {0} x {1} ({2} nonzeros)\n".format(dim1, dim2, num_nonzeros))

def create_output_directory(args):
    """
    Creates an output directory that contains statistics necessary for deriving
    word representations.
    """
    global output_path  # Will create and write to this directory.
    output_path = args.output_path
    if os.path.exists(args.output_path):
        shutil.rmtree(args.output_path)
    os.makedirs(args.output_path)

    global logf  # Will write information here.
    logf = open(os.path.join(args.output_path, "log.0"), "w")

    # Sort word types by counts.
    sorted_wordcounts = extract_sorted_word_types(args.unigram_path)

    # Determine vocab.
    vocab = create_vocab(sorted_wordcounts, args.rare_cutoff)

    # Process n-grams.
    count_word_context, count_word, count_context, window_size = \
        process_ngrams(args.ngram_path, vocab, args.bow)

    assert(len(count_word) <= len(vocab))

    # Write n-grams in a sparse matrix format for SVDLIBC.
    write_counts(count_word_context, count_word, count_context,
                 args.rare_cutoff, window_size, args.bow)

    logf.close()  # Close the global log file variable.

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("unigram_path", type=str, help="path to a raw "
                           "unigram file")
    argparser.add_argument("ngram_path", type=str, help="path to a raw n-gram "
                           "file")
    argparser.add_argument("output_path", type=str, help="path to an output "
                           "directory")
    argparser.add_argument("--rare_cutoff",
                           type=int, default=4000, help="word types occurring "
                           "<= this number are considered rare (default: "
                           "%(default)d)")
    argparser.add_argument("--bow", action="store_true", help="Use bag-of-words"
                           " context?")
    parsed_args = argparser.parse_args()
    create_output_directory(parsed_args)
