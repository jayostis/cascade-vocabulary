# cascade-vocabulary

How a Cascade pod is described and queried.
[`ro-crate-metadata.json`](ro-crate-metadata.json) lists the package a program loads:

- [`ontologies/`](ontologies): the terms and shapes a
  [Cascade Bridge Adapter](https://github.com/jayostis/cascade-bridge-spec)'s output is read against.
  `core`, `health` and `clinical` are copied from
  [the-cascade-protocol/spec](https://github.com/the-cascade-protocol/spec) (CC BY 4.0);
  `records` and `judgments` are first declared here (Apache-2.0).
- [`queries/v1-draft/`](queries/v1-draft): the standard queries over a pod.
- [`runtime/`](runtime): the rules a runtime follows when it fills a pod, the vectors that show them, and where a
  pod files each kind of thing, [`pod-layout.ttl`](runtime/pod-layout.ttl).
- [`conformance/`](conformance): the scenario every runtime must pass, Alex Rivera's: her story, its scripted input and
  its right answers. [`runtime/rules.md`](runtime/rules.md#the-conformance-kit) says what passing it means.

Beside it are one library and the reference tools on it, [`cascade_pod/`](cascade_pod), and the small pods each query
is tested on, [`tests/fixtures/`](tests/fixtures). No pod is committed: the tools replay Alex's story into `build/`.

```sh
python3 -m pip install -r requirements.txt
python3 -m cascade_pod replay conformance/alex-rivera --out build/alex-rivera
python3 -m cascade_pod site build/alex-rivera --out build/alex-rivera/site   # then open build/alex-rivera/site/index.html
python3 -m cascade_pod ask build/alex-rivera "record/Why it is in no view"
python3 -m cascade_pod graphdb build/alex-rivera http://localhost:7200
```
