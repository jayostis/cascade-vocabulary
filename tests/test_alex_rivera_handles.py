from rdflib.namespace import RDF

from alex_rivera import REC, handles, sources
from cascade_pod.pod import NOT_RDF
from examples import pod_file


def test_every_handle_names_one_thing_in_the_pod_and_every_record_and_profile_there_has_one(alex):
    pod = set()
    for path in alex.files():
        if not path.startswith(NOT_RDF):
            pod |= set(pod_file(alex, path))
    named = handles()
    assert len(set(named.values())) == len(named)
    assert sorted(h for h, thing in named.items() if not any(thing in triple for triple in pod)) == []
    records = {o for _, p, o in pod if p == REC.revisionOf}
    subjects = {s for s, p, o in pod if p == RDF.type and o == REC.Subject}
    profiles = {o for _, p, o in pod if p == REC.patient} - subjects
    assert records | profiles == {named[h] for kind in ("records", "profiles") for h in sources()[kind]}
