mnemofy
=======
A Python utility to convert between words and mnemonic numbers.

Description
-----------
The utility uses the [CMU pronouncing dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) to map words to numbers using the [mnemonic major system](http://en.wikipedia.org/wiki/Mnemonic_major_system). Amaze your friends and family by easily memorizing numbers!

When given a set of words, the utility outputs the corresponding mnemonic numbers:
    $ python mnemofy.py it was the best of times it was the worst of times
    # Words
    it 1
    was 0
    the 1
    best 901
    of 8
    times 130
    it 1
    was 0
    the 1
    worst 401
    of 8
    times 130

When given a set of numbers, it will print all possible candidate words sorted by word frequencies in the training set:
    $ python mnemofy.py 90210 8675 309
    # Numbers
    90210 peasants
    90210 obscenities
    90210 absentees
    8675 fishkill
    309 mishap
    309 mosby
    309 mesaba
    309 amsbaugh

Training
--------
The included mnemofy.db SQLite database has been trained on the Brown and Reuters corpora from the [Natural Language Toolkit](http://nltk.org/). Modifying the `make_database` function and running the following command will re-create the database:

    $ python mnemofy.py --make-database
