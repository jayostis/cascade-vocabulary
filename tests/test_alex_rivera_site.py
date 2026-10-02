import pytest

from cascade_pod import site
from alex_rivera import ALEX
from alex_rivera import name as name_of
from test_site import blocks, page_of, pages_of, site_files

PENICILLIN = "urn:cascade:entry:a6ab153490000f8a538712abb75758f2280c92237cd33dc6eee4b8f00e8c2210"


@pytest.fixture(scope="module")
def pages():
    return pages_of(site_files(ALEX))


def test_an_entrys_page_puts_each_chosen_value_beside_the_member_it_came_from(pages):
    [shows] = [b for b in blocks(pages[page_of(PENICILLIN)]) if b["title"] == "What it shows"]
    allergen = "<https://ns.cascadeprotocol.org/health/v1#allergen>"
    assert [(row["value"]["value"], row["from"]["value"]) for row in shows["rows"]
            if row["field"]["value"] == allergen] == [('"Penicillin"', name_of("H2F-ALG-PCN").n3())]


def test_the_pipeline_page_asks_the_same_question_under_each_lens_side_by_side(pages):
    shown = {("--lens export" in b["command"], len(b["rows"])) for b in blocks(pages["pipeline.html"])
             if b["title"] == "My immunizations"}
    assert shown == {(False, 1), (True, 2)}


def test_a_turtle_link_opens_a_file_the_thing_arrived_in_and_a_thing_only_named_has_none(pages):
    [folders] = [b for b in blocks(pages["index.html"]) if b["title"] == "What each folder holds"]
    assert not [href for row in folders["rows"] if "type" in row for href in row["type"]["hrefs"]]
    profile = str(name_of("H1-PAT"))
    cells = [cell for page in pages.values() for block in blocks(page) for row in block["rows"] for cell in row.values()
             if cell["value"] == f"<{profile}>"]
    assert cells and not [href for cell in cells for href in cell["hrefs"] if href.startswith(site.COPY)]
