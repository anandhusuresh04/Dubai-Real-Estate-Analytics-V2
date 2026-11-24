"""Local read-only coverage and permission check of all Phase 3 exhibits."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.analytics.catalog import EXHIBITS
from app.analytics.gateway import load_exhibit,select_columns,EvidenceUnavailable,published_claims,attested_hash
from app_core.claim_permissions import Permissions
from app_core.data_access import read_artifact
from app.analytics.charts import validated_chart_frame
from app_core.integrity import validate_06_release_pair


def audit(root:Path)->list[dict]:
    validate_06_release_pair(root)
    perms=Permissions.load(root)
    rows=[]
    for e in EXHIBITS:
        try:
            claim=published_claims(perms,e.rq)[0] if e.claim_sensitive and published_claims(perms,e.rq) else None
            frame=load_exhibit(root,e,claim_id=claim)
            x,y,z=select_columns(frame,e)
            rows.append(dict(exhibit=e.id,artifact=e.artifact,status='SCHEMA_READY',rows=len(frame),
                             dimension=x,value=y,segment=z,claim=claim))
        except EvidenceUnavailable as exc:
            reason=str(exc)
            code=('CLAIM_WITHHELD' if e.claim_sensitive and
                  ('individually published' in reason or 'claim' in reason.lower()) else
                  'SCHEMA_UNAVAILABLE' if 'column' in reason.lower() or 'schema' in reason.lower() else
                  'OTHER_UNAVAILABLE')
            entry=dict(exhibit=e.id,artifact=e.artifact,status='WITHHELD_OR_UNAVAILABLE',
                       classification=code,reason=reason)
            if e.id=='size_elasticity':
                # Technical schema-only inspection. Never publish beta or bypass
                # the individual-claim authorization barrier.
                try:
                    upstream=read_artifact(root,e.artifact,
                        expected_hash=attested_hash(root,e.artifact))
                    validated_chart_frame(upstream,e)
                    entry['technical_schema']='READY_WITHHELD'
                except Exception as schema_exc:
                    entry['technical_schema']='UNAVAILABLE'
                    entry['technical_reason']=str(schema_exc)
            rows.append(entry)
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='.')
    p.add_argument('--out',default='reports/tables/dashboard_phase3_coverage.json')
    a=p.parse_args()
    root=Path(a.root).resolve()
    entries=audit(root)
    output=(root/a.out).resolve()
    if not output.is_relative_to(root):raise SystemExit('Output must be inside the project.')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(entries,indent=2,ensure_ascii=False),encoding='utf-8')
    ready=sum(x['status']=='SCHEMA_READY' for x in entries)
    print(f'Exhibits with current verified schemas and permissions: {ready}/{len(entries)}')
    for entry in entries:
        if entry['status']!='SCHEMA_READY':print(f"- {entry['exhibit']}: {entry['reason']}")
    from collections import Counter
    classes=Counter(x.get('classification','SCHEMA_READY') for x in entries)
    print('Classification:', ', '.join(f'{k}={v}' for k,v in sorted(classes.items())))
    print(f'Full report: {output}')
