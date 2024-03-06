from itertools import chain

from bs4 import BeautifulSoup
import nltk
import string
import re
import pymorphy3
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
    filtered_tokens = set()
    with open(processing_context.pages_dir_path + '/' + file_name, 'r', encoding='utf-8') as page_content:
        text = BeautifulSoup(page_content, features='html.parser').get_text()
        tokens = wordpunct_tokenize(text)
        filtered_tokens = filtered_tokens | set(filter(
                lambda token: is_correct(processing_context, token), tokens))
    return filtered_tokens


def get_lemmas(processing_context, tokens):
    lemmas = set()
    for token in tokens:
        parsed_token = processing_context.morph_analyzer.parse(token)[0]
        normal_form = parsed_token.normal_form if parsed_token.normalized.is_known else token.lower()
        if normal_form not in lemmas:
            lemmas.add(normal_form)
    return lemmas


def write_inverted_index(inverted_index):
    with open('inverted_index.txt', 'w', encoding='windows-1251') as inverted_index_file:
        for lemma in inverted_index:
            line = lemma + ' '
            for page_number in inverted_index[lemma]:
                line += page_number + ' '
            line += '\n'
            inverted_index_file.write(line)


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


def main():
    processing_context = ProcessingContext()
    inverted_index = dict()
    index = open('raw-pages/index.txt', 'r', encoding="windows-1251")
    line = index.readline()
    while line:
        page_id = line.rsplit(' ', 1)
        file_name = page_id[0] + '.txt'
        tokens = get_tokens(processing_context, file_name)
        lemmas = get_lemmas(processing_context, tokens)
        for lemma in lemmas:
            if lemma not in inverted_index:
                inverted_index[lemma] = set(page_id[0])
            else:
                inverted_index[lemma].add(page_id[0])
        line = index.readline()

    write_inverted_index(inverted_index)


if __name__ == '__main__':
    main()
