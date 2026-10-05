from rdflib import URIRef
from rdflib.namespace import DCTERMS, RDF

from alex_rivera import EVERY_JUDGMENT, INPUT, JDG, PROV, STORY, WEBID, handles, step
from cascade_pod import store

NPX = "http://purl.org/nanopub/x/"
SCRIPTED = {handle: judgment for handle, judgment in EVERY_JUDGMENT.items() if judgment.author == "Alex"}


def scripted(handle):
    return store.parsed(INPUT / "judgments" / f"{handle}.ttl")


def test_alexs_judgments_are_the_scripted_ones_each_a_step_of_its_own_at_its_time():
    assert sorted(path.stem for path in (INPUT / "judgments").glob("*.ttl")) == sorted(SCRIPTED)
    assert [s["name"] for s in STORY["steps"] if "judgment" in s] == sorted(SCRIPTED, key=lambda h: (SCRIPTED[h].at, int(h[1:])))
    for handle, judgment in SCRIPTED.items():
        assert (step(handle)["judgment"], step(handle)["when"]) == (f"scripted-input/judgments/{handle}.ttl", judgment.at)


def test_each_scripted_judgment_is_the_scenarios_verdict_members_used_time_and_reason():
    names = {h: str(term) for h, term in handles().items()}
    for handle, (_, at, _, verdict, members, _, used, replaces, reason) in SCRIPTED.items():
        graph, judgment = scripted(handle), URIRef(names[handle])

        def values(predicate):
            return sorted(str(o) for o in graph.objects(judgment, URIRef(predicate)))

        assert [str(j) for j in graph.subjects(RDF.type, JDG.Judgment)] == [names[handle]], handle
        assert values(PROV + "generatedAtTime") == [at] and values(PROV + "wasAttributedTo") == [WEBID], handle
        assert (URIRef(WEBID), RDF.type, PROV.Person) in graph, handle
        assert values(JDG + "verdict") == ([JDG + verdict] if verdict else []), handle
        assert values(PROV + "hadMember") == sorted(names[m] for m in members), handle
        assert values(PROV + "used") == sorted(names[u] for u in used), handle
        for kind in ("supersedes", "retracts"):
            assert values(NPX + kind) == sorted(names[t] for k, t in replaces if k == kind), handle
        assert (graph.value(judgment, DCTERMS.description) is not None) == reason, handle
        if verdict == "About":
            assert values(JDG + "subject") == [names["S"]] and values(JDG + "basis") == [JDG + "OwnerStatement"], handle

