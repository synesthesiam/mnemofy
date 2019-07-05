#!/usr/bin/python

# Copyright (C) 2013 Michael Hansen (mihansen@indiana.edu)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sqlite3, argparse, re, sys
import itertools as it
from collections import defaultdict

phone_map = {
    "B": 9, "CH": 6, "D": 1, "DH": 1,
    "ER": 4, "F": 8, "G": 7, "JH": 6,
    "K": 7, "L": 5, "M": 3, "N": 2,
    "NG": 7, "P": 9, "R": 4, "S": 0,
    "SH": 6, "T": 1, "TH": 1, "V": 8,
    "Z": 0, "ZH": 0
}

def remove_digits(s):
    """Removes all digits from a string"""
    return "".join([c for c in s if not str.isdigit(str(c))])

def mnemofy_word(word, words):
    """Converts all pronunciations of a word into numbers"""
    num_strs = set()

    for w_phones in words[word]:
        num_strs.add(mnemofy_phones([remove_digits(p) for p in w_phones]))

    return num_strs

def mnemofy_phones(phones):
    """
    Converts a set of CMU pronouncing dictionary phonemes to a mnemonic number.
    0 - s, z, soft c
    1 - d, t, th
    2 - n
    3 - m
    4 - r
    5 - l
    6 - j, sh, soft "ch", dg, zh, soft "g"
    7 - k, hard c, hard g, hard "ch", q, qu, ng
    8 - f, v
    9 - p, b
    Vowels and w, h, y are ignored.
    """
    return "".join([str(phone_map[p]) for p in phones if phone_map.has_key(p)])

def make_database(dbpath, corpora_words = None):
    """Creates a SQLite database with words, their corresponding numbers, and
    word frequencies"""

    import nltk

    # Build word list
    entries = nltk.corpus.cmudict.entries()
    words = defaultdict(list)

    for k, v in entries:
        words[k].append(v)

    # Use NLTK corpora to get word frequencies
    if not corpora_words:
        corpora_words = it.chain([word.lower() for word in nltk.corpus.brown.words()],
                                 [word.lower() for word in nltk.corpus.reuters.words()])

    word_freqs = nltk.FreqDist(corpora_words)

    # Put words into database
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS words")
    cur.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, word TEXT, freq INTEGER)")

    for w in words.keys():
        if len(w) > 1 and all([str.isalpha(str(c)) for c in w]):
            cur.execute("INSERT INTO words (word, freq) VALUES (?, ?)", (w, word_freqs[w]))

    # Words => Numbers
    cur.execute("DROP TABLE IF EXISTS word_mnums")
    cur.execute("CREATE TABLE word_mnums (id INTEGER PRIMARY KEY, word_id INTEGER, mnum TEXT)")

    # Make a list so we can reuse the cursor inside the loop
    rows = list(cur.execute("SELECT id, word from words"))
    for row in rows:
        w_id = row[0]
        w = row[1]

        for mnum in mnemofy_word(w, words):
            cur.execute("INSERT INTO word_mnums (word_id, mnum) VALUES (?, ?)", (w_id, mnum))

    conn.commit()
    conn.close()

def get_mnumbers(cur, words):
    """Returns a dictionary mapping words to frequency, mnemonic number pairs"""
    mnumbers_dict = {}

    for row in cur.execute("SELECT word, freq, mnum FROM words \
                            INNER JOIN word_mnums ON words.id = word_mnums.word_id \
                            WHERE word IN ({0})".format(",".join("?" * len(words))), words):
        word = row[0]
        freq = int(row[1])
        mnum = row[2]
        mnumbers_dict[word] = (freq, mnum)

    return mnumbers_dict

def get_words(cur, mnumbers):
    """Returns a dictionary mapping mnemonic numbers to frequency, word pairs"""
    words_dict = defaultdict(list)

    for row in cur.execute("SELECT word, freq, mnum FROM words \
                            INNER JOIN word_mnums ON words.id = word_mnums.word_id \
                            WHERE mnum IN ({0}) ORDER BY mnum, freq, word DESC".format(",".join("?" * len(mnumbers))), mnumbers):
        word = row[0]
        freq = int(row[1])
        mnum = row[2]
        words_dict[mnum].append( (freq, word) )

    return words_dict

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Mnemofy - numbers to words and back again")
    parser.add_argument("nums_or_words", type=str, nargs="*", help="numbers or words to Mnemofy") 

    parser.add_argument("--database", "-d", type=str, default="mnemofy.db",
                        help="path to sqlite database") 

    parser.add_argument("--frequencies", "-f", dest="frequencies", action="store_true", 
                        help="display word frequencies") 

    parser.add_argument("--make-database", dest="make_database", action="store_true",
                        help="recreate the Mnemofy database (requires NLTK, CMU dictionary, Brown corpus)") 

    args = parser.parse_args()

    if args.make_database:
        make_database(args.database)
        print "# Database created"

    if len(args.nums_or_words) == 0:
        # Nothing left to do
        sys.exit()

    conn = sqlite3.connect(args.database)
    cur = conn.cursor()

    if len(args.nums_or_words) > 0:
        first_num_or_word = args.nums_or_words[0].strip()

        if re.match("^\\d+$", first_num_or_word):
            print "# Numbers"
            numbers = [unicode(item) for item in args.nums_or_words]
            words_dict = get_words(cur, numbers)

            for number in numbers:
                for freq, word in sorted(words_dict[number], key=lambda fw: fw[0], reverse=True):
                    if args.frequencies:
                        print number, word, freq
                    else:
                        print number, word
        else:
            print "# Words"
            words = [item.strip().lower() for item in args.nums_or_words]
            mnumbers_dict = get_mnumbers(cur, words)

            for word in words:
                if word in mnumbers_dict:
                    freq, mnum = mnumbers_dict[word]

                    if args.frequencies:
                        print word, mnum, freq
                    else:
                        print word, mnum

    conn.close()

