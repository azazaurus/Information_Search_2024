from typing import Dict, List

import task_5
import crawler


def invert_dictionary(dictionary):
    return dict((v, k) for k, v in dictionary.items())


def convert_to_income_links(outcome_links: Dict[int, List[int]]) -> Dict[int, List[int]]:
    income_links: Dict[int, List[int]] = {}
    for page_id, page_outcome_links in outcome_links.items():
        for target_page_id in page_outcome_links:
            income_links.setdefault(target_page_id, [])
            income_links[target_page_id].append(page_id)
    return income_links


def rank(outcome_links_list: List[list], index, threshold: float = 0.000001) -> list:
    inverted_index = invert_dictionary(index)
    income_links_list: List[list] = convert_to_income_links_list(outcome_links_list, index)
    current_pagerank_of_links: list = [1 / len(index)] * len(outcome_links_list)
    result_pagerank_of_links: list = []
    delta_current_and_previous_links_pagerank_list: List[int] = []
    while True:
        current_link_index = 0
        delta_current_and_previous_links_pagerank_list: List[int] = []
        result_pagerank_of_links: list = []
        for income_links in income_links_list:
            pagerank_of_current_link = 0
            for link in income_links:
                link_index = inverted_index[link]
                pagerank_of_current_link += current_pagerank_of_links[link_index] / len(income_links[link_index])

            result_pagerank_of_links.append(pagerank_of_current_link)
            current_pagerank_of_link = current_pagerank_of_links[current_link_index]
            result_pagerank_of_link = result_pagerank_of_links[current_link_index]
            delta_current_and_previous_links_pagerank = abs(current_pagerank_of_link
                 - result_pagerank_of_link)
            delta_current_and_previous_links_pagerank_list.append(delta_current_and_previous_links_pagerank)

        if max(delta_current_and_previous_links_pagerank_list) < threshold:
            break

        current_pagerank_of_links = result_pagerank_of_links

    return result_pagerank_of_links


def pagination():
    raise NotImplemented


def filter_self_loop_links(links: Dict[int, List[int]]):
    for page_id, page_links in links.items():
        try:
            page_links.remove(page_id)
        except ValueError:
            pass


def main():
    outcome_links = crawler.read_page_outcome_links()
    index = task_5.get_index()

    filter_self_loop_links(outcome_links)
    income_links = convert_to_income_links(outcome_links)
    ranks = rank(outcome_links, index, 0.5)
    print(ranks)


if __name__ == '__main__':
    main()
