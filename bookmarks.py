import itertools as itr
import os
import warnings as wn
from collections import deque
from io import TextIOWrapper
from types import FunctionType
from typing import Final

import roman


def number_to_base_list(number: int, base: int) -> list[int]:
    base_representation: list[int] = []
    if base < 2:
        raise ArithmeticError(
            f"Base should be number greater than one. Received {base} instead."
        )
    if number < 0:
        raise ArithmeticError(f"The number got, {number}, is less than zero.")
    elif number == 0:
        return [0]
    elif number > 0:
        while number > 0:
            quotient, remainder = divmod(number, base)
            base_representation.append(remainder)
            number = quotient

    base_representation = base_representation[::-1]
    return base_representation


class Counter:
    counter_styles: Final[list[str]] = [
        "LowercaseRomanNumerals",
        "DecimalArabicNumerals",
        "UppercaseRomanNumerals",
        "UppercaseAlphaNumerals",
        "LowercaseAlphaNumerals",
        "NoNumber",
    ]

    def __init__(
        self,
        start_counting_from: int,
        start_at_page: int,
        style: str,
        prefix=None,
        stop_at_page: int | None = None,
    ) -> None:
        self.start_counting_from: int = start_counting_from
        self.start_at_page: int = start_at_page
        self.stop_at_page: int | None = stop_at_page
        self.prefix: None | str = prefix

        if style not in Counter.counter_styles:
            raise KeyError(f"Counter style, {style}, not recognized")
        else:
            self.style = style

        match self.style:
            case "LowercaseRomanNumerals":
                self.page_to_label: FunctionType | None = (
                    Counter.to_lowercase_roman_numeral
                )
            case "DecimalArabicNumerals":
                self.page_to_label: FunctionType | None = (
                    Counter.to_decimal_arabic_numeral
                )
            case "UppercaseRomanNumerals":
                self.page_to_label: FunctionType | None = (
                    Counter.to_uppercase_roman_numeral
                )
            case "UppercaseAlphaNumerals":
                self.page_to_label: FunctionType | None = (
                    Counter.to_uppercase_alpha_numeral
                )
            case "LowercaseAlphaNumerals":
                self.page_to_label: FunctionType | None = (
                    Counter.to_lowercase_alpha_numeral
                )
            case "NoNumber":
                self.page_to_label: FunctionType | None = None

    def __str__(self) -> str:
        return (
            f"- Start at absolute page: {self.start_at_page}\n"
            + f"- Start counting from: {self.start_counting_from}\n"
            + f"- Style: {self.style}"
        )

    def __repr__(self) -> str:
        return (
            f"Start at absolute page: {self.start_at_page}\n"
            + f"Start counting from: {self.start_counting_from}\n"
            + f"Style: {self.style}"
        )

    @staticmethod
    def to_lowercase_roman_numeral(page_number: int) -> str:
        return roman.toRoman(page_number).lower()

    @staticmethod
    def to_uppercase_roman_numeral(page_number: int) -> str:
        return roman.toRoman(page_number)

    @staticmethod
    def to_decimal_arabic_numeral(page_number: int) -> str:
        return str(page_number)

    @staticmethod
    def to_lowercase_alpha_numeral(page_number: int) -> str:
        page_label = []
        while page_number > 0:
            page_number, remainder = divmod(page_number - 1, 26)
            page_label.append(chr(ord("a") + remainder))
        return "".join(reversed(page_label))

    @staticmethod
    def to_uppercase_alpha_numeral(page_number: int) -> str:
        return Counter.to_lowercase_alpha_numeral(page_number).upper()


class Bookmark:
    def __init__(self, title: str, level: int, page_number: int):
        self.title: str = title
        self.level: int = level
        self.page_number: int = page_number

    # Returns a raw string conversion
    def __str__(self) -> str:
        return f"{(self.level - 1) * 4 * " "}- {self.title} {self.page_number}"


class Metadata:
    def __init__(
        self,
        page_amount: int,
        counters: list[Counter] | deque[Counter] = [],
        bookmarks: list[Bookmark] | deque[Bookmark] = [],
        metadatas: list[str] = [],
    ):
        self.page_amount: int = page_amount
        if isinstance(counters, deque):
            self.counters: deque[Counter] = counters
        elif isinstance(counters, list):
            self.counters: deque[Counter] = deque(counters)
        if isinstance(bookmarks, deque):
            self.bookmarks: deque[Bookmark] = bookmarks
        elif isinstance(bookmarks, list):
            self.bookmarks: deque[Bookmark] = deque(bookmarks)

        self.label_list: list[str] = []
        self.metadatas: list[str] = metadatas

    @classmethod
    def construct_metadata_from_pdf(
        cls, pdf_path: str, metadata_output_path: None | str = None
    ):
        pdf_metadata: str = os.popen(f"pdftk {pdf_path} dump_data").read()
        pdf_metadatas: list[str] = pdf_metadata.split("\n")
        page_amount_line: int | None = cls.find_text_range_in_list(
            pdf_metadatas, "NumberOfPages"
        )[0]
        if page_amount_line is None:
            raise KeyError(
                "No page amount specified in metadata. Something is seriously wrong with this PDF."
            )

        page_amount: int = int(pdf_metadatas[page_amount_line].split(": ", 1)[-1])
        metadata = Metadata(page_amount, metadatas=pdf_metadatas)
        metadata.parse_pdf_metadatas()

        if metadata_output_path is not None:
            with open(metadata_output_path, "w") as output_file:
                output_file.write(pdf_metadata)

        return metadata

    def parse_pdf_metadatas(self, metadatas_override: list[str] | None = None):
        # If no metadatas are available
        if not self.metadatas and metadatas_override is None:
            raise ValueError("PDF Metadata is empty")

        self._create_bookmarks_from_pdf_metadatas(self.metadatas)
        self._create_counters_from_pdf_metadatas(self.metadatas)

    @staticmethod
    def find_text_range_in_list(
        target_list: list[str], target_str: str
    ) -> tuple[int | None, int | None]:
        does_text_contain_str: list[bool] = [
            True if (target_str in text) else False for text in target_list
        ]
        try:
            start_index: int | None = does_text_contain_str.index(True)
            end_index: int | None = len(does_text_contain_str) - does_text_contain_str[
                ::-1
            ].index(True)
        except ValueError:
            start_index = None
            end_index = None
        return start_index, end_index

    def add_bookmark_to_bookmarks(self, bookmark: Bookmark):
        self.bookmarks.append(bookmark)

    def add_counter_to_counters(self, counter: Counter):
        self.counters.append(counter)

    def _create_bookmarks_from_pdf_metadatas(self, pdf_metadatas: list[str]):
        bookmark_metadata_start, bookmark_metadata_end = self.find_text_range_in_list(
            pdf_metadatas, "Bookmark"
        )
        bookmark_metadatas: deque[str] = deque(
            pdf_metadatas[bookmark_metadata_start:bookmark_metadata_end]
        )

        if bookmark_metadatas[0] == "BookmarkBegin":
            bookmark_metadatas.popleft()

        if bookmark_metadatas[-1] != "BookmarkBegin":
            bookmark_metadatas.append("BookmarkBegin")

        bookmark_title: str = ""
        bookmark_level: int | None = 0
        bookmark_page_number: int | None = 0
        current_type: int = 0

        for line_number, bookmark_metadata in enumerate(bookmark_metadatas):
            if bookmark_metadata != "BookmarkBegin":
                bookmark_metadata = tuple(bookmark_metadata.split(": ", maxsplit=1))
                match bookmark_metadata:
                    case ["BookmarkTitle", title]:
                        bookmark_title = title
                        current_type = 0
                    case ["BookmarkLevel", level]:
                        bookmark_level = int(level)
                        current_type = 1
                    case ["BookmarkPageNumber", page_number]:
                        bookmark_page_number = int(page_number)
                        current_type = 2
                    case [other]:  # Lines without headers
                        if current_type == 0:
                            bookmark_title += " " + other
                            wn.warn(
                                f"Line {line_number} might not contain bookmark."
                                + f"Added string ` {other}` to previous bookmark nonetheless."
                            )
                        else:
                            raise KeyError("Bookmark")
            else:
                if isinstance(bookmark_level, int) and isinstance(
                    bookmark_page_number, int
                ):
                    self.add_bookmark_to_bookmarks(
                        Bookmark(bookmark_title, bookmark_level, bookmark_page_number)
                    )
                    bookmark_title = ""
                    bookmark_level = None
                    bookmark_page_number = None
                else:
                    raise TypeError(
                        f"Bookmark level or page number missing at metadata line {line_number}"
                    )

    def _create_counters_from_pdf_metadatas(self, pdf_metadatas: list[str]) -> None:
        counter_metadata_start, counter_metadata_end = self.find_text_range_in_list(
            pdf_metadatas, "PageLabel"
        )
        counter_metadatas: deque[str] = deque(
            pdf_metadatas[counter_metadata_start:counter_metadata_end]
        )

        if counter_metadatas[0] == "PageLabelBegin":
            counter_metadatas.popleft()

        if counter_metadatas[-1] != "PageLabelBegin":
            counter_metadatas.append("PageLabelBegin")

        counter_start_counting_from: int | None = None
        counter_start_at_page: int | None = None
        counter_prefix: str = ""
        counter_style: str = "NoNumber"

        for line_number, counter_metadata in enumerate(counter_metadatas):
            if counter_metadata != "PageLabelBegin":
                counter_metadata = tuple(counter_metadata.split(": ", maxsplit=1))
                match counter_metadata:
                    case ["PageLabelNewIndex", start_at_page]:
                        counter_start_at_page = int(start_at_page)
                    case ["PageLabelStart", start_counting_from]:
                        counter_start_counting_from = int(start_counting_from)
                    case ["PageLabelPrefix", prefix]:
                        counter_prefix = prefix
                    case ["PageLabelNumStyle", style]:
                        if style in Counter.counter_styles:
                            counter_style = style
                        else:
                            raise KeyError(
                                f"Counter style {style} at line {line_number} is not yet supported"
                            )
                    case _:
                        raise SyntaxError(
                            f"Metadata at line {line_number} not recognized as counter metadata"
                        )
            else:
                if isinstance(counter_start_at_page, int) and isinstance(
                    counter_start_counting_from, int
                ):
                    self.add_counter_to_counters(
                        Counter(
                            start_counting_from=counter_start_counting_from,
                            start_at_page=counter_start_at_page,
                            style=counter_style,
                            prefix=counter_prefix,
                        )
                    )
                else:
                    raise TypeError(
                        f"Counter starting page or counter starting from index missing at metadata line {line_number}"
                    )

        self._check_and_update_counter()

    def _check_and_update_counter(self) -> None:
        if self.counters[0].start_at_page > 1:
            wn.warn(
                "Added an alphabetical counter at the beginning because first counter doesn't count from page one."
            )
            self.add_counter_to_counters(
                Counter(
                    start_counting_from=1,
                    start_at_page=1,
                    style="UppercaseRomanNumerals",
                )
            )

        for counter, next_counter in itr.pairwise(self.counters):
            counter.stop_at_page = next_counter.start_at_page - 1
            if callable(counter.page_to_label):
                # for page in range(counter.start_at_page, next_counter.start_at_page):
                for page in range(
                    counter.start_counting_from,
                    next_counter.start_at_page
                    - counter.start_at_page
                    + counter.start_counting_from,
                ):
                    self.label_list.append(counter.page_to_label(page))
            else:
                self.label_list += [
                    "None"
                    for _ in range(counter.start_at_page, next_counter.start_at_page)
                ]
        else:
            if callable(self.counters[-1].page_to_label):
                for page in range(
                    self.counters[-1].start_counting_from,
                    self.page_amount
                    - self.counters[-1].start_at_page
                    + self.counters[-1].start_counting_from
                    + 1,
                ):
                    if callable(self.counters[-1].page_to_label):
                        self.label_list.append(self.counters[-1].page_to_label(page))
            else:
                self.label_list += [
                    "None"
                    for _ in range(
                        self.counters[-1].start_at_page, self.page_amount + 1
                    )
                ]

    def output_to_md(self, md_file_path: str = "output.md") -> None:
        with open(md_file_path, "w") as md_file:
            md_file.write(f"# Pages amount: {self.page_amount}\n\n")

            md_file.write("# Counters\n\n")
            self._forward_parse_counters(md_file)

            md_file.write("# Bookmarks\n\n")
            self._forward_parse_bookmarks(md_file)

    def _forward_parse_counters(self, md_file: TextIOWrapper) -> None:
        for counter_index, counter in enumerate(self.counters):
            md_file.write(f"Counter {counter_index}:\n")
            md_file.write(str(counter))
            md_file.write("\n\n")

    def _forward_parse_bookmarks(self, md_file: TextIOWrapper) -> None:
        for bookmark in self.bookmarks:
            md_file.write(
                f"{' ' * 4 * (bookmark.level - 1)}- {bookmark.title} {self.label_list[bookmark.page_number - 1]}\n"
            )
