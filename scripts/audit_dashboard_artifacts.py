"""Read-only Phase 1 physical artifact inventory and permission-gate audit.

Usage from repository root:
  python scripts/audit_dashboard_artifacts.py --root . --out reports/tables/dashboard_phase1_inventory.json

No notebook execution, changes to approved exports, or synthetic evidence.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.',help='Existing V2 repository root')
    ap.add_argument('--out',default=None,help='Optional JSON destination; writes only this report')
    ap.add_argument('--strict-all',action='store_true',help='Require every optional dashboard artifact too')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    sys.path.insert(0,str(root))
    from app_core.artifact_registry import ARTIFACTS
    from app_core.data_access import inspect_artifact
    from app_core.claim_permissions import Permissions
    inventory=[vars(inspect_artifact(root,key)) for key in sorted(ARTIFACTS)]
    mandatory={'06_reproducibility_acceptance','06_final_research_decisions',
               '06_dashboard_readiness','06_subclaim_evidence_register',
               '06_finalization_checks','06_export_manifest','06_final_issue_register'}
    mandatory_missing=[x['key'] for x in inventory if x['key'] in mandatory and x['status']!='VERIFIED_STRUCTURE']
    for item in inventory:
        item['columns']=list(item['columns'])
    gate={'status':'BLOCKED','detail':'No verified claim permissions'}
    try:
        permissions=Permissions.load(root)
        gate={'status':'APPROVED' if permissions.approved else 'BLOCKED',
              'detail':permissions.release_status,
              'rq_rows':len(permissions.rq_table),
              'claim_rows':len(permissions.claim_table)}
    except Exception as exc:
        gate['detail']=f'{type(exc).__name__}: {exc}'
    report={'repository':str(root),'artifacts_total':len(inventory),
            'structure_verified':sum(x['status']=='VERIFIED_STRUCTURE' for x in inventory),
            'not_verified':sum(x['status']!='VERIFIED_STRUCTURE' for x in inventory),
            'mandatory_missing':mandatory_missing,
            'claim_gate':gate,'artifacts':inventory,
            'caution':'VERIFIED_STRUCTURE confirms readability and required columns only; final scientific approval additionally requires manifest/hash binding and claim permissions.'}
    if args.out:
        path=Path(args.out)
        if not path.is_absolute():path=root/path
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print(f"Artifact structure: {report['structure_verified']}/{report['artifacts_total']} verified")
    print('Scientific release gate:',gate)
    for item in inventory:
        if item['status']!='VERIFIED_STRUCTURE':print('  BLOCKED',item['key'],item['reason'])
    return 0 if not mandatory_missing and gate['status']=='APPROVED' and (not args.strict_all or report['not_verified']==0) else 2

if __name__=='__main__':
    raise SystemExit(main())
