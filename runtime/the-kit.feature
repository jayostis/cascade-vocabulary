Feature: The conformance kit
  A kit is a scenario every runtime must pass: a folder under conformance/ holding a feature file, its scripted input
  and its right answers only. conformance/alex-rivera/ is Alex Rivera's pod, from
  https://github.com/jayostis/cascade-vocabulary/issues/4.

  - alex-rivera.feature is her story, the Background every example replays: each of Alex's judgments is a step of its
    own, and each matcher run a step with its time. Under it, each planted case P1 to P25 is a rule, and each example
    under it reads the pod at the smallest set of steps and lenses at which it can fail for its own reason. A runtime
    runs them on its one SPARQL engine; whether two engines agree is the vocabulary's own check, made over the fixtures
    of its queries.
  - scripted-input/alex/ holds what the steps name. Each import step's Bridge output is in a folder named as the step,
    because a conversion carries its import's start. The facts the importer gives the Bridge are not input: the
    importer writes them from export.xml.
  - expected/ holds the five views a correct runtime builds at the last step under the everyday lens, each entry a blank
    node, and handles.json, the scenario's name inputs for each record and profile it gives a handle.

  A runtime passes a kit when every rule below holds for one replay of its story. An EARL report names checks 2 to 5
  as tests by an IRI relative to the kit's folder: check 2 is #check-2-each-final-view-equals-expected, check 3
  is #check-3-every-file-conforms-to-the-shapes, check 4 is #check-4-every-name-follows-its-rule, and check 5
  is #check-5-every-file-is-where-the-layout-says.

  Rule: Check 1. Every example passes
    Every example of the kit's feature file, and every example of the rules' feature files. Check 1 is no test of its
    own: its tests are the examples.

  Rule: Check 2. Each final view equals expected/
    Take the view graph the replay builds at the last step under everyday (the graph <address>clinical/<view>.ttl),
    keep each subject that has cascade:mergedFrom with its triples, and replace each urn:cascade:entry: IRI with a blank
    node. The result is the expected file's graph, up to its blank nodes.

    No example states this check: SPARQL cannot compare two graphs up to their blank nodes.

  Rule: Check 3. Every RDF file of the pod conforms to the vocabulary's shapes
    Each read with the files that describe what it names, less clinical/labels.ttl. That file gives a label, for people
    to read, to things other files describe, the subject among them, and rec:SubjectShape is closed: read with the rest,
    it would refuse the subject's rdfs:label.

    No example states this check: SPARQL cannot run SHACL.

  Rule: Check 4. Every name follows its rule
    N1 to N7, N9 and N10, computed from that run's own inputs, its random import and session IDs among them. Each saved
    Bridge output is in the pod less its arrivals, with its import replaced by the import its step wrote (A9, A11), and
    each revision follows an earlier revision of the same record.

    No example states this check: SPARQL cannot hash a canonical graph.

  Rule: Check 5. Every file the runtime wrote is where pod-layout.ttl says
    The check is open-world: the pod may also hold files another app wrote.

    No example states this check: SPARQL cannot read a stored document's bytes.
