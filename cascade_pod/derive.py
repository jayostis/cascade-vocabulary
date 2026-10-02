"""Runs a lens: its derivations, in order, over a store holding a pod."""

from . import vocabulary

DERIVED = "urn:cascade:derived:"


def steps(store, lens):
    """Runs each derivation in turn, adding its triples to the store, and yields its path with the triples it added."""
    held = store.triples()
    for relative in vocabulary.derivations(lens):
        added = store.construct(vocabulary.query(relative)) - held
        store.add(added)
        held |= added
        yield relative, added


def derive(store, lens):
    """Adds the lens's derived state to the store, as a graph of its own, and returns it."""
    derived = set().union(*(added for _, added in steps(store, lens)))
    store.add(derived, DERIVED + lens)
    return derived
