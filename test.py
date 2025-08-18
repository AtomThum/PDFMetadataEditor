import warnings as wn

from bookmarks import Bookmark, Counter, Metadata, number_to_base_list

metadata = Metadata.construct_metadata_from_pdf(pdf_path="ladr.pdf")
metadata.output_to_md()
