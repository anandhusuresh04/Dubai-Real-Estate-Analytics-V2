"""Phase 2 skeleton tests; independent of a Streamlit server and market data."""
from __future__ import annotations
import ast
from pathlib import Path
from types import SimpleNamespace
from html import escape
import sys
import importlib.util
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from app.navigation import PAGES, page_files, register_pages
from app.config import get_settings
from app.runtime import ReleaseView, check_release, require_claim
from app.components.header import page_header,scope_badges
from app.components.kpi import display_value, kpi_card
from app.components.evidence import evidence_panel
from app.components.status import status_badge
from app.components.empty_state import empty_state, REASONS
from app.components.footer import page_footer
from app.components.layout import render_shell
from app.theme.styles import CSS

class FakeStreamlit:
    def __init__(self):
        self.calls=[]
        self.sidebar=self
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def markdown(self,text,**kwargs): self.calls.append(('markdown',text,kwargs))
    def write(self,*args): self.calls.append(('write',args,{}))
    def caption(self,text): self.calls.append(('caption',text,{}))
    def warning(self,text): self.calls.append(('warning',text,{}))
    def columns(self,n,**kwargs): return [self for _ in range(n)]
    def expander(self,*args,**kwargs): self.calls.append(('expander',args,kwargs));return self
    def tabs(self,labels): self.calls.append(('tabs',tuple(labels),{}));return [self for _ in labels]
    def container(self,**kwargs): self.calls.append(('container',kwargs,{}));return self
    def set_page_config(self,**kwargs): self.calls.append(('set_page_config',kwargs,{}))
    def Page(self,path,**kwargs): return SimpleNamespace(path=path,**kwargs)
    def navigation(self,pages,**kwargs):
        self.pages=pages
        self.calls.append(('navigation',len(pages),kwargs))
        return SimpleNamespace(run=lambda:self.calls.append(('run',None,{})))
    def divider(self): self.calls.append(('divider',None,{}))

def text_of(st):
    return '\n'.join(str(item[1]) for item in st.calls)

def test_six_pages_only_stable_order_and_no_duplicates():
    assert len(PAGES)==6
    assert len({p.key for p in PAGES})==6
    assert len({p.title for p in PAGES})==6
    assert [p.key for p in PAGES] == [
        'intelligence_brief','market_dynamics','price_reality',
        'community_intelligence','market_structure','research_reliability']
    assert all(len(p.sections)>=3 for p in PAGES)


def test_page_registration_has_one_default_and_real_paths():
    st=FakeStreamlit()
    pages=register_pages(st,ROOT)
    assert all(Path(p.path).is_file() for p in pages)
    assert sum(p.default for p in pages)==1
    assert pages[0].default
    assert len({p.path for p in pages})==6


def test_all_python_sources_compile_and_no_chart_estimation():
    for f in [ROOT/'app.py',*page_files(ROOT),*(ROOT/'app').rglob('*.py')]:
        source=f.read_text(encoding='utf-8')
        ast.parse(source)
    for f in page_files(ROOT):
        source=f.read_text()
        assert 'read_parquet' not in source
        assert 'price_aed' not in source
        assert 'plotly' not in source


def test_plain_shell_escapes_hostile_html_and_marks_missing_values():
    st=FakeStreamlit()
    page_header(st,'<script>alert(1)</script>','<tag>')
    scope_badges(st,'P1 & P2')
    kpi_card(st,label='<img src=x onerror=alert(1)>',value=None,context='2021 < 2025')
    status_badge(st,'INCONCLUSIVE',note='not causally verified')
    evidence_panel(st,claim_id='<button>',restriction='Not causal')
    assert '&lt;script&gt;' in text_of(st)
    assert '<script>' not in text_of(st)
    assert '<img src=x' not in text_of(st)
    assert 'Not available' in text_of(st)
    assert '&lt;button&gt;' in text_of(st)
    assert 'P1 &amp; P2' in text_of(st)


def test_kpi_fixture_is_explicit_not_a_market_claim():
    st=FakeStreamlit()
    kpi_card(st,label='Illustration',value=42,unit='widgets',fixture=True)
    assert '[SYNTHETIC FIXTURE]' in text_of(st)
    assert display_value(float('nan'))=='Not available'
    assert display_value(float('inf'))=='Not available'
    assert display_value(None)=='Not available'

@pytest.mark.parametrize('reason',sorted(REASONS))
def test_all_empty_states_are_actionable(reason):
    st=FakeStreamlit()
    empty_state(st,reason)
    assert 'role="status"' in text_of(st)
    assert REASONS[reason][0] in text_of(st)
    assert REASONS[reason][1] in text_of(st)


def test_invalid_empty_state_rejected():
    with pytest.raises(ValueError): empty_state(FakeStreamlit(),'anything')


def test_unknown_scientific_status_fails_closed():
    st=FakeStreamlit()
    status_badge(st,'MAGICALLY_APPROVED')
    assert 'BLOCKED' in text_of(st)
    assert 'SUPPORTED' not in text_of(st)


def test_release_fails_closed_when_artifacts_missing(tmp_path):
    status=check_release(tmp_path)
    assert status.authorized is False
    assert status.status=='UNAVAILABLE'
    assert 'unavailable' in status.explanation.lower()


def test_claim_requires_real_integrity_and_claim_level_authorization(tmp_path):
    with pytest.raises(Exception):
        require_claim(tmp_path,'ACT01')


def test_shell_renders_without_scientific_artifacts(monkeypatch):
    st=FakeStreamlit()
    monkeypatch.setattr('app.components.layout.check_release',
                        lambda root:ReleaseView(False,'UNAVAILABLE','No validated artifacts'))
    render_shell(st,PAGES[0])
    content=text_of(st)
    assert 'research release' in content.lower()
    assert 'Research question' in content
    assert 'Registered activity' in content
    assert 'No validated artifacts' in content
    assert 'BLOCKED' in content
    assert '2021–2025' not in content or '2010–2025' in content


def test_approved_shell_still_displays_caveat(monkeypatch):
    st=FakeStreamlit()
    monkeypatch.setattr('app.components.layout.check_release',
        lambda root:ReleaseView(True,'APPROVED_WITH_QUALIFICATIONS','Limited release',15,36))
    render_shell(st,PAGES[2])
    content=text_of(st)
    assert 'approved with qualifications' in content.lower()
    assert 'claim-specific permissions' in content.lower()
    assert 'QUALIFIED' in content
    assert 'Raw versus matched pricing' in content


def test_all_six_pages_can_render_with_fake_streamlit(monkeypatch):
    st=FakeStreamlit()
    monkeypatch.setattr('app.analytics.pages.check_release',
        lambda root:ReleaseView(False,'UNAVAILABLE','Not loaded'))
    for p in PAGES:
        mod=__import__('app.pages.'+p.key,fromlist=['render'])
        mod.render(st)
    content=text_of(st)
    assert all(p.title in content for p in PAGES)


def test_app_entrypoint_uses_native_six_page_navigation(monkeypatch):
    st=FakeStreamlit()
    monkeypatch.setitem(sys.modules,'streamlit',st)
    import app as pkg
    spec=importlib.util.spec_from_file_location('phase2_entrypoint',ROOT/'app.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module,'check_release',lambda root:ReleaseView(False,'UNAVAILABLE','Missing'))
    module.main()
    assert len(st.pages)==6
    assert ('run',None,{}) in st.calls
    assert '🔒' in text_of(st)


def test_phase1_data_interfaces_reused_and_no_shadow_registry():
    runtime=(ROOT/'app/runtime.py').read_text()
    assert 'app_core.claim_permissions' in runtime
    assert 'app_core.integrity' in runtime
    assert not (ROOT/'app/artifact_registry.py').exists()
    assert not (ROOT/'app/metric_contracts.py').exists()


def test_mobile_css_and_keyboard_accessibility():
    assert '@media (max-width: 720px)' in CSS
    assert 'prefers-reduced-motion' in CSS
    assert 'focus:outline-none' not in CSS
    assert 'st.navigation' not in CSS
