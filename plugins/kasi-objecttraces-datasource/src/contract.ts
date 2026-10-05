import type { TraceSpanRow, DataFrame, FieldType } from '@grafana/data';
export interface Attribute { key: string; value: {stringValue?: string; boolValue?: boolean; intValue?: string; doubleValue?: number; bytesValue?: string; arrayValue?: {values: Attribute['value'][]}; kvlistValue?: {values: Attribute[]}} }
export interface Span {
  traceId: string; spanId: string; parentSpanId: string | null; name: string; serviceName: string;
  startTimeUnixNano: string; endTimeUnixNano: string; durationNano: string; receivedAtUnixNano: string;
  kind: number; statusCode: number; statusMessage: string; attributes: Attribute[]; resourceAttributes: Attribute[];
  events: Array<{timeUnixNano: string; name: string; attributes: Attribute[]}>;
  links: Array<{traceId: string; spanId: string; attributes: Attribute[]}>;
  scope: {name: string; version: string; attributes: Attribute[]}; droppedAttributesCount: number;
}
export interface Trace {apiVersion: string; traceId: string; spans: Span[]; meta: {lookupScope: string; warnings: string[]; [key: string]: unknown}}
export function milliseconds(ns: string): number { const n = BigInt(ns); return Number(n / 1000000n) + Number(n % 1000000n) / 1000000; }
function value(v: Attribute['value']): unknown {
  if (v.intValue !== undefined) { const n = BigInt(v.intValue); return n > BigInt(Number.MAX_SAFE_INTEGER) || n < BigInt(Number.MIN_SAFE_INTEGER) ? v.intValue : Number(n); }
  if (v.arrayValue) { return v.arrayValue.values.map(value); }
  if (v.kvlistValue) { return Object.fromEntries(v.kvlistValue.values.map(a => [a.key, value(a.value)])); }
  return v.stringValue ?? v.boolValue ?? v.doubleValue ?? v.bytesValue;
}
export function tags(attrs: Attribute[]) { return attrs.map(a => ({key:a.key,value:value(a.value),type:Object.keys(a.value)[0]})); }
export function rows(trace: Trace): TraceSpanRow[] {
  return [...trace.spans].sort((a,b) => BigInt(a.startTimeUnixNano) < BigInt(b.startTimeUnixNano) ? -1 : BigInt(a.startTimeUnixNano) > BigInt(b.startTimeUnixNano) ? 1 : a.spanId.localeCompare(b.spanId)).map(s => ({
    traceID:s.traceId, spanID:s.spanId, parentSpanID:s.parentSpanId ?? undefined, operationName:s.name, serviceName:s.serviceName,
    startTime:milliseconds(s.startTimeUnixNano), duration:milliseconds(s.durationNano), serviceTags:tags(s.resourceAttributes),
    tags:[...tags(s.attributes).filter(a => s.statusCode !== 2 || a.key !== 'error'), ...(s.statusCode === 2 ? [{key:'error',value:true,type:'boolValue'}] : [])],
    logs:s.events.map(e => ({timestamp:milliseconds(e.timeUnixNano),name:e.name,fields:tags(e.attributes)})),
    references:s.links.map(l => ({traceID:l.traceId,spanID:l.spanId,tags:tags(l.attributes)})),
    kind:['UNSPECIFIED','INTERNAL','SERVER','CLIENT','PRODUCER','CONSUMER'][s.kind], statusCode:s.statusCode,statusMessage:s.statusMessage,
    instrumentationLibraryName:s.scope.name,instrumentationLibraryVersion:s.scope.version,
    warnings:[...(s.parentSpanId && !trace.spans.some(p => p.spanId === s.parentSpanId) ? ['Parent span is missing in this lookup scope'] : []),
      `Scope attributes: ${JSON.stringify(tags(s.scope.attributes))}; dropped attributes: ${s.droppedAttributesCount}`],
  }));
}
export function frame(trace: Trace, refId: string): DataFrame {
  const data = rows(trace);
  const fields: Array<[keyof TraceSpanRow, string]> = [['traceID','string'],['spanID','string'],['parentSpanID','string'],['operationName','string'],['serviceName','string'],['startTime','number'],['duration','number'],['serviceTags','other'],['tags','other'],['logs','other'],['references','other'],['kind','string'],['statusCode','number'],['statusMessage','string'],['instrumentationLibraryName','string'],['instrumentationLibraryVersion','string'],['warnings','other']];
  return {refId,length:data.length,fields:fields.map(([name,type]) => ({name,type:type as FieldType,config:{},values:data.map(r => r[name])})),meta:{preferredVisualisationType:'trace',notices:[{severity:'info',text:`Scope: ${trace.meta.lookupScope}. Completeness unknown. Deterministic fixture.`},...trace.meta.warnings.map(text => ({severity:'warning' as const,text}))]}};
}
