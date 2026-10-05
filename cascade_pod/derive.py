"""Runs derivations, in order, over a store holding a pod."""

from dataclasses import dataclass

from . import vocabulary

DERIVED = "urn:cascade:derived:"


def run(store, derivations):
    """Runs each derivation in turn, adding its triples to the store, and returns the triples each added by its path."""
    held, added = store.triples(), {}
    for relative in derivations:
        added[relative] = store.construct(vocabulary.query(relative)) - held
        store.add(added[relative])
        held |= added[relative]
    return added


@dataclass(frozen=True)
class Derived:
    added_by_step: dict

    @property
    def triples(self):
        return set().union(*self.added_by_step.values())


def derive(store, lens):
    """Adds the lens's derived state to the store, as a graph of its own, and returns it."""
    derived = Derived(run(store, vocabulary.derivations(lens)))
    store.add(derived.triples, DERIVED + lens)
    return derived
