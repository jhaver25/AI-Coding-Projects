# Read a text file and print the total word count using python

import os

def count_words(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
        words = text.split()
        return len(words)

print(count_words('test.txt'))