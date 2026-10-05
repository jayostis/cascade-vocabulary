"""The Cascade matcher: writes a Same wherever a rule of the current rule list joins two of the subject's records. It
reads the pod's triples, their derived state under the everyday lens and the current version of each table, and runs
the comparison query each rule names; which records it takes, in what order, and what it writes are its own."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS

from . import Failure, derive, names, store, turtle, vocabulary
from .pod import LAYOUT, save, stem
from .store import ENGINES, date_time
from .turtle import JDG, NPX, PAV, PROV, REC

MATCHER = URIRef("urn:uuid:80bcb9f7-34ae-432b-bd78-ba2616a81f76")
LENS = "everyday"
COMPARISONS = "matcher"


def judgment(name, *, at, members, justification, used):
    same = URIRef(name)
    return {(same, RDF.type, JDG.Judgment), (same, JDG.verdict, JDG.Same), (same, JDG.justification, justification),
            *((same, PROV.hadMember, URIRef(m)) for m in members), *((same, PROV.used, URIRef(u)) for u in used),
            (same, PROV.wasAttributedTo, MATCHER), (same, PROV.generatedAtTime, date_time(at)),
            (MATCHER, RDF.type, PROV.SoftwareAgent), (MATCHER, RDFS.label, Literal("Cascade matcher"))}


@dataclass(frozen=True)
class Rule:
    justification: URIRef
    applies_to: frozenset
    query: str
    table: URIRef | None


def rules(rows):
    """The rules a version of the rule list holds, each checked to name a comparison under matcher/ whose bytes hash to
    the rule's hash."""
    found = []
    for row in rows.subjects(RDF.type, REC.MatcherRule):
        def one(predicate):
            values = list(rows.objects(row, predicate))
            if len(values) != 1:
                raise Failure(f"a rule of the rule list gives {len(values)} {predicate}, not one")
            return values[0]

        justification, query, expected = one(REC.justifiedAs), str(one(REC.query)), str(one(REC.queryHash))
        path = PurePosixPath(query)
        if path.is_absolute() or path.parts[:1] != (COMPARISONS,) or ".." in path.parts:
            raise Failure(f"the rule for {justification} names {query}, which is not under {COMPARISONS}/")
        file = vocabulary.QUERIES / query
        if not file.is_file() or names.document(file.read_bytes()) != expected:
            raise Failure(f"{query} does not hash to {expected}, as the rule for {justification} says it does")
        tables = list(rows.objects(row, REC.table))
        if len(tables) > 1:
            raise Failure(f"the rule for {justification} reads {len(tables)} tables, not one")
        found.append(Rule(justification, frozenset(str(kind) for kind in rows.objects(row, REC.appliesTo)), query,
                          tables[0] if tables else None))
    if len({rule.justification for rule in found}) != len(found):
        raise Failure("two rules of the rule list give one justification")
    return sorted(found, key=lambda rule: str(rule.justification))


class References:
    """A folder of reference tables: references.ttl, the index of each series and its versions, and one file per
    version holding its rows, named from the version's name."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.index = store.parsed(self.folder / "references.ttl")

    def description(self, thing):
        """What the index states about a series or one of its versions, less the version a series ships with."""
        return {triple for triple in self.index.triples((URIRef(thing), None, None)) if triple[1] != REC.shipsWith}

    def is_version(self, name):
        return (URIRef(name), PROV.specializationOf, None) in self.index

    def rows(self, version):
        file = self.folder / f"{stem(str(version))}.ttl"
        if not file.is_file():
            raise Failure(f"{self.folder} holds no rows for {version}")
        return store.parsed(file)

    def rule_list(self):
        """The one series whose versions hold the matcher's rules."""
        found = {series for series in self.index.subjects(RDF.type, REC.ReferenceSeries)
                 if any((None, RDF.type, REC.MatcherRule) in self.rows(version)
                        for version in self.index.subjects(PROV.specializationOf, series))}
        if len(found) != 1:
            raise Failure(f"{self.folder} holds {len(found)} rule lists, not one")
        return found.pop()

    def current(self, series, pod):
        """The version of the series the pod names as current, and otherwise the one it ships with."""
        label = self.index.value(series, RDFS.label) or series
        current = list(pod.objects(series, PAV.hasCurrentVersion))
        if not current:
            shipped = self.index.value(series, REC.shipsWith)
            if shipped is None or (shipped, PROV.specializationOf, series) not in self.index:
                raise Failure(f"{label} ships with {shipped}, a version it does not list")
            return shipped
        if len(current) != 1 or (current[0], PROV.specializationOf, series) not in self.index:
            raise Failure(f"the pod holds no one current version the matcher knows of {label}")
        return current[0]


@dataclass(frozen=True)
class Record:
    name: URIRef
    kind: str
    version: URIRef
    arrived: tuple
    activity: URIRef


def arrival(moment):
    """A time's place in time order: its seconds in UTC, then the digits of any fraction of a second."""
    whole, _, fraction = names.in_utc(str(moment))[:-1].partition(".")
    return whole, fraction


class Matcher:
    def __init__(self, pod, references, at, address, engine):
        """`pod` is the pod's triples, `references` its reference tables, `at` the run's time and `address` the pod's
        root; the comparisons run on `engine`."""
        self.references, self.at, self.address = references, at, address
        held = ENGINES[engine]()
        held.add(pod)
        derive.derive(held, LENS)
        self.graph = Graph()
        for triple in held.triples():
            self.graph.add(triple)
        self.rules_version = references.current(references.rule_list(), self.graph)
        self.rules = rules(references.rows(self.rules_version))
        self.table_versions = {rule.table: references.current(rule.table, self.graph)
                               for rule in self.rules if rule.table is not None}
        for version in set(self.table_versions.values()):
            held.add(references.rows(version))
        self.matched = {rule.justification: {(row["record"], row["other"])
                                             for row in held.select(vocabulary.query(rule.query))}
                        for rule in self.rules}
        self.theirs = self._theirs()
        self.files = {}

    def _subject(self):
        subjects = set(self.graph.subjects(RDF.type, REC.Subject))
        if len(subjects) != 1:
            raise Failure(f"the pod holds {len(subjects)} subjects, not one")
        return subjects.pop()

    def _theirs(self):
        """The subject's records, by name."""
        g, subject, theirs = self.graph, self._subject(), {}
        for record in set(g.subjects(REC.subject, subject)):
            first = [r for r in g.subjects(REC.revisionOf, record) if g.value(r, PROV.wasRevisionOf) is None]
            version = g.value(record, PAV.hasCurrentVersion)
            if len(first) != 1 or version is None:
                raise Failure(f"{record} has no one first revision and current version")
            theirs[record] = Record(name=record, kind=str(g.value(record, REC.kind)), version=version,
                                    arrived=arrival(g.value(first[0], PROV.generatedAtTime)),
                                    activity=g.value(first[0], PROV.wasGeneratedBy))
        return theirs

    def holds(self, name):
        return (URIRef(name), None, None) in self.graph

    def replaced(self, judgment):
        return any(True for p in (NPX.supersedes, NPX.retracts) for _ in self.graph.subjects(p, judgment))

    def file(self, path, triples):
        self.files[path] = turtle.write(triples, self.address + path)

    def matches(self, rule, record, other):
        return record.kind in rule.applies_to and (record.name, other.name) in self.matched[rule.justification]

    def same(self, rule, members):
        applied = [self.rules_version] + ([self.table_versions[rule.table]] if rule.table is not None else [])
        used = sorted({str(v) for v in applied} | {str(m.version) for m in members})
        member_names = sorted(str(m.name) for m in members)
        name = names.record([str(MATCHER), str(rule.justification), *member_names, *used])
        if self.holds(name):
            return
        self.file(LAYOUT.place(JDG.Judgment).path(name),
                  judgment(name, at=self.at, members=member_names, justification=rule.justification, used=used))
        place = LAYOUT.place(REC.ReferenceSeries)
        for version in applied:
            series = self.references.index.value(version, PROV.specializationOf)
            for thing, path in ((series, place.path(series)), (version, LAYOUT.version(place, version))):
                if not self.holds(thing):
                    self.file(path, self.references.description(thing))

    def take(self, activity):
        """Files a judgment for each of the subject's records whose first revision `activity` generated, compared with
        her other records, and returns the files by path."""
        taken = sorted((r for r in self.theirs.values() if activity is not None and r.activity == URIRef(activity)),
                       key=lambda r: (r.arrived, str(r.name)))
        compared = [r for r in self.theirs.values() if r not in taken]
        for record in taken:
            for rule in self.rules:
                matched = [other for other in compared if self.matches(rule, record, other)]
                if matched:
                    self.same(rule, [record, *matched])
            compared.append(record)
        return self.files

    def recheck(self):
        """Files a judgment again for each of the matcher's Sames that used a since-revised table and still joins at
        least two of its members, and returns the files by path."""
        g = self.graph
        revised = {o for o in g.objects(None, PROV.wasRevisionOf) if self.references.is_version(o)}
        by_justification = {rule.justification: rule for rule in self.rules}
        for judged in sorted(set(g.subjects(PROV.wasAttributedTo, MATCHER)), key=str):
            if g.value(judged, JDG.verdict) != JDG.Same or self.replaced(judged):
                continue
            if not revised & set(g.objects(judged, PROV.used)):
                continue
            rule = by_justification.get(g.value(judged, JDG.justification))
            if rule is None:
                raise Failure(f"the rule list has no rule for {g.value(judged, JDG.justification)}, which {judged} gives")
            members = [self.theirs[m] for m in sorted(g.objects(judged, PROV.hadMember), key=str) if m in self.theirs]
            still = [m for m in members if any(self.matches(rule, m, o) for o in members if o is not m)]
            if len(still) >= 2:
                self.same(rule, still)
        return self.files


def run(example, read_through, takes, at, out, engine):
    pod = example.story_store(engine, read_through).triples()
    matcher = Matcher(pod, References(example.folder / "references"), at, example.address, engine)
    save(matcher.take(example.activity(takes)) if takes else matcher.recheck(), out)
    return 0
