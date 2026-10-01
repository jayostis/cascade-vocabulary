"""Runs a lens: its derivations, in order, over a store holding a pod."""

from . import vocabulary

DERIVED = "urn:cascade:derived:"


def derive(store, lens):
    """Adds the lens's derived state to the store, as a graph of its own, and returns it."""
    held = store.triples()
    for relative in vocabulary.derivations(lens):
        store.add(store.construct(vocabulary.query(relative)))
    derived = store.triples() - held
    store.add(derived, DERIVED + lens)
    return derived
