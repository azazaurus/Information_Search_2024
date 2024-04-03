from typing import Dict, List

from flask import Flask, render_template, request
from urllib.parse import unquote_plus

import page_rank
import task_5


class SearchResult:
    def __init__(self, title: str, url: str, score: float):
        self.title = title
        self.url = url
        self.score = score


class VectorSearch:
    def __init__(self, index: Dict[int, str]):
        self.pc = task_5.ProcessingContext()
        self.vector_search = task_5.VectorSearch()
        self.index = index
        self.lemmas_tf_idf, self.lemmas_idf = self.vector_search.calculate_pages_tf_idf()

    def search(self, query: str) -> List[SearchResult]:
        query_lemmas_tf_idf = self.vector_search.calculate_query_tf_idf(
            self.vector_search.calculate_query_tf(self.pc, query),
            self.lemmas_idf)
        complemented_pages_vector = self.vector_search.complement_page_vector(
            self.lemmas_tf_idf,
            query_lemmas_tf_idf)
        found_documents = self.vector_search.search(complemented_pages_vector, query_lemmas_tf_idf)

        results: List[SearchResult] = []
        for page_id, distance_to_page in found_documents:
            page_url = self.index[page_id]
            results.append(SearchResult(page_url, page_url, distance_to_page))

        results.sort(key = lambda x: x.score)
        self.to_scores(results)
        return results

    @staticmethod
    def to_scores(results: List[SearchResult]) -> None:
        if len(results) < 1:
            return

        min_score = results[0].score
        max_score = min_score
        for result in results:
            if result.score < min_score:
                min_score = result.score
            if result.score > max_score:
                max_score = result.score
        
        min_max_score_difference = max_score - min_score
        for result in results:
            if min_max_score_difference == 0:
                result.score = 100
                continue
            
            result.score = (1 - (result.score - min_score) / min_max_score_difference) * 100


index = task_5.get_index() 
vector_search = VectorSearch(index)

app = Flask(__name__, static_folder = "../static", template_folder = "../templates")


@app.route("/")
def search():
    decoded_query = unquote_plus(bytes.decode(request.query_string, errors = "replace"))
    search_query = decoded_query[len("query="):]
    search_results = vector_search.search(search_query)
    return render_template("search.html", search_query = search_query, search_results = search_results)


@app.route("/page-ranks")
def page_ranks():
    page_ranks = page_rank.get_page_rank()

    page_rank_results: List[SearchResult] = []
    for page_id, page_rank_value in page_ranks.items():
        page_url = index[page_id]
        page_rank_results.append(SearchResult(page_url, page_url, page_rank_value))
    page_rank_results.sort(key = lambda x: x.score, reverse = True)
    return render_template("page-ranks.html", page_ranks = page_rank_results)


if __name__ == "__main__":
    app.run()
