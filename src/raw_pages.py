from pathlib import Path
import shutil
from typing import Dict, Optional


class NewRawPage:
	def __init__(self, url: Optional[str] = None, markup: Optional[str] = None):
		self.url = url
		self.markup = markup


class RawPage:
	def __init__(self, id_: int, url: str, markup: str):
		self.id_ = id_
		self.url = url
		self.markup = markup


class RawPageRepository:
	def __init__(self, name: str = "raw-pages", file_encoding: str = "utf-8"):
		repository_path = Path(name)

		self._pages_path = repository_path.joinpath("pages")
		self._pages_path.mkdir(parents = True, exist_ok = True)

		self._file_encoding = file_encoding
		self._index_full_file_name = repository_path.joinpath("index.txt")
		self._index_file = open(
			self._index_full_file_name,
			"a+",
			encoding = self._file_encoding)

		self._id_to_url_map: Dict[int, str] = {}
		self._initialize_index_from_file(True)

		self._max_id = max(self._id_to_url_map.keys(), default = -1)

	def create(self, new_page: NewRawPage) -> RawPage:
		page = RawPage(self._get_new_id(), str(new_page.url), str(new_page.markup))
		page_full_file_name = self._get_page_full_file_name(page.id_)
		with open(page_full_file_name, "w", encoding = self._file_encoding) as file:
			file.write(page.markup)

		self._append_index_line_to_file(page.id_, page.url)
		self._index_file.flush()

		self._id_to_url_map[page.id_] = page.url
		
		return page

	def delete_all(self):
		self._index_file.truncate(0)
		self._index_file.flush()
		self._id_to_url_map = {}
		self._max_id = -1

		shutil.rmtree(self._pages_path, ignore_errors = True)
		self._pages_path.mkdir(parents = True, exist_ok = True)

	class IndexRecord:
		def __init__(self, id_: int, url: str):
			self.id_ = id_
			self.url = url

	def _initialize_index_from_file(self, recreate_file_if_inconsistent: bool):
		self._index_file.seek(0)
		file_lines = self._index_file.readlines()

		self._id_to_url_map = {}
		for file_line in file_lines:
			index_line = self._deserialize_index_record(file_line)
			page_full_file_name = self._get_page_full_file_name(index_line.id_)
			if Path(page_full_file_name).is_file():
				self._id_to_url_map[index_line.id_] = index_line.url

		if recreate_file_if_inconsistent and len(self._id_to_url_map) != len(file_lines):
			self._recreate_index_file()

	def _recreate_index_file(self):
		self._index_file.truncate(0)
		for id_, url in self._id_to_url_map.items():
			self._append_index_line_to_file(id_, url)
		self._index_file.flush()

	def _get_new_id(self) -> int:
		self._max_id += 1
		return self._max_id

	def _append_index_line_to_file(self, id_: int, url: str):
		index_line = self._serialize_index_record(id_, url)
		self._index_file.write(index_line)

	def _get_page_full_file_name(self, id_: int):
		return self._pages_path.joinpath(f"{id_}.txt")

	@staticmethod
	def _serialize_index_record(id_: int, url: str) -> str:
		return f"{id_} {url}\n"

	@staticmethod
	def _deserialize_index_record(index_line: str) -> IndexRecord:
		record_values = index_line.rstrip("\n").split(" ")
		return RawPageRepository.IndexRecord(int(record_values[0]), record_values[1])
