import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {frame,milliseconds,rows,Trace} from './contract';
const fixture: Trace = JSON.parse(readFileSync(new URL('../trace.json',import.meta.url),'utf8'));
test('Grafana 12.2 trace contract: IDs, parenting, units, types, errors, events, links',()=>{
  const input = JSON.stringify(fixture);
  const data = rows(fixture); const f = frame(fixture,'B');
  assert.equal(f.refId,'B'); assert.equal(f.meta?.preferredVisualisationType,'trace'); assert.equal(f.meta?.type,undefined);
  assert.ok(f.fields.every(field=>field.values.length===2));
  assert.deepEqual(f.fields.filter(field=>field.type==='number').map(field=>field.name),['startTime','duration','statusCode']);
  assert.equal(data[0].traceID,'0123456789abcdef0123456789abcdef'); assert.equal(data[0].parentSpanID,undefined);
  assert.equal(data[1].parentSpanID,data[0].spanID); assert.equal(data[1].duration,1.5);
  assert.equal(milliseconds('1500000'),1.5); assert.equal(data[0].startTime,1790899200000.0002);
  assert.deepEqual(data[1].tags,[{key:'error',value:true,type:'boolValue'}]);
  assert.equal(data[0].tags?.find(t=>t.key==='large.integer')?.value,'9223372036854775807');
  assert.equal(data[0].tags?.find(t=>t.key==='enabled')?.value,true);
  assert.deepEqual(data[0].tags?.find(t=>t.key==='nested')?.value,{ratio:1.25});
  assert.equal(data[0].tags?.find(t=>t.key==='payload')?.value,'AQID');
  assert.equal(data[1].logs?.[0].timestamp,1790899200001.2502); assert.equal(data[1].logs?.[0].name,'exception');
  assert.equal(data[1].references?.[0].spanID,'3333333333333333'); assert.equal(data[1].references?.[0].traceID,'abcdef0123456789abcdef0123456789');
  assert.equal(data[1].references?.[0].tags?.[0].value,'payment attempt');
  assert.equal(JSON.stringify(fixture),input);
});
test('sorts without changing input; missing parent diagnostic',()=>{
  const t = structuredClone(fixture); t.spans.reverse(); assert.equal(rows(t)[0].spanID,'1111111111111111');
  t.spans = [t.spans[0]]; assert.match(rows(t)[0].warnings![0],/missing/);
});
