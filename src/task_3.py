from itertools import chain
from typing import Dict, Iterable, List, Set, Tuple

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


class SearchContext:
    def __init__(self, morph_analyzer: pymorphy3.MorphAnalyzer, inverted_index: Dict[str, Set[int]], all_page_ids: Set[int]):
        self.morph_analyzer = morph_analyzer
        self.inverted_index = inverted_index
        self.all_page_ids = all_page_ids


def get_tokens(processing_context, file_name):
    filtered_tokens = set()
    with open(processing_context.pages_dir_path + '/' + file_name, 'r', encoding='utf-8') as page_content:
        text = BeautifulSoup(page_content, features='html.parser').get_text()
        tokens = wordpunct_tokenize(text)
        filtered_tokens = filtered_tokens | set(filter(
                lambda token: is_correct(processing_context, token), tokens))
    return filtered_tokens


def get_lemmas(morph_analyzer, tokens):
    lemmas = set()
    for token in tokens:
        parsed_token = morph_analyzer.parse(token)[0]
        normal_form = parsed_token.normal_form if parsed_token.normalized.is_known else token.lower()
        if normal_form not in lemmas:
            lemmas.add(normal_form)
    return lemmas


def write_inverted_index(inverted_index):
    with open('inverted_index.txt', 'w', encoding='windows-1251') as inverted_index_file:
        for lemma in inverted_index:
            line = lemma + ' '
            for page_number in inverted_index[lemma]:
                line += str(page_number) + ' '
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


def search_for(search_context, original_query):
    opening_parentheses_stack = []
    results = []
    query = original_query
    i = 0
    while i < len(query):
        if query[i] == "(":
            opening_parentheses_stack.append(i)
        elif query[i] == ")":
            start_index = opening_parentheses_stack.pop()
            end_index = i
            sub_query = query[start_index:end_index + 1]
            query = query[:start_index] + '$' + query[end_index + 1:]
            i -= len(sub_query) - 1
            evaluate_query(search_context, sub_query, results)

        i += 1

    evaluate_query(search_context, query, results)
    return results[0]


def evaluate_query(search_context: SearchContext, query: str, results: List[Set[int]]):
    query = query.strip().lstrip("(").rstrip(")")
    and_operator_entries = ((x.start(), " and ") for x in re.finditer("\\sAND\\s", query))
    or_operator_entries = ((x.start(), " or ") for x in re.finditer("\\sOR\\s", query))
    operators: List[Tuple[int, str]] = list(chain(and_operator_entries, or_operator_entries))
    operators.sort(key = lambda x: x[0])
    operators.append((len(query), " and ")) # border fake operator

    query_results = []
    for i in range(len(query) - 1, -1, -1):
        if query[i] == "$":
            query_results.append(results.pop())

    not_operator_entries = set(x.start() for x in re.finditer("NOT\\s", query))
    current_result = evaluate_operand(search_context, 0, query[:operators[0][0]], query_results, not_operator_entries)
    for i in range(len(operators) - 1):
        current_operator = operators[i]
        start_index = current_operator[0] + len(current_operator[1])
        end_index = operators[i + 1][0]
        operand = evaluate_operand(search_context, start_index, query[start_index:end_index], query_results, not_operator_entries)

        if current_operator[1] == " and ":
            current_result.intersection_update(operand)
        elif current_operator[1] == " or ":
            current_result = current_result.union(operand)
        else:
            raise ValueError("Unexpected operator \"" + current_operator[1] + "\"")

    results.append(current_result)


def evaluate_operand(
        search_context: SearchContext,
        start_index: int,
        token: str,
        results: List[Set[int]],
        not_operator_entries: Set[int]) -> Set[int]:
    prepared_token = token.lstrip()
    start_index += len(token) - len(prepared_token)
    prepared_token = prepared_token.rstrip()

    is_negated = start_index in not_operator_entries
    if is_negated:
        prepared_token = prepared_token[len("not"):].lstrip()

    result = results.pop() if prepared_token == "$" else find_pages(search_context, prepared_token)
    return result if not is_negated else search_context.all_page_ids.difference(result)


def find_pages(search_context: SearchContext, token: str) -> Set[int]:
    lemma = next(iter(get_lemmas(search_context.morph_analyzer, [token])))
    return search_context.inverted_index.get(lemma, set())


def find_page_urls(page_urls: Dict[int, str], page_ids: Iterable[int]) -> List[str]:
    return [page_urls[id_] for id_ in page_ids]


def main():
    processing_context = ProcessingContext()
    inverted_index: Dict[str, Set[int]] = dict()
    page_urls: Dict[int, str] = dict()
    index = open('raw-pages/index.txt', 'r', encoding="windows-1251")
    line = index.readline()
    while line:
        parsed_index_line = line.rstrip("\r\n").split(' ', 1)
        page_id = int(parsed_index_line[0])
        page_urls[page_id] = parsed_index_line[1]

        file_name = parsed_index_line[0] + '.txt'
        tokens = get_tokens(processing_context, file_name)
        lemmas = get_lemmas(processing_context.morph_analyzer, tokens)
        for lemma in lemmas:
            if lemma not in inverted_index:
                inverted_index[lemma] = { page_id }
            else:
                inverted_index[lemma].add(page_id)
        line = index.readline()

    write_inverted_index(inverted_index)

    while True:
        print("Your search query: ")
        query = input()
        page_ids = search_for(
            SearchContext(processing_context.morph_analyzer, inverted_index, set(page_urls.keys())),
            query)
        result_page_urls = find_page_urls(page_urls, page_ids)
        for page_url in result_page_urls:
            print(page_url)


if __name__ == '__main__':
    main()
