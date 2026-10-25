Feature: The conformance kit
  A kit is a scenario every runtime must pass: a folder under conformance/ holding a feature file, its scripted input
  and its right answers only. conformance/alex-rivera/ is Alex Rivera's pod, from
  https://github.com/jayostis/cascade-vocabulary/issues/4, and FHIR only. conformance/priya-natarajan/ is Priya
  Natarajan's, from https://github.com/jayostis/cascade-runtime-js/issues/70: one pod from FHIR and C-CDA together, with
  medications and lab results, laid out as Alex's and with its own planted cases P1 to P17. conformance/martin-okafor/
  is Martin Okafor's, from https://github.com/jayostis/cascade-vocabulary/issues/138: one variant in two FHIR reports,
  each saved as a pull, with the story's subset of ClinVar's table and its own planted cases M1 to M6.
  conformance/tamsin-vale/ is Tamsin Vale's, from cascade-runtime-js#343: one hospital's record pulled twice, a year
  apart, a medication stopped between the pulls, with its own planted cases T1 to T4. What follows says it of Alex's
  kit; Priya's, Martin's and Tamsin's are alike.

  - alex-rivera.feature is her story, the Background every example replays: each of Alex's judgments is a step of its
    own, and each matcher run a step with its time. Under it, each planted case P1 to P25 is a rule, and each example
    under it reads the pod at the smallest set of steps and lenses at which it can fail for its own reason. A runtime
    runs them on its one SPARQL engine; whether two engines agree is the vocabulary's own check, made over the fixtures
    of its queries.
  - scripted-input/alex/ holds what the steps name. Each import step's Bridge output is in a folder named as the step,
    because a conversion carries its import's start. The facts the importer gives the Bridge are not input: the
    importer writes them from export.xml.
  - expected/ holds each view a correct runtime builds at the last step under the everyday lens, each entry a blank
    node, and handles.json, the scenario's name inputs for each record and profile it gives a handle.

  A runtime passes a kit when every rule below holds for one replay of its story. An EARL report names checks 2 to 6
  as tests by an IRI relative to the kit's folder: check 2 is #check-2-each-final-view-equals-expected, check 3
  is #check-3-every-file-conforms-to-the-shapes, check 4 is #check-4-every-name-follows-its-rule, check 5
  is #check-5-every-file-is-where-the-layout-says, and check 6 is #check-6-no-view-holds-the-pods-address.

  Rule: Check 1. Every example passes
    No note rules this.
    Every example of the kit's feature file, and every example of the rules' feature files. Check 1 is no test of its
    own: its tests are the examples.

  Rule: Check 2. Each final view equals expected/
    No note rules this.
    Take the view graph the replay builds at the last step under everyday (the graph <address>clinical/<view>.ttl),
    keep each subject that has cascade:mergedFrom with its triples but its members' current values
    (cascade:memberCurrentValues), which the fixtures of queries/questions/entry/What it shows.rq hold to it, and
    replace each entry, which the file writes as <#hex> (N13) and the graph holds resolved against the view's address,
    with a blank node. The result is the expected file's graph, up to its blank nodes.

    No example states this check: SPARQL cannot compare two graphs up to their blank nodes.

  Rule: Check 3. Every RDF file of the pod conforms to the vocabulary's shapes
    No note rules this.
    Each read with the files that describe what it names, less clinical/labels.ttl. That file gives a label, for people
    to read, to things other files describe, the subject among them, and cascade:SubjectShape is closed: read with the rest,
    it would refuse the subject's rdfs:label.

    No example states this check: SPARQL cannot run SHACL.

  Rule: Check 4. Every name follows its rule
    No note rules this.
    N1 to N7, N9, N10, N14 and N15, computed from that run's own inputs, its random import and matcher run IDs among them.
    Each saved Bridge output is in the pod less its arrivals, with its import replaced by the import its step wrote and
    the runtime that performed it left out (A9, A11), and each revision follows an earlier revision of the same record.
    Each act leaves one snapshot, named by its rule, whose first parent is the snapshot before it and whose added files
    are the files of the set its act wrote; its set hash is the set's after its step, and the last snapshot's is the set
    hash of the files the final pod lists of that set: a pod with one file of the set removed or changed fails it.

    No example states this check: SPARQL cannot hash a canonical graph.

  Rule: Check 5. Every file the runtime wrote is where pod-layout.ttl says
    No note rules this.
    The check is open-world: the pod may also hold files another app wrote.

    No example states this check: SPARQL cannot read a stored document's bytes.

  Rule: Check 6. No view the runtime wrote, nor any view it shares, holds the pod's address
    decisions/naming.md, row "view entry"; decisions/republishing-sources.md, row "what leaves the pod".
    A view entry is written in the view file as <#hex>, relative to its view
    (N13), never as the derivations' placeholder urn:cascade:entry:<hex>, and no IRI a view file holds, as its bytes
    write it, begins with the pod's address: a view says nothing of where the pod lives.

    No example states this check: SPARQL reads a file's IRIs resolved against its address, never as its bytes write them.
