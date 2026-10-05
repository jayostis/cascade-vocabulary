# cascade-vocabulary

How a Cascade pod is described and queried.
[`ro-crate-metadata.json`](ro-crate-metadata.json) lists the package a program loads:

- [`ontologies/`](ontologies): the terms and shapes a
  [Cascade Bridge Adapter](https://github.com/jayostis/cascade-bridge-spec)'s output is read against.
  `core`, `health` and `clinical` are copied from
  [the-cascade-protocol/spec](https://github.com/the-cascade-protocol/spec) (CC BY 4.0);
  `records` and `judgments` are first declared here (Apache-2.0).
- [`queries/v1-draft/`](queries/v1-draft): the standard queries over a pod.

Beside it are one library and the reference tools on it, [`cascade_pod/`](cascade_pod), and one
example pod, as data, [`example-pods/alex-rivera/`](example-pods/alex-rivera).

```sh
python3 -m pip install -r requirements.txt
python3 -m cascade_pod site example-pods/alex-rivera --out site   # then open site/index.html
python3 -m cascade_pod ask example-pods/alex-rivera "record/Why it is in no view"
```
