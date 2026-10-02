# What to borrow from Tempo

Research date: 2026-10-02. This note informs [SPEC.md](../SPEC.md). Tempo 2.9 source is pinned below; current 3.0 documentation and `main` source are moving references.

## 1. Trace assembly is bounded, not proof of completion

Tempo 2.9 ingesters group incoming spans by trace ID in memory. They cut trace fragments when idle, when a maximum live duration is reached, or when explicitly forced. Defaults in the inspected code are 5 seconds idle and 30 seconds live. A separate head-block lifecycle cuts blocks by age/size; defaults are 30 minutes and 500 MiB. These are different controls, not a single flush timeout.

Trace-ID reads combine data from live traces, the head block, completing blocks, and completed local blocks. Consequently, backend block publication latency is not the minimum latency for viewing a recent trace.

Sources: [Tempo v2.9 configuration](https://github.com/grafana/tempo/blob/v2.9.0/modules/ingester/config.go), [trace cutting and lookup implementation](https://github.com/grafana/tempo/blob/v2.9.0/modules/ingester/instance.go).

## 2. Current Tempo has separate recent-data and block-building paths

Tempo 3.0 documentation describes a live-store that serves recent traces and a separate block-building path. In microservices mode these consume Kafka independently; monolithic live-stores receive data directly. Live-store idle handling improves co-location, but it is not a guarantee about backend block placement.

The long-running-traces documentation explicitly says block-builders cut at a record boundary and flush the consumed cycle regardless of trace completeness. A trace may therefore occupy multiple blocks. Search summaries can cover fewer fragments than a trace-ID lookup, and structural TraceQL conditions may be evaluated against only the trace fragment in a block.

Sources: [Live-store](https://grafana.com/docs/tempo/latest/reference-tempo-architecture/components/live-store/), [long-running traces](https://grafana.com/docs/tempo/latest/troubleshooting/querying/long-running-traces/).

Do not copy a Tempo 2.x `trace_idle_period` setting into a Tempo 3.0 block-builder design and assume equivalent behavior.

## 3. Time bounds prune blocks; they do not prove completeness

Tempo's trace-ID API accepts optional `start` and `end`. With neither, it considers all backend blocks; with both, it limits the block search by time. Its API documentation explicitly warns that time bounds can produce missing or partial traces. A caller can use a known range to reduce work, but widening on “not found” alone cannot repair an already returned partial trace.

Source: [Tempo trace-ID API](https://grafana.com/docs/tempo/latest/api_docs/#query).

The PoC will expose both scopes. Grafana trace-ID entry defaults to the selected range, with an explicit all-retained option. Search links use known summary times with padding. Scope and excluded indexed fragments are visible to the user. The padding is a PoC decision, not behavior claimed for Tempo.

## 4. Searching all blocks does not mean scanning all spans

In the inspected vParquet4 lookup implementation, Tempo first checks a sharded Bloom filter. A negative eliminates the block. For a possible match, it uses an optional trace-ID index or searches ordered Parquet row groups, then reads the matching trace row. The inspected code gates the optional index behind an environment variable; it should not be described as universally enabled.

Source: [vParquet4 trace-ID lookup](https://github.com/grafana/tempo/blob/main/tempodb/encoding/vparquet4/block_findtracebyid.go).

The PoC already proposed an exact trace-to-file metadata map. Retain that for the bounded dataset rather than adding redundant Bloom filters now. Intersect that mapping with file time intervals, then let DuckDB filter the sorted span rows. This is a different physical schema from Tempo's nested trace representation; do not claim DuckDB reproduces Tempo's exact row-seek algorithm. If the exact metadata map grows too large, compare compact per-block Bloom filters and index structures using measured metadata/read costs.

## 5. Changes adopted in the spec

| Earlier draft | Revised design |
|---|---|
| Parquet publication per OTLP request | Bounded cycles grouping several requests and co-locating trace spans |
| Span-start-hour directories | Ingestion-cycle directories; event-time ranges in metadata |
| Always ignore Grafana time range | Explicit time-scoped or all-retained lookup |
| Unqualified “every published span” | Merge all matching fragments within the declared scope and captured view |
| Five-second publication target | Fifteen-second target including a ten-second building cycle |

Raw OTLP remains durable before the writer acknowledges it. The block-building cycle improves grouping without delaying that persistence. Late fragments go into subsequent immutable blocks and are merged at read time.

The PoC still serves only published blocks. Adding Tempo-like immediate trace reads is a separate architectural extension: active trace state, replay, query merging, memory limits, and a publication handoff without missing or double-counting spans. We should implement that if sub-cycle visibility is required, rather than claiming that object-only reads have Tempo's freshness.

## 6. Consequences worth measuring

- Fragments and files read per trace before/after grouping.
- Object count and metadata growth per million spans.
- Visibility latency versus block size at low and high ingestion rates.
- Exact lookup with and without time bounds, including late spans.
- Search-summary accuracy: this PoC deliberately expands matching IDs to all published fragments, which can cost more than Tempo's block-local search summaries.

The enduring constraint remains: neither an idle timeout nor the presence of a root span tells the backend that all spans have arrived. Bounded assembly improves layout; scoped indexed reads improve query cost; completeness remains unknown.
