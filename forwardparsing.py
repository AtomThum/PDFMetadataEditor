import itertools as itr
import os

import roman


def find_range_in_list(target_list: list[str], target_str: str) -> tuple[int, int]:
    does_pdf_metadata_contain_text: list[bool] = [
        True if (target_str in text) else False for text in target_list
    ]
    start_index: int = does_pdf_metadata_contain_text.index(True)
    end_index: int = len(
        does_pdf_metadata_contain_text
    ) - does_pdf_metadata_contain_text[::-1].index(True)
    return start_index, end_index


pdf_path: str = "ladr.pdf"
pdf_metadata: str = os.popen(f"pdftk {pdf_path} dump_data").read()
pdf_metadata_list: list[str] = pdf_metadata.split("\n")

with open("output.txt", "w+") as txt_file:
    txt_file.write(pdf_metadata)

# NOTE: Locate target metadata

start_bookmark, end_bookmark = find_range_in_list(pdf_metadata_list, "Bookmark")
start_counter, end_counter = find_range_in_list(pdf_metadata_list, "PageLabel")
page_amount: int = 0

for metadata in pdf_metadata_list:
    if "NumberOfPages" in metadata:
        page_amount = int(metadata.split(": ")[1])
        break

bookmark_metadata: list[str] = [
    text
    for text in pdf_metadata_list[start_bookmark:end_bookmark]
    if text != "BookmarkBegin"
]
counter_metadata: list[str] = [
    text
    for text in pdf_metadata_list[start_counter:end_counter]
    if text != "PageLabelBegin"
]

# NOTE: Forward parsing metadata
output = "output.md"
with open(output, "w") as md_file:
    md_file.write("# Metadata location (DO NOT EDIT)\n")
    md_file.write(
        f"Begin bookmark line: {start_bookmark}\n"
        + f"End bookmark line: {end_bookmark}\n"
        + f"Begin counter line: {start_counter}\n"
        + f"End counter line: {end_counter}\n\n"
    )

    md_file.write(f"# Page amount: {page_amount}\n\n")

    md_file.write("# Counters\n")
    counter_metadatas: list = list(itr.batched(counter_metadata, 3))

    counter_pages: list[int] = []
    counter_starts: list[int] = []
    counter_styles: list[str] = []

    counter_index: int = 0
    for counter_metadata in counter_metadatas:
        counter_page_metadata, counter_start_metadata, counter_style_metadata = (
            counter_metadata
        )

        counter_page: int = int(counter_page_metadata.split(": ")[1])
        counter_start: int = int(counter_start_metadata.split(": ")[1])
        counter_style: str = ".".join(counter_style_metadata.split(": ")[1:])

        counter_pages.append(counter_page - 1)
        counter_starts.append(counter_start)
        counter_styles.append(counter_style)

        md_file.write(
            f"Counter {counter_index}:\n"
            + f"    - Start at absolute page: {counter_page}\n"
            + f"    - Start counting from: {counter_start}\n"
            + f"    - Style: {counter_style}\n"
        )
        counter_index += 1

    counter_pages.append(page_amount)
    page_labels: list = []

    for (page_start, page_end), counter_start, counter_style in zip(
        itr.pairwise(counter_pages), counter_starts, counter_styles
    ):
        enumerator: enumerate = enumerate(range(page_start, page_end), counter_start)

        if counter_style == "LowercaseRomanNumerals":
            page_labels += [roman.toRoman(number).lower() for number, _ in enumerator]
        elif counter_style == "UppercaseRomanNumerals":
            page_labels += [roman.toRoman(number) for number, _ in enumerator]
        elif counter_style == "DecimalArabicNumerals":
            page_labels += [number for number, _ in enumerator]

    md_file.write("\n# Bookmarks\n")
    for (
        bookmark_title_metadata,
        bookmark_level_metadata,
        bookmark_page_metadata,
    ) in itr.batched(bookmark_metadata, 3):
        bookmark_title: str = bookmark_title_metadata[15:]
        bookmark_level: int = int(bookmark_level_metadata.split(": ")[1])
        bookmark_page: str = page_labels[int(bookmark_page_metadata.split(": ")[1]) - 1]

        md_file.write(
            f"{' ' * 4 * (bookmark_level - 1)}- ({bookmark_page}) {bookmark_title}\n"
        )
