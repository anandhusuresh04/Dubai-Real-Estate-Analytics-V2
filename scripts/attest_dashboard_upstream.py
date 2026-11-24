"""Explicit OFFLINE local upstream file attestation (not a scientific reanalysis).

Run only after local Phase 1 inventory and full research test suite succeed.
This creates a byte-level frozen snapshot for the dashboard, with serializations
and raw source consistency checks. It cannot independently prove every scientific
estimate; Notebook 06 remains the authority on scientific publication rights.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_core.artifact_registry import ARTIFACTS,SOURCE_SHA256,resolve_artifact
from app_core.data_access import inspect_artifact,sha256_file
from app_core.integrity import validate_06_release_pair
from app_core.claim_permissions import Permissions
from app.analytics.gateway import ATTESTATION


def attest(root:Path, *,strict:bool=True)->dict:
    root=Path(root)
    validate_06_release_pair(root)
    perms=Permissions.load(root)
    if not perms.approved:raise RuntimeError('Research publication gate rejected attestation.')
    source=root/'data/raw/dld_sales_transactions.parquet'
    if not source.is_file() or sha256_file(source)!=SOURCE_SHA256:
        raise RuntimeError('Frozen source dataset missing or does not match approved SHA-256.')
    records={};failed=[]
    for key,spec in ARTIFACTS.items():
        if spec.owner=='06':continue
        result=inspect_artifact(root,key)
        if result.status!='VERIFIED_STRUCTURE':
            failed.append(f'{key}: {result.reason}');continue
        # Check both available serializations for schema/row identity. A missing
        # CSV is recorded; it does NOT create an invented research export.
        pq=root/'data/aggregates'/f'{key}.parquet'
        csv=root/'reports/tables'/f'{key}.csv'
        if pq.is_file() and csv.is_file():
            import pandas as pd
            p=pd.read_parquet(pq)
            c=pd.read_csv(csv,dtype='string',keep_default_na=False)
            if len(p)!=len(c) or list(p.columns)!=list(c.columns):
                failed.append(f'{key}: CSV/Parquet row count or columns differ');continue
            import numpy as np
            difference=None
            for col in p.columns:
                original=p[col]
                text=c[col].fillna('').astype(str)
                if pd.api.types.is_bool_dtype(original):
                    converted=text.map({'True':True,'False':False,'true':True,'false':False,'':pd.NA})
                    matches=original.astype('boolean').reset_index(drop=True).equals(
                            converted.astype('boolean').reset_index(drop=True))
                elif pd.api.types.is_numeric_dtype(original):
                    a=pd.to_numeric(original,errors='coerce').to_numpy(dtype=float,na_value=np.nan)
                    b=pd.to_numeric(text.replace('',pd.NA),errors='coerce').to_numpy(dtype=float,na_value=np.nan)
                    matches=bool(np.allclose(a,b,rtol=1e-9,atol=1e-7,equal_nan=True))
                else:
                    matches=original.fillna('').astype(str).reset_index(drop=True).equals(
                             text.reset_index(drop=True))
                if not matches:
                    difference=col;break
            if difference:
                failed.append(f'{key}: paired CSV/Parquet values differ in {difference}');continue
        records[key]={'verified':True,'relative_path':spec.relative_path.as_posix(),
                      'sha256':result.sha256,'rows':result.rows,'columns':list(result.columns),
                      'paired_format_check':pq.is_file() and csv.is_file()}
    if strict and failed:
        raise RuntimeError(f'Unverified upstream artifacts ({len(failed)}):\n'+'\n'.join(failed))
    return {'attestation_version':1,'source_sha256':SOURCE_SHA256,
            'release_status':perms.release_status,'generated_utc':datetime.now(timezone.utc).isoformat(),
            'artifacts':records,'unverified':failed,
            'note':'Local physical artifact snapshot, not an independent proof of scientific estimands.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default='.')
    parser.add_argument('--out',default=str(ATTESTATION))
    parser.add_argument('--allow-missing',action='store_true',help='Attest existing files only; missing exhibit files remain unavailable')
    args=parser.parse_args()
    root=Path(args.root).resolve()
    report=attest(root,strict=not args.allow_missing)
    out=(root/args.out).resolve()
    if not out.is_relative_to(root):raise SystemExit('Output must be inside project root')
    if out.exists():raise SystemExit(f'Refusing to overwrite previous attestation: {out}. Rename or archive it first.')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f"Verified upstream files: {len(report['artifacts'])}; unavailable: {len(report['unverified'])}")
    print(f'Attestation written: {out}')
