from typing import Dict, List, Optional

import task_5
import crawler


def convert_to_income_links(outcome_links: Dict[int, List[int]]) -> Dict[int, List[int]]:
    income_links: Dict[int, List[int]] = {}
    for page_id, page_outcome_links in outcome_links.items():
        for target_page_id in page_outcome_links:
            income_links.setdefault(target_page_id, [])
            income_links[target_page_id].append(page_id)
    return income_links


def rank(
        outcome_links: Dict[int, List[int]],
        income_links: Dict[int, List[int]],
        threshold: float = 0.000001
    ) -> Dict[int, float]:
    page_count = len(income_links)
    initial_page_rank_value = 1 / page_count
    previous_page_ranks = {page_id: initial_page_rank_value for page_id in income_links}

    while True:
        page_rank_contributions = {page_id: page_rank / len(outcome_links[page_id])
            for page_id, page_rank in previous_page_ranks.items()}

        max_page_rank_delta: Optional[float] = None
        current_page_ranks: Dict[int, float] = {}
        for page_id, page_income_links in income_links.items():
            page_rank = sum(page_rank_contributions[source_page_id] for source_page_id in page_income_links)
            current_page_ranks[page_id] = page_rank

            page_rank_delta = abs(page_rank - previous_page_ranks[page_id])
            max_page_rank_delta = (page_rank_delta
                if max_page_rank_delta is None
                else max(max_page_rank_delta, page_rank_delta))

        previous_page_ranks = current_page_ranks
        if max_page_rank_delta < threshold:
            break

    return previous_page_ranks


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
    ranks = rank(outcome_links, income_links)
    print(ranks)


if __name__ == '__main__':
    main()
