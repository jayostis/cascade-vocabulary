import json

import pytest

from cascade_pod import Failure, match
from cascade_pod.example import Example

SUBJECT = "urn:example:subject"
RXNORM, SNOMED = "http://www.nlm.nih.gov/research/umls/rxnorm/", "http://snomed.info/sct/"


def uuid(n):
    return f"urn:uuid:00000000-0000-4000-8000-{n:012d}"


SERIES = [
    {"key": "rules", "name": uuid(1), "label": "Matcher rules", "ships_with": "1",
     "versions": [{"name": uuid(2), "version": "1", "table": "rules-1.csv"}]},
    {"key": "ingredient-map", "name": uuid(3), "label": "Ingredient map", "ships_with": "1",
     "versions": [{"name": uuid(4), "version": "1", "table": "ingredient-map-1.csv"},
                  {"name": uuid(5), "version": "2", "revises": "1", "table": "ingredient-map-2.csv"}]},
    {"key": "cvx-vaccine-groups", "name": uuid(6), "label": "Vaccine groups", "ships_with": "1",
     "versions": [{"name": uuid(7), "version": "1", "table": "cvx-vaccine-groups-1.csv"}]},
]
TABLES = {
    "rules-1.csv": "rule,applies_to,justification,table\nR1,Allergy Condition Procedure,SameCode,\n"
                   "R2,Immunization,SameCodeAndDate,\nR3,Allergy,SameMappedCode,ingredient-map\n"
                   "R4,Immunization,SameMappedCodeAndDate,cvx-vaccine-groups\n",
    "ingredient-map-1.csv": f"snomed,rxnorm\n{SNOMED}373270004,{RXNORM}7980\n",
    "ingredient-map-2.csv": "snomed,rxnorm\n",
    "cvx-vaccine-groups-1.csv": "cvx,group\n141,INFLUENZA\n150,INFLUENZA\n",
}


def reference_tables(folder):
    folder.mkdir(parents=True)
    (folder / "references.json").write_text(json.dumps({"series": SERIES}), encoding="utf-8")
    for name, text in TABLES.items():
        (folder / name).write_text(text, encoding="utf-8")


class SmallPod:
    def __init__(self, root):
        self.root, self.events = root, [{"event": "E1", "subject": SUBJECT, "adds": []}]
        reference_tables(root / "references")

    def tell(self):
        story = {"address": "https://pod.example/", "events": self.events, "derived": []}
        (self.root / "events.json").write_text(json.dumps(story), encoding="utf-8")


def test_a_series_that_ships_with_a_version_it_does_not_list_is_a_failure_not_a_traceback(tmp_path):
    pod = SmallPod(tmp_path)
    references = match.References(pod.root / "references")
    references.by_key["rules"]["ships_with"] = "no such version"
    pod.tell()
    with pytest.raises(Failure):
        references.current("rules", match.Reading(Example(tmp_path), "E1"))
