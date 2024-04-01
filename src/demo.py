import task_5
import crawler


def invert_dictionary(dictionary):
    return dict((v, k) for k, v in dictionary.items())


def convert_to_income_links_list(links_list: list[list], index: dict):
    pages_count = len(index)
    inverted_index = invert_dictionary(index)
    income_links_list: list[list] = [list()] * pages_count
    for i in range(pages_count):
        for outcome_link in links_list[i]:
            if (outcome_link in inverted_index) and (outcome_link not in income_links_list[inverted_index[outcome_link]]):
                income_links_list[inverted_index[outcome_link]].append(index[i])

    return income_links_list


def rank(outcome_links_list: list[list], index, threshold: float = 0.000001) -> list:
    inverted_index = invert_dictionary(index)
    income_links_list: list[list] = convert_to_income_links_list(outcome_links_list, index)
    current_pagerank_of_links: list = [1 / len(index)] * len(outcome_links_list)
    result_pagerank_of_links: list = []
    delta_current_and_previous_links_pagerank_list: list[int] = []
    while True:
        current_link_index = 0
        delta_current_and_previous_links_pagerank_list: list[int] = []
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


def main():
    outcome_links_lists = crawler.main()
    index = task_5.get_index()
    income_links_lists = convert_to_income_links_list(outcome_links_lists, index)
    ranks = rank(outcome_links_lists, index, 0.5)
    print(ranks)


if __name__ == '__main__':
    main()
