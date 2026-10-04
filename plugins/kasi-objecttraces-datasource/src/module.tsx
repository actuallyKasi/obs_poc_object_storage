import React from 'react';
import { DataSourceApi, DataSourcePlugin, DataQuery, DataQueryRequest, DataSourceInstanceSettings, QueryEditorProps, DataSourcePluginOptionsEditorProps } from '@grafana/data';
import { getBackendSrv } from '@grafana/runtime';
import { DataSourceHttpSettings } from '@grafana/ui';
import { forkJoin, map, of } from 'rxjs';
import { frame, Trace } from './contract';
interface Query extends DataQuery { traceId?: string; lookupScope?: 'time_range' | 'all_retained'; start?: string; end?: string }
class DataSource extends DataSourceApi<Query> {
  constructor(private settings: DataSourceInstanceSettings) { super(settings); }
  query(request: DataQueryRequest<Query>) {
    const targets = request.targets.filter(q => !q.hide && q.traceId);
    if (!targets.length) { return of({data:[]}); }
    return forkJoin(targets.map(q => {
      if (!/^[0-9a-f]{32}$/.test(q.traceId!)) { throw new Error('Trace ID must be 32 lowercase hex characters'); }
      const params = new URLSearchParams();
      if (q.lookupScope !== 'all_retained') { params.set('start',q.start ?? request.range.from.toISOString()); params.set('end',q.end ?? request.range.to.toISOString()); }
      return getBackendSrv().fetch<Trace>({url:`${this.settings.url}/api/v1/traces/${q.traceId}?${params}`}).pipe(map(r => frame(r.data,q.refId)));
    })).pipe(map(data => ({data})));
  }
  async testDatasource() { await new Promise<void>((resolve,reject) => getBackendSrv().fetch({url:`${this.settings.url}/healthz`}).subscribe({next:()=>resolve(),error:reject})); return {status:'success',message:'Fixture endpoint available'}; }
}
function QueryEditor({query,onChange,onRunQuery}: QueryEditorProps<DataSource,Query>) {
  return <div><label>Trace ID <input aria-label="Trace ID" style={{width:330}} value={query.traceId ?? ''} onChange={e=>onChange({...query,traceId:e.target.value})} onBlur={onRunQuery}/></label>{' '}
    <label>Lookup scope <select aria-label="Lookup scope" value={query.lookupScope ?? 'time_range'} onChange={e=>{onChange({...query,lookupScope:e.target.value as Query['lookupScope'],start:undefined,end:undefined});onRunQuery();}}><option value="time_range">Selected time range</option><option value="all_retained">All retained data</option></select></label>
    <p>Deterministic fixture · Scope: {query.lookupScope === 'all_retained' ? 'All retained data' : 'Selected time range'} · Completeness unknown</p></div>;
}
function ConfigEditor({options,onOptionsChange}: DataSourcePluginOptionsEditorProps) { return <DataSourceHttpSettings defaultUrl="http://querier:8080" dataSourceConfig={options} onChange={onOptionsChange}/>; }
export const plugin = new DataSourcePlugin<DataSource,Query>(DataSource).setQueryEditor(QueryEditor).setConfigEditor(ConfigEditor);
