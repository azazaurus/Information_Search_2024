from copy import copy

import nltk
import pymorphy3
from task_4 import is_correct
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
from collections import Counter
from nltk.corpus import stopwords
from src.task_4 import ProcessingContext, get_pages_tokens, calculate_lemma_tf, calculate_lemmas_idf


class VectorSearch:
    def __init__(self):
        self.__distance_threshold: float = 1
        self.pages_dir_path = 'raw-pages/pages/'
        self.pages_lemmas_dir_path = 'each-pages-lemmas/'
        self.stop_words = set(stopwords.words('russian'))
        self.morph_analyzer = pymorphy3.MorphAnalyzer()

    def scalar_product(self, vector1: list[float], vector2: list[float]) -> float:
        return sum(map(lambda first, second: first * second, vector1, vector2))

    def calculate_distance(self, first_vector: list, second_vector: list):
        return 1 - self.scalar_product(first_vector, second_vector) / (len(first_vector) * len(second_vector))

    def calculate_pages_tf_idf(self):
        processing_context = ProcessingContext()
        pages_tokens = get_pages_tokens(processing_context)
        lemma_tf = calculate_lemma_tf(processing_context, pages_tokens)
        lemma_idf = calculate_lemmas_idf(lemma_tf)
        pages_tf_idf: list[dict[str, float]] = list()
        for page_number in range(0, len(lemma_tf)):
            lemma_tf_idf = {}
            for term in lemma_tf[page_number]:
                term_tf_idf = lemma_tf[page_number][term] * lemma_idf[term]
                lemma_tf_idf[term] = term_tf_idf

            pages_tf_idf.append(lemma_tf_idf)

        return pages_tf_idf, lemma_idf

    def calculate_query_tf_idf(self, query_lemmas_tf, pages_idf):
        query_tf_idf: dict[str, float] = {x: 0 for x in copy(pages_idf)}
        for lemma in query_lemmas_tf:
            if lemma in pages_idf:
                query_tf_idf[lemma] = query_lemmas_tf[lemma] * pages_idf[lemma]

        return query_tf_idf

    def calculate_query_tf(self, pc: ProcessingContext, query):
        text = BeautifulSoup(query, features='html.parser').get_text()
        tokens = wordpunct_tokenize(text)

        filtered_tokens = list(filter(lambda tk: is_correct(pc, tk), tokens))
        query_lemmas_tf = Counter(list(get_normalized_form(pc, x) for x in filtered_tokens))

        return query_lemmas_tf

    def search(self, pages_lemmas_tf_idf: list[dict], query_lemmas_tf_idf: dict):
        result_documents = list()

        for page_id in range(len(pages_lemmas_tf_idf)):
            page_vector_tf_idf = list(pages_lemmas_tf_idf[page_id].values())
            query_vector_tf_idf = list(query_lemmas_tf_idf.values())
            if self.calculate_distance(page_vector_tf_idf, query_vector_tf_idf) < self.__distance_threshold:
                result_documents.append(page_id)

        return result_documents


def get_normalized_form(processing_context, token):
    parsed_token = processing_context.morph_analyzer.parse(token)[0]
    return parsed_token.normal_form if parsed_token.normalized.is_known else token.lower()


def get_index():
    index: dict[str, str] = {}
    with open('raw-pages/index.txt', 'r', encoding='utf-8') as index_file:
        line = index_file.readline()
        while line:
            index[line.split(' ')[0]] = line.split(' ')[1]
            line = index_file.readline()

    return index


def main():
    pc = ProcessingContext()
    print("Загружаю страницы \n")
    index = get_index()

    print("Загружаю рассчитанные значения TF–IDF \n")
    lemmas_tf_idf, lemmas_idf = VectorSearch().calculate_pages_tf_idf()

    print("Произвожу предрасчёты для векторного поиска \n")
    search: VectorSearch = VectorSearch()

    while True:
        query: str = input("Введите поисковый запрос: ")

        query_lemmas_tf_idf = VectorSearch().calculate_query_tf_idf(VectorSearch().calculate_query_tf(pc, query),
                                                                    lemmas_idf)

        result_documents = search.search(lemmas_tf_idf, query_lemmas_tf_idf)
        print('smthng')

        if len(result_documents) > 0:
            for document_id in result_documents:
                print(index[document_id: str])
        else:
            print("Ничего не найдено")
        print()


if __name__ == '__main__':
    main()
