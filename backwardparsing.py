import itertools as itr
import subprocess as sbp

import roman

# Reconstructing variables.

with open("output.md", "r") as md_file:
    metadata_list: list[str] = md_file.read().split("\n")
    # pp.pprint(metadata_list)

    # The first 6 lines is always fixed
    metadata_locations: list[str] = metadata_list[1:5]

    start_bookmark, end_bookmark, start_counter, end_counter = [
        int(metadata_location.split(": ")[1])
        for metadata_location in metadata_locations
    ]
    page_amount: int = int(metadata_list[6].split(": ")[1])

    counter_header_location = metadata_list.index("# Counters")
    bookmark_header_location = metadata_list.index("# Bookmarks")

    counter_metadatas = metadata_list[
        counter_header_location + 1 : bookmark_header_location - 1
    ]
    bookmark_metadatas = metadata_list[bookmark_header_location + 1 : -1]

    # Creating page labels
    counter_pages: list[int] = []
    counter_starts: list[int] = []
    counter_styles: list[str] = []

    pdf_counter_metadata: list = []

    for _, counter_page, counter_start, counter_style in itr.batched(
        counter_metadatas, 4
    ):
        counter_pages.append(int(counter_page.split(": ")[1]) - 1)
        counter_starts.append(int(counter_start.split(": ")[1]))
        counter_styles.append(counter_style.split(": ")[1])

        pdf_counter_metadata += [
            "PageLabelBegin",
            f"PageLabelNewIndex: {counter_pages[-1] + 1}",
            f"PageLabelStart: {counter_starts[-1]}",
            f"PageLabelNumStyle: {counter_styles[-1]}",
        ]

    counter_pages.append(page_amount)
    print(counter_pages)
    print(counter_starts)
    print(counter_styles)

    page_label_list: list[str] = []

    for (page_start, page_end), counter_start, counter_style in zip(
        itr.pairwise(counter_pages), counter_starts, counter_styles
    ):
        enumerator: enumerate = enumerate(range(page_start, page_end), counter_start)

        if counter_style == "LowercaseRomanNumerals":
            page_label_list += [
                roman.toRoman(number).lower() for number, _ in enumerator
            ]
        elif counter_style == "UppercaseRomanNumerals":
            page_label_list += [roman.toRoman(number) for number, _ in enumerator]
        elif counter_style == "DecimalArabicNumerals":
            page_label_list += [str(number) for number, _ in enumerator]

    page_labels: dict[str, int] = {
        page_label: page for page, page_label in enumerate(page_label_list)
    }

    pdf_bookmark_metadata: list[str] = []
    # Converting markdown bookmarks into pdf bookmark tree.
    for bookmark_line in bookmark_metadatas:
        # Count amount of leading space and convert that to bookmark level:
        bookmark_level: int = (
            sum(1 for _ in itr.takewhile(str.isspace, bookmark_line)) // 4 + 1
        )
        bookmark_line = bookmark_line.lstrip()[3:]
        _ = bookmark_line.index(")")
        bookmark_page = page_labels[bookmark_line[:_]] + 1
        bookmark_title = bookmark_line[_ + 1 :].lstrip()

        pdf_bookmark_metadata += [
            "BookmarkBegin",
            f"BookmarkTitle: {bookmark_title}",
            f"BookmarkLevel: {bookmark_level}",
            f"BookmarkPageNumber: {bookmark_page}",
        ]

# Print the bookmark and counter metadata into one single file with .info extension
with open("output.info", "w") as info_file:
    info_file.write("\n".join(pdf_bookmark_metadata))
    info_file.write("\n".join(pdf_counter_metadata))

# Finally, update the pdf
sbp.run(["pdftk", "ladr.pdf", "update_info", "output.info", "output", "out.pdf"])
