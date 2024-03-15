import os
import re
import string
from pathlib import Path
from typing import Dict

import nltk
import pymorphy3
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize

nltk.download('stopwords')


class ProcessingContext:
    def __init__(self):
        self.pages_dir_path = 'raw-pages/pages/'
        self.pages_lemmas_dir_path = 'each-pages-lemmas/'
        self.stop_words = set(stopwords.words('russian'))
        self.morph_analyzer = pymorphy3.MorphAnalyzer()


def get_tokens(processing_context, file_name):
    filtered_tokens = list
    tokens_counts = {}
    with open(processing_context.pages_dir_path + '/' + file_name, 'r', encoding='utf-8') as page_content:
        text = BeautifulSoup(page_content, features='html.parser').get_text()
        tokens = wordpunct_tokenize(text)
        filtered_tokens = list(filter(
            lambda tk: is_correct(processing_context, tk), tokens))
        for token in filtered_tokens:
            if token in tokens_counts:
                tokens_counts[token] = tokens_counts[token] + 1
            else:
                tokens_counts[token] = 1

    return tokens_counts


def is_correct(processing_context, token):
    are_stuck_words = False
    if sum(map(str.isupper, token[1:])) > 0 and (sum(map(str.islower, token[1:])) > 0 or str.islower(token[0])):
        are_stuck_words = True
    is_good_word = True if processing_context.morph_analyzer.parse(token)[0].score >= 0.5 else False
    has_punctuation = True if any(x in string.punctuation for x in token) else False
    is_stop_word = bool(token.lower() in processing_context.stop_words)
    is_number = bool(re.compile(r'^[0-9]+$').match(token))
    is_russian = bool(re.compile(r'^[а-яА-Я]{2,}$').match(token))
    return not has_punctuation and not is_stop_word and not is_number and is_russian and not are_stuck_words and \
        is_good_word


def get_pages_tokens(processing_context: ProcessingContext):
    index = open('raw-pages/index.txt', 'r')
    line = index.readline()
    pages_tokens = []
    while line:
        parsed_index_line = line.rstrip("\r\n").split(' ', 1)
        file_name = parsed_index_line[0] + '.txt'
        pages_tokens.append(get_tokens(processing_context, file_name))
        line = index.readline()

    return pages_tokens


def calculate_token_tf(pages_tokens: list):
    pages_tf = []
    for page in pages_tokens:
        page_tf = {}
        pages_word_count = sum(page.values())
        for token in page:
            page_tf[token] = page[token] / pages_word_count

        pages_tf.append(page_tf)

    return pages_tf


def calculate_token_idf(pages_tokens: list):
    idf = {}
    pages_count = len(pages_tokens)
    for page in pages_tokens:
        for token in page:
            if token not in idf:
                idf[token] = pages_count / find_token_entrance_count_among_pages(pages_tokens, token)

    return idf


def find_token_entrance_count_among_pages(pages_tokens, token):
    counter = 0
    for page in pages_tokens:
        if token in page:
            counter = counter + 1

    return counter


def calculate_lemma_tf(processing_context: ProcessingContext, pages_tokens: list):
    pages_tf = []
    for page in pages_tokens:
        page_tf = {}
        for token in page:
            parsed_token = processing_context.morph_analyzer.parse(token)[0]
            normal_form = parsed_token.normal_form if parsed_token.normalized.is_known else token.lower()
            if normal_form not in page_tf:
                page_tf[normal_form] = page.get(token)
            else:
                page_tf[normal_form] += page.get(token)

        for lemma in page_tf:
            page_tf[lemma] = page_tf[lemma] / len(page)

        pages_tf.append(page_tf)

    return pages_tf


def calculate_lemmas_idf(lemma_tf: list):
    idf = {}
    pages_count = len(lemma_tf)
    for page in lemma_tf:
        for lemma in page:
            if lemma not in idf:
                idf[lemma] = pages_count / find_token_entrance_count_among_pages(lemma_tf, lemma)

    return idf


def write_tf_idf(tf: list, idf: dict, directory_name: str):
    for page_number in range(0, len(tf)):
        tf_idf_file_direction = 'raw-pages/' + directory_name + '/' + str(page_number) + '.txt'
        Path('raw-pages/' + directory_name).mkdir(exist_ok=True)
        with open(tf_idf_file_direction, 'w') as file:
            for term in tf[page_number]:
                line = term + ' '
                line += str(tf[page_number][term]) + ' '
                line += str(idf[term])
                line += '\n'
                file.write(line)


def main():
    processing_context = ProcessingContext()
    pages_tokens = get_pages_tokens(processing_context)
    token_tf = calculate_token_tf(pages_tokens)
    token_idf = calculate_token_idf(pages_tokens)
    lemma_tf = calculate_lemma_tf(processing_context, pages_tokens)
    lemma_idf = calculate_lemmas_idf(lemma_tf)
    write_tf_idf(token_tf, token_idf, 'token_tf_idf')
    write_tf_idf(lemma_tf, lemma_idf, 'lemma_tf_idf')


if __name__ == '__main__':
    main()
