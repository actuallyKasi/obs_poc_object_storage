# Grafana 12.2.0 source contract

Upstream tag `v12.2.0`, commit `92f1fba9b4b6700328e99e97328d6639df8ddc3d`.
The adjacent files are verbatim snapshots from
[`packages/grafana-data/src/types/`](https://github.com/grafana/grafana/tree/92f1fba9b4b6700328e99e97328d6639df8ddc3d/packages/grafana-data/src/types).
Grafana is AGPL-3.0-only; these snapshots retain upstream source and are used as
compatibility references. See [upstream license](https://github.com/grafana/grafana/blob/92f1fba9b4b6700328e99e97328d6639df8ddc3d/LICENSE).

SHA-256:

```text
2176277f9f129f1ba536b623c25ff7232f79ce251cf90589d5387c11d99a7ef4  data.ts
fcdcb40b58cd0c32f31fae6f0d21ed69e7b27e4e3c8f7a3ef74dd305ffac26dd  dataFrame.ts
ceb7c5be117e8cee067d20231c12a2b1b044246b1cd27bb8ce7bab9cbc3959b0  trace.ts
```

`TraceSpanRow` specifies milliseconds, typed tag/log/reference arrays and boolean
`error: true`. `DataFrameMeta.preferredVisualisationType` selects the native trace
view. No dataplane `meta.type` is invented. The plugin compiles against exact
`@grafana/{data,runtime,ui}` 12.2.0 packages, with transitive dependencies and
integrity hashes in `package-lock.json`; the Grafana, Node and Python images are
pinned by manifest digest in their Dockerfiles.
