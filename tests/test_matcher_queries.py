import pytest

from cascade_pod import store, vocabulary

PREFIXES = """
@prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix pav: <http://purl.org/pav/> .
@prefix rec: <https://ns.cascadeprotocol.org/records/v1-draft#> .
@prefix rxnorm: <http://www.nlm.nih.gov/research/umls/rxnorm/> .
@prefix snomed: <http://snomed.info/sct/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix : <urn:x:> .
"""
BOTH = {("a", "b"), ("b", "a")}
INGREDIENT_MAP = "snomed:91936005 rec:sameIngredientAs rxnorm:733, rxnorm:734 ."
VACCINE_GROUPS = """[] rec:cvxCode "141" ; rec:vaccineGroup "INFLUENZA" .
                    [] rec:cvxCode "150" ; rec:vaccineGroup "INFLUENZA" ."""


def immunizations(code_a, date_a, code_b, date_b):
    def one(name, code, date):
        dated = f'; rec:date "{date}"^^xsd:date' if date else ""
        return f':{name} rec:kind "Immunization" ; pav:hasCurrentVersion :{name}v . :{name}v health:vaccineCode "{code}" {dated} .\n'
    return one("a", code_a, date_a) + one("b", code_b, date_b)


CASES = {
    "same-code/two allergies sharing an rxnorm code": ("same-code", """
        :a rec:kind "Allergy" ; pav:hasCurrentVersion :av . :av health:allergenCode rxnorm:10180 .
        :b rec:kind "Allergy" ; pav:hasCurrentVersion :bv . :bv health:allergenCode rxnorm:10180 .
    """, BOTH),
    "same-code/two procedures sharing a code on different dates": ("same-code", """
        :a rec:kind "Procedure" ; pav:hasCurrentVersion :av . :av clinical:snomedCode "73761001" ; rec:date "2025-03-01"^^xsd:date .
        :b rec:kind "Procedure" ; pav:hasCurrentVersion :bv . :bv clinical:snomedCode "73761001" ; rec:date "2026-09-01"^^xsd:date .
    """, BOTH),
    "same-code/an allergy and a condition sharing a code": ("same-code", """
        :a rec:kind "Allergy" ; pav:hasCurrentVersion :av . :av health:snomedCode snomed:38341003 .
        :b rec:kind "Condition" ; pav:hasCurrentVersion :bv . :bv health:snomedCode snomed:38341003 .
    """, set()),
    "same-code/a code only an earlier version shared": ("same-code", """
        :a rec:kind "Allergy" ; pav:hasCurrentVersion :av2 . :av1 health:allergenCode rxnorm:10180 .
        :av2 health:allergenCode rxnorm:2670 .
        :b rec:kind "Allergy" ; pav:hasCurrentVersion :bv . :bv health:allergenCode rxnorm:10180 .
    """, set()),
    "same-code-and-date/one code on one date": ("same-code-and-date", immunizations("150", "2025-10-01", "150", "2025-10-01"), BOTH),
    "same-code-and-date/one code on two dates": ("same-code-and-date", immunizations("150", "2025-10-01", "150", "2025-10-02"), set()),
    "same-code-and-date/one code, one date missing": ("same-code-and-date", immunizations("150", "2025-10-01", "150", None), set()),
    "same-mapped-code/a pair the map holds": ("same-mapped-code", INGREDIENT_MAP + """
        :a rec:kind "Allergy" ; pav:hasCurrentVersion :av . :av health:allergenCode snomed:91936005 .
        :b rec:kind "Allergy" ; pav:hasCurrentVersion :bv . :bv health:allergenCode rxnorm:733 .
    """, BOTH),
    "same-mapped-code/a pair the map does not hold": ("same-mapped-code", INGREDIENT_MAP + """
        :a rec:kind "Allergy" ; pav:hasCurrentVersion :av . :av health:allergenCode snomed:91936005 .
        :b rec:kind "Allergy" ; pav:hasCurrentVersion :bv . :bv health:allergenCode rxnorm:7980 .
    """, set()),
    "same-mapped-code/two rxnorm codes mapped from one snomed code": ("same-mapped-code", INGREDIENT_MAP + """
        :a rec:kind "Allergy" ; pav:hasCurrentVersion :av . :av health:allergenCode rxnorm:733 .
        :b rec:kind "Allergy" ; pav:hasCurrentVersion :bv . :bv health:allergenCode rxnorm:734 .
    """, set()),
    "same-mapped-code-and-date/two codes of one group on one date": (
        "same-mapped-code-and-date", VACCINE_GROUPS + immunizations("141", "2025-10-15", "150", "2025-10-15"), BOTH),
    "same-mapped-code-and-date/two codes of one group on two dates": (
        "same-mapped-code-and-date", VACCINE_GROUPS + immunizations("141", "2025-10-15", "150", "2025-10-16"), set()),
    "same-mapped-code-and-date/one code on both": (
        "same-mapped-code-and-date", VACCINE_GROUPS + immunizations("150", "2025-10-15", "150", "2025-10-15"), set()),
    "same-mapped-code-and-date/a code in no group": (
        "same-mapped-code-and-date", VACCINE_GROUPS + immunizations("115", "2025-10-15", "150", "2025-10-15"), set()),
}


@pytest.mark.parametrize("engine", sorted(store.ENGINES))
@pytest.mark.parametrize("case", sorted(CASES))
def test_each_comparison_gives_both_orders_of_each_pair_it_matches_and_no_other_row(engine, case, tmp_path):
    query, turtle, expected = CASES[case]
    path = tmp_path / "pod.ttl"
    path.write_text(PREFIXES + turtle, encoding="utf-8")
    held = store.ENGINES[engine]()
    held.load(path, "urn:x:")
    found = held.select(vocabulary.query(f"matcher/{query}.rq"))
    assert {(str(row["record"])[len("urn:x:"):], str(row["other"])[len("urn:x:"):]) for row in found} == expected
    assert len(found) == len(expected)
