from pathlib import Path
import pytest
import pandas as pd
from app_core.artifact_registry import ARTIFACTS, get_artifact, resolve_artifact, SOURCE_SHA256
from app_core.data_access import read_artifact, inspect_artifact, ArtifactError, sha256_file
from app_core.metric_contracts import METRICS, Operation, validate_filter, require_aggregation, UnsupportedInteraction
from app_core.claim_permissions import Permissions, PermissionDenied, _bool
from app_core.integrity import verify_06_manifest_entry


def test_registry_has_real_research_owners_and_no_duplicate_paths():
    assert len(ARTIFACTS)>45
    assert {a.owner for a in ARTIFACTS.values()}=={'01','02','03','04','05','06'}
    paths=[a.relative_path for a in ARTIFACTS.values()]
    assert len(paths)==len(set(paths))
    assert len(SOURCE_SHA256)==64
    assert get_artifact('market_yearly').filename=='market_yearly.parquet'  # unprefixed NB01


def test_unregistered_artifact_rejected(tmp_path):
    with pytest.raises(KeyError):resolve_artifact(tmp_path,'../../private.txt')


def test_missing_and_empty_artifact_fail_closed(tmp_path):
    assert inspect_artifact(tmp_path,'01_market_summary').status=='BLOCKED'
    p=tmp_path/'reports/tables/01_market_summary.csv'
    p.parent.mkdir(parents=True)
    p.write_text('')
    with pytest.raises(ArtifactError):read_artifact(tmp_path,'01_market_summary')


def test_string_keeping_and_required_csv_columns(tmp_path):
    p=tmp_path/'reports/tables/01_market_summary.csv'
    p.parent.mkdir(parents=True)
    p.write_text('year,n_transactions,category\n2025,5,NA\n2024,3,True\n')
    x=read_artifact(tmp_path,'01_market_summary')
    assert x.category.tolist()==['NA','True']
    assert x.year.tolist()==['2025','2024']
    with pytest.raises(ArtifactError):read_artifact(tmp_path,'01_market_summary',required_columns=('missing_column',))
    with pytest.raises(ArtifactError):read_artifact(tmp_path,'01_market_summary',expected_hash='0'*64)
    assert len(sha256_file(p))==64


def test_metric_to_artifact_registry_and_all_rq():
    for metric in METRICS.values():
        assert metric.artifact in ARTIFACTS, metric.name
        assert metric.rq in ARTIFACTS[metric.artifact].rq, metric.name


def test_unsupported_global_filter_rejected():
    validate_filter('matched_price_change',{'design':'A'})
    with pytest.raises(UnsupportedInteraction):validate_filter('matched_price_change',{'area_id':1})
    with pytest.raises(UnsupportedInteraction):validate_filter('matched_price_change',{'design':'A'},available_columns=('year',))


def test_prohibit_mean_of_medians_and_unsafe_sums():
    with pytest.raises(UnsupportedInteraction):require_aggregation('residential_median_psm',Operation.SUM,disjoint=True)
    with pytest.raises(UnsupportedInteraction):require_aggregation('registered_count',Operation.SUM,disjoint=False)
    require_aggregation('registered_count',Operation.SUM,disjoint=True)


def test_bool_strings_not_python_truthiness():
    assert _bool('False') is False
    assert _bool('True') is True
    with pytest.raises(PermissionDenied):_bool('1')


def _sample_permissions():
    return Permissions('APPROVED_WITH_QUALIFICATIONS',True,
      pd.DataFrame([{'rq_id':'RQ11','final_status':'QUALIFIED'}]),
      pd.DataFrame([{'page':'Market Structure','rq':'RQ11','publishable':True}]),
      pd.DataFrame([{'upstream_claim_id':'REG01','rq_id':'RQ11','published':False,'release_approved':False}]))


def test_rq_metric_permission_does_not_publish_subclaim():
    p=_sample_permissions()
    p.authorize_metric(page='Market Structure',rq='RQ11',artifact_verified=True)
    with pytest.raises(PermissionDenied):p.authorize_claim('REG01')
    with pytest.raises(PermissionDenied):p.authorize_metric(page='Market Structure',rq='RQ11',artifact_verified=False)
    with pytest.raises(PermissionDenied):p.authorize_metric(page='Market Dynamics',rq='RQ11',artifact_verified=True)


def test_release_failure_denies_every_dashboard_claim():
    p=_sample_permissions()
    p=Permissions('RELEASE_BLOCKED',False,p.rq_table,p.dashboard_table,p.claim_table)
    with pytest.raises(PermissionDenied):p.authorize_metric(page='Market Structure',rq='RQ11',artifact_verified=True)


def test_manifest_cannot_self_certify_or_certify_older_notebooks(tmp_path):
    with pytest.raises(ArtifactError):verify_06_manifest_entry(tmp_path,'06_export_manifest')
    with pytest.raises(ArtifactError):verify_06_manifest_entry(tmp_path,'02_price_index_endpoint')


def test_manifest_rejects_corrupted_digest(tmp_path):
    p=tmp_path/'reports/tables/06_export_manifest.csv'
    p.parent.mkdir(parents=True)
    p.write_text('name,status,csv_sha256,parquet_sha256\n06_final_research_decisions,VERIFIED,'+'0'*64+','+'0'*64+'\n')
    with pytest.raises(ArtifactError):verify_06_manifest_entry(tmp_path,'06_final_research_decisions')


def test_runtime_access_refuses_untrusted_upstream_hash(tmp_path,monkeypatch):
    from app_core.approved_data import load_approved_metric
    # Do not allow a consumer to bypass the strict release record and physical
    # artifact tests with its own `artifact_verified=True` assertion.
    with pytest.raises((ArtifactError,PermissionDenied)):
        load_approved_metric(tmp_path,'matched_price_change',{'design':'A'})


def test_all_runtime_metric_rqs_are_declared():
    from app_core.approved_data import SOURCE_PAGE_BY_RQ
    assert set(SOURCE_PAGE_BY_RQ)=={f'RQ{i:02}' for i in range(1,16)}
    for m in METRICS.values():
        assert SOURCE_PAGE_BY_RQ[m.rq] is not None


def test_empty_final_issue_ledger_is_valid_structure(tmp_path):
    p=tmp_path/'data/aggregates/06_final_issue_register.parquet'
    # Empty issue ledger validation is exercised without installing optional
    # Parquet libraries: the read boundary is replaced, not the gate logic.
    from unittest.mock import patch
    import app_core.data_access as access
    with patch.object(access,'read_artifact',return_value=pd.DataFrame(columns=['severity','code'])) as reader, \
         patch.object(access,'sha256_file',return_value='a'*64):
        p.parent.mkdir(parents=True)
        p.write_bytes(b'parquet-fixture')
        result=access.inspect_artifact(tmp_path,'06_final_issue_register')
        assert result.status=='VERIFIED_STRUCTURE'
        assert reader.call_args.kwargs['allow_empty'] is True
