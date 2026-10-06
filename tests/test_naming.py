"""Every name a feature file writes beside its inputs is the record rule over those inputs, as cascade-bridge-spec's
engine/sparql.md words it: the first 128 bits of SHA-256("90c60849-c5ef-4ca6-bfb8-8662bd07d2b5|" and the inputs joined
by "|"), as a version 8 UUID."""

import hashlib

from gherkin.parser import Parser

from contract import ROOT


def record_name(inputs):
    digest = hashlib.sha256(("90c60849-c5ef-4ca6-bfb8-8662bd07d2b5|" + "|".join(inputs)).encode()).hexdigest()
    return (f"urn:uuid:{digest[0:8]}-{digest[8:12]}-8{digest[13:16]}-"
            f"{'89ab'[int(digest[16], 16) % 4]}{digest[17:20]}-{digest[20:32]}")


def named():
    for path in sorted([*ROOT.glob("runtime/*.feature"), *ROOT.glob("conformance/*/*.feature")]):
        document = Parser().parse(path.read_text(encoding="utf-8"))
        for child in document["feature"]["children"]:
            for inner in child.get("rule", {}).get("children", [child]):
                for step in inner.get("scenario", {}).get("steps", []):
                    header, *rows = [[cell["value"] for cell in row["cells"]]
                                     for row in step.get("dataTable", {}).get("rows", [])] or [[]]
                    if {"inputs", "name"} <= set(header):
                        yield from ((row[header.index("inputs")], row[header.index("name")]) for row in rows)


def test_every_name_written_beside_its_inputs_is_the_record_rule_over_them():
    pairs = list(named())
    assert len(pairs) >= 13
    assert [(inputs, name) for inputs, name in pairs if record_name(inputs.split(", ")) != name] == []
