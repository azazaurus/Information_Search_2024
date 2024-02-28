from bs4 import BeautifulSoup
import nltk
import string
import re
import pymorphy3
from os import listdir
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize


class ProcessingContext:
    def __init__(self):
        self.pages_dir_path = 'raw-pages/pages/'
        self.tokens = set()
        self.lemmas = dict()
        self.stop_words = set(stopwords.words('russian'))
        self.morph_analyzer = pymorphy3.MorphAnalyzer()


def get_tokens(processing_context):
    for file_name in listdir(processing_context.pages_dir_path):
        with open(processing_context.pages_dir_path + '/' + file_name, 'r', encoding='utf-8') as page_content:
            text = BeautifulSoup(page_content, features='html.parser').get_text()
            tokens = wordpunct_tokenize(text)
            processing_context.tokens = processing_context.tokens | set(filter(
                lambda token: is_correct(processing_context, token), tokens))
    write_tokens(processing_context)


def group_tokens_by_lemmas(processing_context):
    for token in processing_context.tokens:
        parsed_token = processing_context.morph_analyzer.parse(token)[0]
        normal_form = parsed_token.normal_form if parsed_token.normalized.is_known else token.lower()
        if normal_form not in processing_context.lemmas:
            processing_context.lemmas[normal_form] = []
        processing_context.lemmas[normal_form].append(token)
    write_lemmas(processing_context)


def write_lemmas(processing_context):
    with open('lemmas.txt', 'w') as file_with_lemmas:
        for lemma, tokens in processing_context.lemmas.items():
            line = lemma + ': '
            for token in tokens:
                line += token + ' '
            line += '\n'
            file_with_lemmas.write(line)


def write_tokens(processing_context):
    with open('tokens.txt', 'w') as tokens_file:
        for token in processing_context.tokens:
            tokens_file.write(token + '\n')


def is_correct(processing_context, token):
    nltk.download('stopwords')
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
    get_tokens(processing_context)
    group_tokens_by_lemmas(processing_context)


if __name__ == '__main__':
    main()
