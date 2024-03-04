import os
from typing import List, Optional, Set, Union
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from collections import deque
from logs import configure_log
from raw_pages import NewRawPage, RawPageRepository
import requests
from text import delete_extra_whitespaces, format_exception
import validators

crawler_request_headers = {
	"accept": "text/html",
	"accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
	"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
}


def main(
		root_page_url: str = "https://hvost.news/",
		max_pages_count: int = 100,
		min_words_per_page_count: int = 0,
		whitelisted_domains: Optional[List[str]] = [
			"hvost.news"
		],
		blacklisted_urls: Optional[List[str]] = [
			"https://hvost.news/agreement/",
			"https://hvost.news/contacts/",
			"https://hvost.news/privacy/"
		]):
	log = configure_log()

	log.debug("Initializing page repository")
	page_repository = RawPageRepository()
	page_repository.delete_all()

	page_urls_to_download = deque([root_page_url])
	seen_page_urls = {root_page_url}
	downloaded_page_urls: Set[str] = set()
	whitelisted_domains_set = set(whitelisted_domains) if whitelisted_domains is not None else None
	blacklisted_urls_set: Set[str] = set(blacklisted_urls) if blacklisted_urls is not None else set()
	while len(page_urls_to_download) > 0 and len(downloaded_page_urls) < max_pages_count:
		page_url = page_urls_to_download.popleft()
		log.info("Downloading " + page_url)
		page_markup = _download(page_url, seen_page_urls)
		if page_markup is None:
			continue
		if issubclass(type(page_markup), Exception):
			log.warning(f"Unable to download {page_url}:" + os.linesep + format_exception(Exception(page_markup)))
			continue

		try:
			parsed_page = BeautifulSoup(str(page_markup), "html.parser")
		except Exception as exception:
			log.warning(
				f"Unable to parse {page_url} as HTML:" + os.linesep
				+ format_exception(exception) + os.linesep
				+ "Downloaded:" + os.linesep
				+ str(page_markup))
			continue

		if count_words(get_text(parsed_page)) >= min_words_per_page_count:
			downloaded_page_urls.add(page_url)
	
			log.debug("Saving " + page_url)
			page = NewRawPage(page_url, str(page_markup))
			try:
				page_repository.create(page)
			except Exception as exception:
				log.error(
					f"Unable to save {page_url}:" + os.linesep + format_exception(exception))
	
		child_urls = set(_get_link_urls(page_url, parsed_page, whitelisted_domains_set, blacklisted_urls_set))
		child_urls = child_urls.difference(seen_page_urls)

		page_urls_to_download.extend(child_urls)
		seen_page_urls = seen_page_urls.union(child_urls)


def _download(url: str, seen_page_urls: Set[str]) -> Union[str, Exception, None]:
	try:
		response = requests.get(url, headers = crawler_request_headers, stream = True)

		if response.url != url and response.url in seen_page_urls:
			return None

		content_type = response.headers.get("content-type")
		if content_type is None or len(content_type) == 0:
			return ValueError("Empty Content-Type")
		if "html" not in content_type:
			return ValueError("Unknown Content-Type: " + content_type)

		return response.text
	except Exception as error:
		return error


def _get_link_urls(
		current_url: str,
		parsed_page: BeautifulSoup,
		whitelisted_domains: Optional[Set[str]],
		blacklisted_urls: Set[str]) -> List[str]:
	if parsed_page.body is None:
		return []

	a_tags = parsed_page.body.find_all("a")
	urls = (tag.get("href", default = "") for tag in a_tags)
	urls = (urldefrag(urljoin(current_url, url))[0] for url in urls)
	return list(
		filter(
			lambda url: validators.url(url)
				and url not in blacklisted_urls
				and (whitelisted_domains is None or urlparse(url).netloc in whitelisted_domains),
			urls))


def get_text(markup: BeautifulSoup) -> str:
	text = markup.get_text(" ")
	text = delete_extra_whitespaces(text)
	return text


def count_words(text: str) -> int:
	return len(text.split())


if __name__ == "__main__":
	main()
