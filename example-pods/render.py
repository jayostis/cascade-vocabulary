"""Renders a pod in the example layout as a static HTML site: its subject, its views, each entry and each record.

python3 example-pods/render.py <pod folder> --out <directory>
"""

import argparse
import base64
import hashlib
import html
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pyoxigraph

sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
from cascade_pod import derive, vocabulary  # noqa: E402
from cascade_pod.pod import VIEW_FILES, Example  # noqa: E402
from cascade_pod.store import Oxigraph  # noqa: E402

LENS = vocabulary.DEFAULT_LENS
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
XSD_DATE_TIME = "http://www.w3.org/2001/XMLSchema#dateTime"
TRUE = ("literal", "true", "http://www.w3.org/2001/XMLSchema#boolean", None)
REC = "https://ns.cascadeprotocol.org/records/v1-draft#"
MERGED_FROM = "https://ns.cascadeprotocol.org/core/v1#mergedFrom"
SOURCES = {REC + "latestMember": "Latest member", REC + "statusFrom": "Status from", REC + "dateFrom": "Date from"}
NOT_FIELDS = {RDF_TYPE, MERGED_FROM, *SOURCES}
DOCUMENT_PREFIX = "ni:///sha-256;"
CODE_SYSTEMS = {
    "http://snomed.info/sct/": "SNOMED CT",
    "http://www.nlm.nih.gov/research/umls/rxnorm/": "RxNorm",
    "http://hl7.org/fhir/sid/cvx/": "CVX",
    "http://hl7.org/fhir/sid/icd-10-cm/": "ICD-10-CM",
}
STYLE = """
body { font: 16px/1.5 system-ui, sans-serif; margin: 0 auto; max-width: 64rem; padding: 0 1rem 3rem;
       color: #1d2330; background: #fff; }
nav { padding: .75rem 0; border-bottom: 1px solid #d5d9e0; margin-bottom: 1rem; }
nav a { margin-right: 1rem; }
h1 { font-size: 1.5rem; line-height: 1.3; margin: .5rem 0; }
h2 { font-size: 1.15rem; margin: 2rem 0 .5rem; }
a { color: #1a5bb8; }
.kind { color: #5b6475; margin: 0; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; vertical-align: top; padding: .35rem .6rem; border-bottom: 1px solid #e3e6eb;
         overflow-wrap: break-word; }
th { background: #f3f5f8; font-weight: 600; white-space: nowrap; }
h3 { font-size: 1rem; margin: 1.5rem 0 .5rem; padding-top: .75rem; border-top: 1px solid #e3e6eb; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: .25rem 1rem; margin: 0; }
dt { color: #5b6475; }
dd { margin: 0; overflow-wrap: anywhere; }
ul { padding-left: 1.25rem; }
.counts { color: #1f7a3a; font-weight: 600; }
.lapsed { color: #a3401b; font-weight: 600; }
.quiet { color: #5b6475; }
@media (max-width: 40rem) {
  dl { grid-template-columns: 1fr; } dt { margin-top: .5rem; }
  thead { display: none; }
  table, tbody, tr, td { display: block; }
  tr { border-bottom: 1px solid #d5d9e0; padding: .5rem 0; }
  td { border: 0; padding: .15rem 0; }
  td:empty { display: none; }
  td::before { content: attr(data-label); display: block; color: #5b6475; font-size: .85rem; }
}
"""


def page(iri):
    return hashlib.sha256(iri.encode("utf-8")).hexdigest() + ".html"


def local_name(iri):
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def attachment(document):
    if not document.startswith(DOCUMENT_PREFIX):
        return None
    digest = document[len(DOCUMENT_PREFIX):]
    return "attachments/sha-256/" + base64.urlsafe_b64decode(digest + "=" * (-len(digest) % 4)).hex()


def when(text):
    if len(text) < 16 or text[10] != "T":
        return text
    return instant(text).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def instant(text):
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def term_key(term):
    return tuple("" if part is None else part for part in term)


def e(text):
    return html.escape(text, quote=True)


class Pod:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.example = Example(self.folder.parent)
        self.store = derive.build(self.example, "oxigraph", LENS).store
        self.labels = self._labels()
        self.views = {view: self._view(relative) for view, relative in sorted(VIEW_FILES.items())}

    def rows(self, relative):
        found = self.store.select(vocabulary.query(relative))
        return sorted(found, key=lambda row: sorted((k, term_key(v)) for k, v in row.items()))

    def _labels(self):
        terms = Oxigraph()
        vocabulary.load(terms)
        text = vocabulary.query("questions/pod/What everything is called.rq")
        labels = {}
        for source in (terms.select(text), self.store.select(text)):
            for row in sorted(source, key=lambda r: r["label"][1]):
                labels.setdefault(row["thing"], row["label"][1])
        return labels

    def _view(self, relative):
        base = self.example.address + relative
        entries = defaultdict(list)
        convert = Oxigraph()._term
        for triple in pyoxigraph.parse(path=str(self.example.pod / relative), format=pyoxigraph.RdfFormat.TURTLE,
                                       base_iri=base):
            subject = convert(triple.subject)
            if subject != ("iri", base):
                entries[subject[1]].append((triple.predicate.value, convert(triple.object)))
        return {entry: sorted(pairs, key=lambda pair: (pair[0], term_key(pair[1]))) for entry, pairs in entries.items() if any(p == MERGED_FROM for p, _ in pairs)}


class Site:
    def __init__(self, pod):
        self.pod = pod
        self.labels = pod.labels
        self._collect()

    def _collect(self):
        pod = self.pod
        standing = pod.rows("questions/judgment/Whether it counts.rq")
        self.counting = {row["judgment"][1] for row in standing if row.get("counts") == TRUE}
        self.lapsed = defaultdict(set)
        for row in standing:
            if "happened" in row:
                self.lapsed[row["judgment"][1]].add((row["happened"][1], row["by"]))
        self.judgments = defaultdict(lambda: {"members": set(), "supersedes": set(), "retracts": set()})
        for row in pod.rows("questions/judgment/Who judged what.rq"):
            j = self.judgments[row["judgment"][1]]
            for key in ("made", "verdict", "author", "role", "reason"):
                if key in row:
                    j[key] = row[key]
            for key in ("supersedes", "retracts"):
                if key in row:
                    j[key].add(row[key][1])
            if "member" in row:
                j["members"].add(row["member"][1])
        self.naming = defaultdict(set)
        for judgment, j in self.judgments.items():
            for member in j["members"]:
                self.naming[member].add(judgment)

        self.revisions = defaultdict(list)
        self.current = {}
        revisions = {}
        for row in pod.rows("questions/record/Its revisions, in the order they arrived.rq"):
            revision = revisions.get(row["revision"])
            if revision is None:
                revision = revisions[row["revision"]] = {
                    key: row[key] for key in ("record", "revision", "version", "arrived", "previous", "import", "started")
                    if key in row}
                revision["documents"] = defaultdict(lambda: {"retrieved": set(), "hospital": set(), "transmitter": set()})
                self.revisions[row["record"][1]].append(revision)
            if "document" in row:
                held = revision["documents"][row["document"]]
                for key in held:
                    if key in row:
                        held[key].add(row[key])
        for record, rows in self.revisions.items():
            rows.sort(key=lambda r: (instant(r["arrived"][1]), r["revision"][1]))
            currents = [r for r in rows if not any(o.get("previous") == r["revision"] for o in rows)]
            self.current[record] = currents[-1]
        self.content = defaultdict(list)
        for row in pod.rows("questions/record/What each version says.rq"):
            self.content[row["version"][1]].append((row["field"][1], row["value"]))
        self.sources = defaultdict(list)
        for row in pod.rows("questions/entry/Which member each chosen value came from.rq"):
            self.sources[row["entry"][1]].append((row["role"][1], row["record"][1]))
        self.profile_records = defaultdict(set)
        for row in pod.rows("questions/profile/Which records name it.rq"):
            self.profile_records[row["profile"][1]].add(row["record"][1])
        self.not_shown = pod.rows("questions/record/Why it is in no view.rq")
        self.subjects = [row["subject"][1] for row in pod.rows("questions/pod/The person this pod is about.rq")]
        self.counted_profiles = defaultdict(set)
        for row in pod.rows("questions/profile/Whose it is counted as.rq"):
            if row["counts"] != TRUE:
                continue
            hospitals = self.counted_profiles[(row["profile"], row["about"])]
            if "hospital" in row:
                hospitals.add(row["hospital"][1])

        self.entry_view = {}
        self.record_entry = {}
        for view, entries in pod.views.items():
            for entry, pairs in entries.items():
                self.entry_view[entry] = view
                for p, o in pairs:
                    if p == MERGED_FROM:
                        self.record_entry[o[1]] = entry
        profiles = set(self.profile_records) | {profile[1] for profile, _ in self.counted_profiles}
        profiles |= {m for j in self.judgments.values() if j.get("verdict") == ("iri", "https://ns.cascadeprotocol.org/judgments/v1-draft#About") for m in j["members"]}
        self.pages = {}
        for entry in self.entry_view:
            self.pages[entry] = page(entry)
        for record in self.revisions:
            self.pages[record] = page(record)
        for judgment in self.judgments:
            self.pages[judgment] = page(judgment)
        for profile in profiles:
            self.pages[profile] = page(profile)

    # Text

    def label(self, term):
        if isinstance(term, str):
            term = ("iri", term)
        if term in self.labels:
            text = self.labels[term]
            return text[:1].upper() + text[1:]
        if term[0] == "literal":
            return when(term[1]) if term[2] == XSD_DATE_TIME else term[1]
        if term[0] == "iri":
            return local_name(term[1])
        return "unnamed"

    def value(self, term, field):
        if term[0] == "iri" and term not in self.labels and term[1] not in self.pages:
            for prefix, system in CODE_SYSTEMS.items():
                if term[1].startswith(prefix):
                    named = "" if system.lower() in self.label(field).lower() else e(system) + " "
                    return f'{named}<a href="{e(term[1])}">{e(term[1][len(prefix):])}</a>'
            return f'<a href="{e(term[1])}">{e(term[1])}</a>'
        return self.link(term)

    def link(self, term):
        if isinstance(term, str):
            term = ("iri", term)
        text = e(self.label(term))
        if term[0] == "iri" and term[1] in self.pages:
            return f'<a href="{self.pages[term[1]]}">{text}</a>'
        return text

    def standing(self, judgment):
        if judgment in self.counting:
            return '<span class="counts">counts</span>'
        reasons = sorted(self.lapsed.get(judgment, ()), key=lambda r: (r[0], self.label(r[1])))
        if not reasons:
            return '<span class="lapsed">does not count</span>'
        return '<span class="lapsed">does not count</span>: ' + "; ".join(
            f"{e(why)} by {self.link(by)}" for why, by in reasons)

    def made_by(self, judgment):
        j = self.judgments[judgment]
        if "author" in j and j["author"] in self.labels:
            return self.link(j["author"])
        if "role" in j and j["role"] in self.labels:
            return "the " + e(self.labels[j["role"]])
        return self.link(j["author"]) if "author" in j else ""

    # Pieces

    def document(self, title, body, kind=None):
        nav = '<nav><a href="index.html">The pod</a><a href="not-shown.html">Not shown</a></nav>'
        heading = (f'<p class="kind">{e(kind)}</p>' if kind else "") + f"<h1>{e(title)}</h1>"
        return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                f"<title>{e(title)}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n{nav}\n<main>\n"
                f"{heading}\n{body}\n</main>\n</body>\n</html>\n").encode("utf-8")

    @staticmethod
    def table(head, rows, empty):
        if not rows:
            return f'<p class="quiet">{e(empty)}</p>'
        cells = "".join(f"<th>{e(h)}</th>" for h in head)
        body = "\n".join("<tr>" + "".join(f'<td data-label="{e(h)}">{c}</td>' for h, c in zip(head, row)) + "</tr>"
                         for row in rows)
        return f'<div class="scroll"><table>\n<thead><tr>{cells}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table></div>'

    @staticmethod
    def facts(pairs):
        return "<dl>\n" + "\n".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in pairs) + "\n</dl>"

    def judgment_rows(self, judgments):
        rows = []
        def order(judgment):
            made = self.judgments[judgment].get("made")
            return made is None, made and instant(made[1]), self.label(judgment), judgment

        for judgment in sorted(judgments, key=order):
            j = self.judgments[judgment]
            rows.append([self.link(judgment), e(self.label(j["verdict"])) if "verdict" in j else "",
                         e(when(j["made"][1])) if "made" in j else "", self.made_by(judgment), self.standing(judgment)])
        return self.table(["Judgment", "Verdict", "Made", "By", f"Under the {LENS} lens"], rows,
                          "No judgment names it.")

    def view_title(self, view):
        stem = Path(VIEW_FILES[view]).stem.replace("-", " ")
        return stem[:1].upper() + stem[1:]

    def fields(self, pairs):
        return sorted({p for p, _ in pairs if p not in NOT_FIELDS}, key=lambda p: self.label(p))

    @staticmethod
    def hospitals(revision):
        return ", ".join(sorted({h[1] for held in revision["documents"].values() for h in held["hospital"]}))

    def current_content(self, record):
        row = self.current.get(record)
        return set(self.content.get(row["version"][1], ())) if row else set()

    # Pages

    def index(self):
        subjects = "".join(f"<li>{self.link(s)}</li>" for s in sorted(self.subjects, key=self.label))
        profiles = [[self.link(profile), e(", ".join(sorted(hospitals))), self.link(about)]
                    for (profile, about), hospitals in sorted(self.counted_profiles.items(),
                                                              key=lambda p: (self.label(p[0][0]), self.label(p[0][1])))]
        views = [[f'<a href="view-{e(view)}.html">{e(self.view_title(view))}</a>', str(len(entries))]
                 for view, entries in self.pod.views.items()]
        body = (f"<h2>Subject</h2>\n<ul>{subjects}</ul>\n"
                "<h2>Patient profiles counted as theirs</h2>\n"
                + self.table(["Profile", "Hospital", "About judgment"], profiles, "No profile is counted as theirs.")
                + "\n<h2>Views</h2>\n" + self.table(["View", "Entries"], views, "There are no views.")
                + f'\n<h2>Records in no view</h2>\n<p><a href="not-shown.html">Not shown</a>: '
                  f"{len({row['record'] for row in self.not_shown})} records, and why.</p>")
        return self.document("The pod", body, f"The {LENS} lens")

    def view(self, view):
        entries = self.pod.views[view]
        fields = self.fields([pair for pairs in entries.values() for pair in pairs])
        rows = []
        for entry in sorted(entries, key=self.label):
            pairs = entries[entry]
            cells = [self.link(entry)]
            for field in fields:
                cells.append(", ".join(self.value(o, field) for p, o in pairs if p == field))
            cells.append(str(sum(1 for p, _ in pairs if p == MERGED_FROM)))
            rows.append(cells)
        head = ["Entry", *(self.label(f) for f in fields), "Records"]
        return self.document(self.view_title(view), self.table(head, rows, "This view has no entries."), "View")

    def entry(self, entry):
        view = self.entry_view[entry]
        pairs = self.pod.views[view][entry]
        members = sorted((o[1] for p, o in pairs if p == MERGED_FROM), key=self.label)
        holding = {m: self.current_content(m) for m in members}
        rows = []
        for field in self.fields(pairs):
            for p, o in pairs:
                if p == field:
                    carriers = [m for m in members if (field, o) in holding[m]]
                    rows.append([e(self.label(field)), self.value(o, field), "<br>".join(self.link(m) for m in carriers)])
        sources = [[e(SOURCES[role]), self.link(record)]
                   for role, record in sorted(self.sources.get(entry, ()), key=lambda s: (SOURCES[s[0]], s[1]))]
        member_rows = []
        for member in members:
            row = self.current.get(member)
            member_rows.append([self.link(member),
                                e(self.hospitals(row)) if row else "",
                                self.link(row["version"]) if row else "",
                                e(when(row["arrived"][1])) if row else ""])
        judgments = set().union(*(self.naming.get(m, set()) for m in members))
        body = (f'<p>In the view <a href="view-{e(view)}.html">{e(self.view_title(view))}</a>.</p>\n'
                "<h2>Fields</h2>\n" + self.table(["Field", "Value", "Members whose current version has it"], rows,
                                                 "This entry has no fields.")
                + "\n<h2>Chosen from</h2>\n" + self.table(["Choice", "Member"], sources,
                                                          "No field is chosen from one member.")
                + "\n<h2>Members</h2>\n" + self.table(["Record", "Hospital", "Current version", "Last arrived"],
                                                      member_rows, "It has no members.")
                + "\n<h2>Judgments naming its members</h2>\n" + self.judgment_rows(judgments))
        return self.document(self.label(entry), body, "Entry")

    def record(self, record, copied):
        blocks = []
        current = self.current[record]["revision"]
        for row in self.revisions[record]:
            facts = [("Revision", e(self.label(row["revision"])))]
            if "previous" in row:
                facts.append(("Revises", e(self.label(row["previous"]))))
            facts.append(("Version", e(self.label(row["version"]))))
            content = sorted(self.content.get(row["version"][1], ()), key=lambda c: (self.label(c[0]), term_key(c[1])))
            if content:
                facts.append(("Its content", "<ul>" + "".join(
                    f'<li><span class="quiet">{e(self.label(f))}:</span> {self.value(v, f)}</li>' for f, v in content)
                    + "</ul>"))
            for document in sorted(row["documents"], key=term_key):
                held = row["documents"][document]
                path = attachment(document[1])
                text = e(self.label(document))
                if path and (self.pod.folder / path).is_file():
                    copied.add(path)
                    text = f'<a href="{e(path)}">{text}</a>'
                facts.append(("Document", text))
                for key, title in (("hospital", "Hospital"), ("transmitter", "Transmitter")):
                    facts.extend((title, e(value[1])) for value in sorted(held[key], key=term_key))
                facts.extend(("Retrieved", e(when(value[1])))
                             for value in sorted(held["retrieved"], key=lambda v: (instant(v[1]), term_key(v))))
            if "import" in row:
                started = f' <span class="quiet">started {e(when(row["started"][1]))}</span>' if "started" in row else ""
                facts.append(("Import", e(self.label(row["import"])) + started))
            mark = " (current)" if row["revision"] == current else ""
            blocks.append(f"<h3>Arrived {e(when(row['arrived'][1]))}{mark}</h3>\n" + self.facts(facts))
        entry = self.record_entry.get(record)
        if entry:
            shown = f"<p>Shown in {self.link(entry)}.</p>"
        else:
            whys = sorted({row["why"][1] for row in self.not_shown if row["record"][1] == record})
            shown = (f'<p>In no view: {e("; ".join(whys) or "no reason found")}. '
                     'See <a href="not-shown.html">Not shown</a>.</p>')
        body = (shown + "\n<h2>Revisions and their versions, in the order they arrived</h2>\n" + "\n".join(blocks)
                + "\n<h2>Judgments naming it</h2>\n" + self.judgment_rows(self.naming.get(record, ())))
        return self.document(self.label(record), body, "Record")

    def judgment(self, judgment):
        j = self.judgments[judgment]
        facts = [("Verdict", e(self.label(j["verdict"])) if "verdict" in j else ""),
                 ("Made", e(when(j["made"][1])) if "made" in j else ""),
                 ("By", self.made_by(judgment)),
                 (f"Under the {LENS} lens", self.standing(judgment))]
        if "reason" in j:
            facts.append(("Reason given", e(j["reason"][1])))
        for key, title in (("supersedes", "Supersedes"), ("retracts", "Retracts")):
            for other in sorted(j[key], key=self.label):
                facts.append((title, self.link(other)))
        members = [[self.link(m), self.link(self.record_entry[m]) if m in self.record_entry else
                    ('<a href="not-shown.html">not shown</a>' if m in self.revisions else "")]
                   for m in sorted(j["members"], key=self.label)]
        body = (self.facts([(k, v) for k, v in facts if v]) + "\n<h2>Members</h2>\n"
                + self.table(["Member", "Shown in"], members, "It names no member."))
        return self.document(self.label(judgment), body, "Judgment")

    def profile(self, profile):
        records = [[self.link(r), self.link(self.record_entry[r]) if r in self.record_entry
                    else '<a href="not-shown.html">not shown</a>']
                   for r in sorted(self.profile_records.get(profile, ()), key=self.label)]
        body = ("<h2>Judgments naming it</h2>\n" + self.judgment_rows(self.naming.get(profile, ()))
                + "\n<h2>Records whose current version names it</h2>\n"
                + self.table(["Record", "Shown in"], records, "No record names it."))
        return self.document(self.label(profile), body, "Subject" if profile in self.subjects else "Patient profile")

    def not_shown_page(self):
        rows = [[self.link(row["record"]), e(row["why"][1]), self.link(row["because"]) if "because" in row else ""]
                for row in sorted(self.not_shown, key=lambda r: (r["why"][1], self.label(r["record"]),
                                                                  self.label(r.get("because", ("", "")))))]
        return self.document("Not shown", self.table(["Record", "Why", "Because of"], rows,
                                                      "Every record is in a view."), "Records in no view")

    def files(self):
        site = {"index.html": self.index(), "not-shown.html": self.not_shown_page()}
        for view in self.pod.views:
            site[f"view-{view}.html"] = self.view(view)
        copied = set()
        for thing, name in self.pages.items():
            if thing in self.entry_view:
                site[name] = self.entry(thing)
            elif thing in self.revisions:
                site[name] = self.record(thing, copied)
            elif thing in self.judgments:
                site[name] = self.judgment(thing)
            else:
                site[name] = self.profile(thing)
        for path in copied:
            site[path] = (self.pod.folder / path).read_bytes()
        return site


def render(pod_folder, out):
    site = Site(Pod(pod_folder)).files()
    for relative, octets in sorted(site.items()):
        target = Path(out) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(octets)
    return site


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pod", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    site = render(arguments.pod, arguments.out)
    print(f"{len(site)} files written to {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
