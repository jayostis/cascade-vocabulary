# cascade-vocabulary

How a Cascade pod is described and queried, as one package that
[`ro-crate-metadata.json`](ro-crate-metadata.json) lists:

- [`ontologies/`](ontologies): the terms and shapes a
  [Cascade Bridge Adapter](https://github.com/jayostis/cascade-bridge-spec)'s output is read against.
  `core`, `health` and `clinical` are copied from
  [the-cascade-protocol/spec](https://github.com/the-cascade-protocol/spec) (CC BY 4.0);
  `records` and `judgments` are first declared here (Apache-2.0).
- [`queries/v1-draft/`](queries/v1-draft): the lenses, derivations, views and questions over a pod.
- [`cascade_pod/`](cascade_pod): one library, and the reference tools on it.
- [`example-pods/alex-rivera/`](example-pods/alex-rivera): one example pod, as data.

```sh
python3 -m pip install -r requirements.txt
python3 -m cascade_pod site example-pods/alex-rivera --out site
python3 -m cascade_pod ask example-pods/alex-rivera "record/Why it is in no view"
```
