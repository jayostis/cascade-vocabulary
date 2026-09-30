# cascade-vocabulary

The ontology and shapes files a
[Cascade Bridge Adapter](https://github.com/jayostis/cascade-bridge-spec)'s output
is read against, as one package: [`ro-crate-metadata.json`](ro-crate-metadata.json)
lists its files. An adapter names this repository as its `bridge:cascadeVocabularyPin`
and each file it is read against, by the path in that list, as a `bridge:vocabularyFile`.

- `ontologies/core`, `health`, `clinical`: terms copied from
  [the-cascade-protocol/spec](https://github.com/the-cascade-protocol/spec) under their
  own IRIs, each naming the file and commit it came from with `dct:source`. CC BY 4.0.
- `ontologies/records`, `judgments`: the records and judgments of the records, judgments
  and views design, first declared here. Apache-2.0.
