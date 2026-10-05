import xml.etree.ElementTree as ElementTree

import pytest

from alex_rivera import ADDRESS, INPUT, KIT, STORY
from cascade_pod import vocabulary
from examples import ROOT


def alex():
    """What only Alex's kit says: her pod's address, the kit's title, her subject and her hospitals."""
    facts = {ADDRESS, vocabulary.title(KIT), STORY["subject"]}
    for export in INPUT.glob("downloads/*/apple_health_export/export.xml"):
        facts |= {entry.get("sourceName") for entry in ElementTree.parse(export).getroot().iter("ClinicalRecord")}
    return facts


def mentions(text, facts):
    return sorted(fact for fact in facts if fact.lower() in text.lower())


def test_the_alex_check_finds_her_address_in_a_line_of_code():
    assert mentions('POD = "https://pod.alex-rivera.example/"', alex()) != []


@pytest.mark.parametrize("module", sorted(path.name for path in (ROOT / "cascade_pod").glob("*.py")))
def test_nothing_in_cascade_pod_names_alex(module):
    assert mentions((ROOT / "cascade_pod" / module).read_text(encoding="utf-8"), alex()) == []


@pytest.mark.parametrize("module", sorted(path.name for path in (ROOT / "tests").glob("*.py")
                                          if not path.name.startswith(("alex_rivera", "test_alex_rivera_"))))
def test_nothing_in_the_tests_but_alex_riveras_own_files_names_alex(module):
    assert mentions((ROOT / "tests" / module).read_text(encoding="utf-8"), alex()) == []
