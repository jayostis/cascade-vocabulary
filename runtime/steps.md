# Steps

Every step a runtime implements to run the feature files: [the rules](.) under `runtime/` and each kit under
[`conformance/`](../conformance). A feature file uses no step this document does not list, and a runtime implements each
once. Phrases are written as [Cucumber Expressions](https://github.com/cucumber/cucumber-expressions): `{...}` is one of
the parameters below, `(s)` is optional text and `a/b` is either word.

## How an example runs

An example's `Given` and `When` steps happen in order, its `Background`'s first, to a pod that the first of them
creates. Its `Then` steps read the pod as it stood after the last of them, under the `everyday` lens, unless a step
reads it at another point.

**Writers.** The pod has one writer, the first, until `a second writer of the pod` starts another. Each `Given` and
`When` step is taken by one writer: the first until a step names another, and then the writer the last such step
named. A `Then` reads the pod as the writer that took the step read at holds it.

A `Given` or `When` step may end with a label in parentheses, `(E13)`, which names it. Otherwise a step is named by the
name it quotes: an import by its export's, its download's or its pull's, a download's extension kept, an entry or a
judgment by its file's, an open by its tables folder's. The pod's creation, a reference version's arrival, a matcher run and a recheck are named `pod`,
`reference`, `matcher` and `recheck`, a second writer's start `writer` and a writer's receiving of files `sync`. Two steps of one example never share a name: where they would, the later is
labelled. A name is letters, digits, `-`, `_` and `.`, so that `urn:cascade:step:NAME` below is an IRI.

**The dataset a `Then` reads** is the one each step has always been read against. Each file of the pod is a named
graph, named by the pod's address plus its path. The lens's derived state is the graph `urn:cascade:derived:<lens>`,
and the files built from that state, the views, the labels, the type index and `manifest.ttl`, are graphs too. The
pod's layout, [`pod-layout.ttl`](pod-layout.ttl) read with the pod's address as its base, is the graph
`urn:cascade:pod-layout`. The default graph is the union of all of these. One more graph, `urn:cascade:steps`, outside
the default graph, lists what each step wrote, up to the one read at: `<urn:cascade:step:NAME> prov:generated <file>`,
each file new to the pod, `attachments/` included. A file that arrived from another writer is listed under the step
that wrote it there, never under the step that received it.

The dataset also holds the story's tables. At a read point, the version of each series current then (the tables of the
last `open` step that was not refused, from that step on, else `references/`: its shipped versions and those that have
arrived) is a named graph of its rows, named by the version's IRI, **outside** the default graph. The descriptions of
those versions and their series, as the matcher reads them (M13), are the graph `urn:cascade:references`, which is
**in** the default graph. Every series has its current version here, the rule list and the names included, read the way
the matcher reads them, so a published query reads in an example as it does in an app. A series is left out when the
pod names several current versions of it (a read refuses nothing, where the matcher refuses the step) and when the
pod's current version is not one the folder holds.

**Scripted input** is in the folder `scripted-input/<person>/` beside the feature file, the person's name in lower case,
and `scripted-input/people.ttl` gives each person's subject (`foaf:name`) and pod (`pim:storage`):

| Folder | What it holds |
|---|---|
| `downloads/<export>/apple_health_export/` | an Apple Health export, as the phone writes it |
| `downloads/<file>` | a file the person downloaded, as a patient portal hands it out |
| `downloads/<pull>/` | a pull from a hospital's FHIR API, saved as two files: `bundle.json`, a FHIR R4 Bundle, and `pull.json`, a JSON object whose `fhirBase` is the hospital's FHIR base. The rest of `pull.json`, and what the import states with the Bundle, are the runtime's |
| `bridge/<step>/<file stem>/graph.ttl`, `findings.ttl` | the Bridge's saved output for each document an import step converts, in a folder named as the step, because a conversion carries its import's start; `unaccepted.txt` instead for a document no adapter accepted |
| `entries/<entry>.ttl` | an entry: its session, the `urn:uuid:` the app minted for it once, and its drafts `urn:cascade:output-N`, with their versions |
| `judgments/<judgment>.ttl` | one judgment a person makes, under the IRI it keeps |
| `references/` | the matcher's reference tables, below |
| `tables/<name>/` | the tables an open step gives the pod, laid out as `references/` |

The runtime gives each import a new random UUID on every run, keeps each entry session's IRI, and gives the session the
step's time. A step that is refused writes nothing, and the example goes on. The Bridge output saved for a rule's
example and for a kit is the Bridge's own, regenerated by the Bridge and the adapters, except four hand-made inputs
that no Bridge produces, each a named failure fixture a regeneration must put back: `finn/bridge/stray-statement/`
holds a statement about nothing (`<urn:example:stray>`), for A14's refused graph; `finn/bridge/type-filed-nowhere/`
types its record `cascade:NoSuchRecord`, for A14's record of a type the pod files nowhere;
`finn/bridge/import-disagreement/AllergyIntolerance-disagreeing/` describes its import as "Another export", for A14's
import whose documents disagree; `ada/bridge/current-version-again/` holds a finding the adapter does not raise, for
A10's document kept for its findings. A document no adapter accepted is saved as `bridge/<step>/<file stem>/unaccepted.txt`,
saying why; a document an import must convert and has no saved output for is the example's error, not a refusal.

**The matcher's reference tables** are `references/` until an open step names other tables, in Turtle:

- **`references.ttl`**, the index: each `cascade:ReferenceSeries` with its `rdfs:label`, the one `cascade:TableKind` its
  versions are (`cascade:tableKind`), if it is a table, and the version it `cascade:defaultTableVersion`, and each version, a
  `prov:Entity`, with its `prov:specializationOf` series, its `pav:version` and the version it `prov:wasRevisionOf`, if
  any. A version's description in the pod, and the file a reference step files, are what the index states about the
  series and the version, less `cascade:defaultTableVersion`.
- **One file per version, holding its rows,** named from the version's name by N9. Each row conforms to its kind's
  `cascade:rowShape` in `records.shapes.ttl` and holds no blank node: a mapping row is an `owl:Axiom` named by N11 with
  its `owl:annotatedSource`, `owl:annotatedProperty`, `owl:annotatedTarget` and `sssom:mapping_justification` (a panel
  member row also holds its `cascade:panelSequence` and at most one `cascade:observationRequiredInPanel`). A
  version with no rows is a file with no triples.
- **The rule list is not a table.** Each row is a `cascade:RuleListRow` giving the matcher rule it runs (`cascade:matcherRule`),
  its justification (`cascade:justifiedAs`), each class of record it applies to (`cascade:appliesToClass`), its comparison
  query as a path under
  `queries/` (`cascade:queryPath`), N5's name for that file's bytes (`cascade:queryHash`), and the kind of table the query
  reads, if any (`cascade:tableKind`). A matcher claim cites its rule (`cascade:matcherRule`), and its assertion names the
  rule list's version, whose row for the rule says which query ran, by its bytes. A rule list version's description in
  the pod also describes each of its rows, `<version>#<rule's local name>`, with its rule and query hash (M8). A tables folder an `open` step
  names may list a version of the vocabulary's rule list (`runtime/rule-list/`) without holding its file: the rows are
  those of the file of that name there, unless the folder holds a file of its own. A person's `references/` folder holds
  every file it lists.

The rows of each current version of a kind a rule reads are loaded into the graph named by the version's IRI, and the
descriptions of those versions and their series into the default graph the matcher's queries read (M13). A query reads
rows only inside `GRAPH ?origin`. No other version's rows are loaded, and rows are never written to the pod. The rule
list's rows are `[] a cascade:RuleListRow`: no row shape and no N12 cover them.

## Parameters

| Parameter | Matches | Written | Means |
|---|---|---|---|
| `{person}` | `[A-Z][a-z]+` | `Ada` | a person `people.ttl` names: the pod's subject |
| `{time}` | `\d{4}-\d{2}-\d{2} at \d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?` | `2026-01-02 at 10:00`, `2026-09-01 at 10:00:04` | a time in UTC |
| `{name}` | `"[^"]*"` | `"first-export"` | a name in quotes: of a step, a file or a series |
| `{step}` | `that step\|that import\|that entry\|"[^"]*"` | `that step`, `that import`, `that entry`, `"E13"` | the last step before this one, or, in a `Then`, the last step the pod is read after; the last import or entry of those; the step of that name |
| `{steps}` | `that step\|"[^"]*"(?:(?:, \|, and \| and \|, or \| or )"[^"]*")*` | `"E15" and "M8"` | steps by name, joined by `,`, `and` or `or` |
| `{record}`, `{records}` | `(?:[^:]\|:(?=\S))+` | `allergy RxNorm 1191 "Ecotrin"`, `H1-ALG-PCN`, `variant HGVS NM_000249.4:c.2042C>T` | records in words, below; several joined by `,` and `and`; a colon is part of the words when a non-space follows it, and the colon ending a step is not |
| `{judgment}` | `(?:[^:]\|:(?=\S))+` | `J21`, `the matcher's same code of H2O-ALG-SULFA and H1-ALG-SULFA` | a judgment in words, below |
| `{view}` | `allergies\|conditions\|immunizations\|procedures\|medications\|lab-results\|patient-profile\|variants\|variant-interpretations` | `allergies` | a view |
| `{lens}` | `[a-z]+` | `export` | a lens under `queries/lenses/` |
| `{count}` | `no file\|1 file\|\d+ files` | `no file`, `1 file`, `3 files` | how many files |
| `{writer}` | `the first writer\|the second writer` | `the second writer` | a writer of the pod: the first, which created it, or the second |

A parameter matches the regular expression beside it, each `\|` written so in the table being an alternation. A time in
a table is written the same way, with or without its `at`.

### Things in words

A record is named by what a person reads in it, never by its IRI, except where a naming rule's example shows the IRI:

- **`<kind> <system> <code> "<name>"`**, as `allergy RxNorm 1191 "Ecotrin"`, with the code, the name or both: the
  record of that kind whose version gives them. The kinds are `allergy`, `condition`, `immunization`, `procedure`,
  `medication`, `lab result`, `variant` and `variant interpretation`; the systems `SNOMED` (an `http://snomed.info/id/` IRI, or a `cascade:snomedCode`),
  `RxNorm` (an `https://ns.cascadeprotocol.org/codes/rxnorm/` IRI), `NDC` (an
  `https://ns.cascadeprotocol.org/codes/ndc11/` IRI, a medication's `cascade:ndcCode`), `ICD-10-CM` (an
  `https://ns.cascadeprotocol.org/codes/icd10cm/` IRI), `LOINC` (an `http://loinc.org/rdf/` IRI) and `CVX`
  (a `cascade:vaccineCode`), `HGVS` (a variant's `cascade:hgvsCodingDnaExpression`, the expression as written, as in
  `variant HGVS NM_000249.4:c.2042C>T`) and `ClinVar` (a variant's `cascade:clinvarVariationId`, the digits, as in
  `variant ClinVar 90011`); the name is the version's allergen, condition, vaccine, procedure, drug or test name, or a
  variant's HGVS expression. A `variant interpretation` has neither a code nor a name, so no step names one: a step
  names the variant it interprets, and the interpretation is read by its place in the view. Each
  draft of an entry has a name of its own, so no record is named by its position.
- **`… from <source>`**, where two imported records share code and name: `from codeine-1` is the record whose
  `cascade:sourceRecordId` the export gave as `codeine-1`. A variant has no such term, so it is never named so.
- **A handle** a kit's `expected/handles.json` gives, as `H1-ALG-PCN`: the record or profile it names by the inputs of
  the rule that names it (`naming.feature`, N1 and N2): by its server, type and ID (`cascade:sourceUrl`); by its entry's
  file and the draft's position; by its `document` and `selector`, the `rdf:value` of its selector, RFC 6901's fragment
  form for a JSON document and the XPath for an XML one, for a FHIR record with no `id` or a `urn:uuid:` `fullUrl`, and
  for a C-CDA entry whose id its document repeats with other content, and for every record of a C-CDA document that
  states no custodian id or not exactly one patient with an id; a C-CDA record with an id by its `document`, whose
  custodian and patient ids scope it, and its `identifier`, `root:extension` or the root alone; one with no id by its
  `document`, its `class` and its `key`, a list of `field=value` strings whose fingerprint its name takes, or, with no
  key, its `members`, a list of member strings.
- **A person's name**, as `Alex`: the pod's subject.
- **`the runtime`**: the runtime replaying the example, named as N7 says, which every act it performs is
  `prov:wasAssociatedWith`.

Each names exactly one thing in the pod, or the step fails.

A judgment a person makes is named by its handle in a kit (`J21`) or by its file's name (`"retract-b"`). A matcher
judgment is named `the matcher's <justification> of <records>`, the justification in words: `same code`,
`same code and date`, `same mapped code`, `same mapped code and date`, `same medication code`, `same result`,
`same converted code`, `same code and period`, `same brand generic`, `same product code`, `same variation` or
`same variation through the table`. A
reference series is named by its `rdfs:label` in `references/` or any of the person's `tables/` folders, one series per label, and a version `<label> version <version>`, as `SNOMED CT to RxNorm ingredient map version 2`. A version of
a record is `version N of <record>`, where the record's versions are numbered from 1 in the order its revisions first
name them, and a document `the document of <record>`, the one its first revision is derived from, or `the document "<path>"`, the file at that path under the person's `downloads/`, named by N5. An entry of a view is
`the entry of <record>`: the entry, in the views of the lens read at, that holds the record (`cascade:mergedFrom`).
Exactly one entry must hold it, or the example is in error.

The matcher is `https://ns.cascadeprotocol.org/cascade#CascadeMatcher`, a `prov:SoftwareAgent` labelled `Cascade matcher`.

## Given and When

Each of these says something happened. A step may be written as `Given`, `When` or `And`.

### `a new pod for {person} on {time}`

The pod is created, at the address `people.ttl` gives the person, with the person as its subject. Every example starts
with this step, or a background that does.

### `the export {name} is imported on {time}`

The person imports the Apple Health export `downloads/<name>/apple_health_export/`. The Bridge's saved output for each
document it converts is in `bridge/<step>/`.

### `the download {name} is imported on {time}`

The person imports the file `downloads/<name>`, as they downloaded it. The first importer `cascade-runtime.json` names
that recognises the file as its kind takes it. The Bridge's saved output for each document it converts is in `bridge/<step>/`.

### `the pull {name} is imported on {time}`

The person imports the pull saved in the folder `downloads/<name>/`, their record as an app pulled it from a hospital's
FHIR API. The first importer `cascade-runtime.json` names that recognises the folder as its kind takes it. The import's
one document is `bundle.json`, and `pull.json` is none. The Bridge's saved output for each document it converts is in
`bridge/<step>/`.

### `{person} enters {name} on {time}`

The person makes the entry `entries/<name>.ttl`.

### `{person} files the judgment {name} on {time}`

The person makes the judgment `judgments/<name>.ttl`.

### `version {name} of {name} arrives on {time}`

A reference version arrives: the version so numbered of the series so labelled, as `references.ttl` describes it.

### `the matcher runs on the records of {step} on {time}`

The matcher runs, taking the records whose first revision came from that step's import or entry session, or, for a
step that received files, from an act its sync names (M1).

### `the matcher rechecks on {time}`

The matcher runs with no step's records: a recheck.

### `the pod is opened with the tables {name} on {time}`

An app opens the pod with the tables in `tables/<name>/` (O1, O2). They are the story's tables from this step on.

### `a second writer of the pod`

A second writer of the pod starts, holding a copy of every file the pod holds as it stands and no snapshot of its own:
a new writer (N14). It writes nothing, and the steps after it are still taken by the writer that took the step before.

### `the steps that follow are {writer}'s`

The steps after this one are taken by that writer. It changes nothing.

### `{writer} receives the files of {writer} on {time}`

The first writer named is given every file the second holds in a folder the layout gives by `solid:instanceContainer`,
the views' folder aside, writes each it lacks, and writes a sync if `sync.feature` says it does. The steps after it are
the receiving writer's.

### `the pod is read as it stood after {step}`, `the pod is read as it stood after {step}, under the {lens} lens`

The `Then` steps that follow read the pod as it stood after that step, under that lens, `everyday` if none is named.
It changes nothing.

### `the query is:`

The SPARQL `SELECT` query in the DocString beneath it is the one the next `it answers` step asks. It changes nothing: the step is written `When`, as the read point is.

### `the query {name} is asked`

The SPARQL `SELECT` query in the file at that path under `queries/` is the one the next `it answers` step asks,
as the file holds it. It changes nothing: the step is written `When`, as the read point is.

## Then

Each of these reads the dataset. A table's first row names its columns, and a column a step lists as optional may be
left out; a cell left empty means there is no value, and a table of its first row alone means there are none.

### `{steps} wrote {count}`

Those steps each wrote that many files new to the pod.

### `that step is refused`

The step the example took last was refused.

### `the pod holds no revision`

No graph holds a `cascade:Revision`.

### `no file that {steps} wrote names {record}`

No file those steps wrote has the record as a subject or an object.

### `the pod neither names nor stores the document {name}`

The file at that path under the person's `downloads/`, as a document named by N5, is in no graph, and no step wrote its
bytes.

### `{record} has these revisions:`, `the records have these revisions:`

| record | arrived | version | <field> | after |
|---|---|---|---|---|

The record's revisions, or those of every record the table names, are exactly these: when each arrived (its
`prov:generatedAtTime`), the number of the version it sets, and when the revision it follows arrived. Any other column
names a field of the version, in words (`verification status` for any property whose local name is
`verificationStatus`), and each cell is that field's values, joined by `,`, in the version that row's revision sets:
so a revision that sets the wrong content fails, not only one that reuses the wrong version.

### `these records have:`

| record | field | value |
|---|---|---|

For each record and field the table names, the record has exactly these values. The fields are `kind`; `version`, the
number of its current version; `subject`, the person whose record the lens says it is; and, of its current version,
`criticality`, `patient` and `influenced by`.

### `the matcher's judgments holding {records} are:`

| justification | members | asserted under | used | inputs | name |
|---|---|---|---|---|---|

The matcher's judgments with any of those records as a member are exactly these. Each is a claim: a `cascade:Same` with
that justification and exactly those members, attributed to the matcher. `asserted under` (optional) is each rule list
version an assertion of it names (`cascade:assertedUnderRuleListVersion`), in words; `used` (optional) everything it
`prov:used`, in words; `inputs` (optional) the rule first and then the inputs N6 names
it from, joined by `, `, a list in parentheses: `cascade:ClaimNamingRule`, the maker `cascade:CascadeMatcher`, the
matcher rule term, the justification, `(` its members `)` and `(` what it used `)`, each the IRI the pod holds (`cascade:`
stands for the namespace); `name` (optional) its IRI. Every column but `name` is checked first, so an input the pod does not
hold and a name the inputs do not give fail apart.

### `the matcher has no judgment holding {records}`

No matcher judgment has any of those records as a member.

### `{step} wrote these matcher judgments:`

| justification | members | asserted under | used | inputs | name |
|---|---|---|---|---|---|

The claims the step asserted, writing an assertion of each, are exactly these, each as the step before says, whether or
not the step wrote the claim itself (M9). Every claim the step wrote it asserted, and holds only what N6 names it from;
every other subject in the files the step wrote is an assertion of one of these, the matcher, described as above, a
reference series or version, or, in the run's own file, the run, its snapshot or the runtime (N7, N14).

### `{step} wrote these reference descriptions:`

| reference |
|---|

The reference series and versions the files the step wrote describe are exactly these, each as `references.ttl` does,
and each version of a rule list with its rows as well (M8).

### `{judgment} counts`, `{judgment} does not count`

Whether the judgment has `cascade:countsUnderLens true` under the lens.

### `{judgment} has lapsed`, `{judgment} has not lapsed`

Whether the judgment has `cascade:lapsed true` under the lens.

### `the {view} view holds these entries:`

| members |
|---|

The entries of the view that hold any record the table names are exactly these, each with exactly those members
(`cascade:mergedFrom`).

### `the {view} view has no entry`

The view holds no entry.

### `the entry of {record} shows:`, `the entry of {record} shows only:`

| field | value |
|---|---|

The entry holding the record has, for each field the table names, exactly these values; with `only`, it states nothing
else but its members. The fields are `type`, `status`, `criticality`, `abatement date`, `status from` and
`latest member`.

### `{records} is/are in no view`

No view holds the record, or any of the records.

### `these records are in no view, for these reasons:`

| record | reason | because |
|---|---|---|

No view holds the record, and it is left out for exactly that reason (`cascade:leftOutFor`), in words, `because` of that
thing.

### `these are named:`

| thing | inputs | name |
|---|---|---|

Each thing, in words, has exactly that IRI. An example showing how things are named uses this step, as the naming rules
and P19 do. `inputs` (optional) are the rule that names it and then its inputs in the rule's order, joined by `, `, a
list in parentheses and `cascade:` standing for the namespace: for a record from a server
`cascade:RecordFromServerNamingRule`, the base URL, the resource type and the id; for a record an entry made
`cascade:EnteredRecordNamingRule`, the entry's session IRI, which the record's first revision must hold, and the draft's
position, which reaches the pod only through the name. `tests/test_naming.py` checks every such cell against
`tests/naming.py`.

### `that step's import is named by a new random UUID`

The step wrote one import, and its IRI is a version 4 `urn:uuid:`.

### `it answers:`, `it answers nothing`

The query gives exactly these rows as a multiset, or none. A cell is a
Turtle term (`<iri>`, a prefixed name, `"text"`, `"2026-01-02"^^xsd:date`, `true`, `22`) or a thing in words. A
prefixed name, in a cell or in the query, may use the prefixes the query declares and, without declaring them, `rdf:`,
`rdfs:`, `xsd:`, `prov:`, `pav:`, `npx:`, `bridge:`, `oa:` (W3C Web Annotation) and `cascade:` as the vocabulary
declares them. This is the step for what the others do not say; an example uses it only where a plain one would be forced.
