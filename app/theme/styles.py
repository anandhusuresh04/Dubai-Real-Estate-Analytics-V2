"""Dubai RE Analytics V2 — understated institutional design system.

Pure presentation CSS: no research numbers, remote assets, or scripted DOM changes.
Native Streamlit navigation and controls stay keyboard accessible.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Tokens:
    navy: str = '#10243A'
    blue: str = '#176D9E'
    teal: str = '#137D74'
    amber: str = '#A8752C'
    canvas: str = '#F4F7F8'
    muted: str = '#5E7180'

TOKENS = Tokens()

CSS = """
<style>
:root {
 --v2-navy:#10243A; --v2-blue:#176D9E; --v2-teal:#137D74;
 --v2-ink:#192E42; --v2-muted:#5E7180; --v2-line:#DFE7EB;
 --v2-canvas:#F4F7F8; --v2-ease:cubic-bezier(.2,.7,.2,1);
}
html, body, [data-testid="stApp"] {
 font-family: Inter, 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}
[data-testid="stAppViewContainer"] {background:#F4F7F8;color:#192E42;}
[data-testid="stMainBlockContainer"] {
 max-width:1550px; padding:1.3rem clamp(1.15rem,3vw,3.25rem) 3rem;
}
[data-testid="stHeader"] {background:transparent;}
/* Sidebar: preserve native Streamlit navigation/accessibility but give it product identity. */
[data-testid="stSidebar"] {
 background:#10243A; border-right:1px solid #22394D;
 min-width:264px; max-width:300px;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding-top:1rem;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {color:#B4C4D1;}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] {padding:0 .75rem;}
[data-testid="stSidebar"] [data-testid="stSidebarNav"]::before {
 content:'DUBAI  /  RESEARCH INTELLIGENCE'; display:block;
 padding:.65rem .85rem 1.35rem; font-size:.62rem; font-weight:800;
 letter-spacing:.15em; color:#8EA8BB; border-bottom:1px solid #294156;
 margin-bottom:1rem;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
 border-radius:10px; margin:.17rem .25rem; padding:.43rem .68rem;
 min-height:40px; transition:background 150ms var(--v2-ease);
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {background:#203D53;}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span,
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] p {color:#C9D6DF;font-weight:560;font-size:.88rem;}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
 background:#2C5368; box-shadow:inset 3px 0 0 #4BC3B3;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] p {color:white;font-weight:720;}
[data-testid="stSidebar"] button, [data-testid="stSidebar"] a {color:#DAE4EC;}
.v2-sidebar-brand {font-size:.86rem;font-weight:800;letter-spacing:.105em;color:white;margin:.55rem 0 .3rem;}
.v2-sidebar-caption {font-size:.75rem;line-height:1.65;color:#B3C7D4;margin:0 0 1.15rem;}
.v2-sidebar-meta {border-top:1px solid #31465A;padding:1rem .1rem .5rem;color:#B1C5D4;font-size:.74rem;line-height:1.8;}
.v2-sidebar-meta strong {display:block;color:#EAF4F8;font-size:.75rem;margin-bottom:.15rem;}
.v2-sidebar-dot {display:inline-block;width:.48rem;height:.48rem;background:#52B9A7;border-radius:50%;margin-right:.45rem;vertical-align:middle;}
.v2-sidebar-dot--off {background:#E8A39C;}
/* Top editorial hero establishes product identity without fabricated market metrics. */
.v2-hero {
 background:#10243A; border:1px solid #263F53; border-radius:19px;
 padding:clamp(1.3rem,2.5vw,2.2rem) clamp(1.35rem,2.7vw,2.5rem);
 color:white; position:relative; overflow:hidden; margin:.2rem 0 1.1rem;
}
.v2-hero::after {content:'';position:absolute;right:-5%;top:0;bottom:0;width:26%;
 background:repeating-linear-gradient(90deg,transparent 0,transparent 31px,rgba(255,255,255,.045) 32px,rgba(255,255,255,.045) 33px);
 pointer-events:none; transform:skew(-15deg);}
.v2-hero-top {display:flex;justify-content:space-between;align-items:center;gap:.6rem;flex-wrap:wrap;margin-bottom:.75rem;}
.v2-eyebrow {color:#81CFD1;font-size:.68rem;line-height:1.6;font-weight:800;text-transform:uppercase;letter-spacing:.16em;}
.v2-hero-index {border:1px solid #426076;border-radius:7px;color:#C1D4DD;padding:.25rem .55rem;font-weight:750;font-size:.68rem;letter-spacing:.08em;}
.v2-heading {color:#FFF;font-size:clamp(1.82rem,2.9vw,2.9rem);font-weight:780;line-height:1.11;letter-spacing:-.044em;margin:.2rem 0 .6rem;}
.v2-subtitle {color:#C0D2DD;font-size:clamp(.91rem,1.17vw,1.04rem);line-height:1.55;margin:0;max-width:800px;}
.v2-scope-row {display:flex;flex-wrap:wrap;gap:.48rem;margin-top:1.25rem;}
.v2-chip {display:inline-flex;align-items:center;border:1px solid #40596C;border-radius:6px;
 background:#203B4D;color:#D7E4EB;font-size:.70rem;font-weight:620;line-height:1.4;padding:.36rem .65rem;}
.v2-strip {display:flex;gap:1rem;align-items:center;justify-content:space-between;flex-wrap:wrap;
 background:#FFF;border:1px solid var(--v2-line);border-radius:11px;padding:.7rem .95rem;
 margin:0 0 1.35rem;box-shadow:0 2px 12px rgba(22,49,68,.025);}
.v2-strip-label {display:flex;align-items:center;gap:.6rem;color:var(--v2-ink);font-weight:720;font-size:.83rem;}
.v2-strip-sub {color:var(--v2-muted);font-size:.75rem;line-height:1.5;}
.v2-dot {display:inline-block;width:9px;height:9px;border-radius:50%;background:#179C86;flex:none;}
.v2-dot--blocked {background:#B64A49;}
.v2-section-head {display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:0 0 .8rem;}
.v2-section-title {color:var(--v2-navy);font-size:1.17rem;font-weight:770;letter-spacing:-.022em;line-height:1.25;}
.v2-section-meta {color:#6B7B88;font-size:.72rem;line-height:1.4;text-align:right;}
.v2-lead {color:var(--v2-navy);font-size:1.16rem;font-weight:725;letter-spacing:-.015em;line-height:1.43;margin:.15rem 0 .5rem;}
.v2-body {color:#576C7C;font-size:.86rem;line-height:1.67;margin:0;}
.v2-overview {display:grid;grid-template-columns:minmax(0,1.85fr) minmax(255px,1fr);gap:1.05rem;align-items:start;}
.v2-panel {background:white;border:1px solid var(--v2-line);border-radius:14px;padding:1.25rem 1.35rem;box-shadow:0 2px 13px rgba(15,37,52,.025);}
.v2-panel--ink {background:#EAF2F3;border-color:#D5E4E6;}
.v2-panel-kicker {font-size:.67rem;letter-spacing:.12em;text-transform:uppercase;color:#357C82;font-weight:800;margin-bottom:.65rem;}
.v2-side-label {font-size:.7rem;color:#607789;letter-spacing:.07em;font-weight:740;text-transform:uppercase;margin:1.15rem 0 .35rem;}
.v2-rule {height:1px;background:#E1E8EC;margin:1.1rem 0;}
.v2-modules {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.85rem;}
.v2-module {min-height:139px;display:flex;flex-direction:column;background:#FFF;
 border:1px solid #DCE6E9;border-radius:13px;padding:1.05rem 1.1rem;
 box-shadow:0 2px 12px rgba(15,37,52,.024);}
.v2-module-top {display:flex;align-items:center;justify-content:space-between;gap:.6rem;margin-bottom:.85rem;}
.v2-module-no {font-size:.72rem;font-weight:830;color:#177D81;font-variant-numeric:tabular-nums;letter-spacing:.09em;}
.v2-module-state {color:#667A88;background:#F1F5F7;border:1px solid #E5EDF0;border-radius:5px;font-size:.65rem;font-weight:730;padding:.22rem .5rem;white-space:nowrap;}
.v2-module-title {font-size:.97rem;font-weight:770;color:#122B41;letter-spacing:-.012em;margin-bottom:.42rem;}
.v2-module-desc {font-size:.79rem;line-height:1.52;color:#607483;}
.v2-module:last-child:nth-child(odd) {grid-column:1/-1;min-height:104px;}
.v2-evidence-layout {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.85rem;}
.v2-evidence-item {background:white;border:1px solid var(--v2-line);border-radius:12px;padding:1.05rem 1.15rem;}
.v2-evidence-name {font-size:.7rem;font-weight:790;letter-spacing:.09em;color:#46717B;text-transform:uppercase;margin-bottom:.45rem;}
.v2-evidence-text {font-size:.87rem;color:#284052;line-height:1.65;}
.v2-kpi-number {font-weight:780;color:#10243A;font-size:clamp(1.5rem,2.4vw,2.25rem);letter-spacing:-.04em;line-height:1.17;}
.v2-kpi-note {color:#637786;font-size:.8rem;line-height:1.5;margin-top:.5rem;}
.v2-kpi-unit {color:#657B88;font-size:.8rem;font-weight:600;margin-left:.35rem;}
.v2-card {background:#FFF;border:1px solid var(--v2-line);border-radius:13px;padding:1.2rem;min-height:135px;}
.v2-label {font-size:.73rem;text-transform:uppercase;letter-spacing:.1em;font-weight:750;color:#5B7281;margin-bottom:.55rem;}
.v2-status {display:inline-flex;align-items:center;border-radius:6px;font-size:.73rem;font-weight:750;padding:.35rem .65rem;border:1px solid;line-height:1.5;}
.v2-status--supported {background:#E6F4F0;color:#096856;border-color:#B8DED4;}
.v2-status--qualified {background:#FBF2E4;color:#865B14;border-color:#ECD8B8;}
.v2-status--inconclusive,.v2-status--not-estimable {background:#EBF0F3;color:#435A69;border-color:#D1DFE6;}
.v2-status--blocked {background:#FBEDEA;color:#9B3B36;border-color:#EBD0CC;}
.v2-placeholder {min-height:125px;border:1px solid #DCE6E9;border-radius:12px;padding:1rem 1.2rem;background:#FFF;display:flex;flex-direction:column;justify-content:center;gap:.4rem;}
.v2-placeholder-name {color:#1F3A4C;font-weight:730;font-size:.95rem;}
.v2-placeholder-desc {font-size:.81rem;color:#5F7584;line-height:1.55;}
.v2-callout {background:#EEF4F7;border-left:3px solid #237D89;border-radius:0 9px 9px 0;padding:1.05rem 1.15rem;color:#344D60;font-size:.84rem;line-height:1.65;}
.v2-footer {border-top:1px solid #D7E1E5;color:#667D88;padding:1.2rem 0 .45rem;font-size:.74rem;line-height:1.8;margin-top:1.5rem;}
/* Native tab affordances and inputs: accessible contrast without hiding focus states. */
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.55rem;}
[data-testid="stTabs"] [role="tab"] {font-weight:670;letter-spacing:-.01em;}
[data-testid="stTabs"] [aria-selected="true"] {color:#126878;}
/* Narrow laptop and mobile: no fixed-width grid columns or clipped information. */
@media (max-width:1120px) {
 .v2-overview {grid-template-columns:minmax(0,1.35fr) minmax(220px,1fr);}
 [data-testid="stMainBlockContainer"] {padding-left:1.4rem;padding-right:1.4rem;}
}
@media (max-width:850px) {
 .v2-overview {grid-template-columns:1fr;}
 .v2-modules {grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width: 720px) {
 [data-testid="stMainBlockContainer"] {padding:1rem .8rem 2rem;}
 .v2-hero {padding:1.3rem 1.15rem;border-radius:13px;}
 .v2-heading {font-size:1.75rem;}
 .v2-strip {align-items:flex-start;}
 .v2-modules,.v2-evidence-layout {grid-template-columns:1fr;}
 .v2-module:last-child:nth-child(odd) {grid-column:auto;}
 .v2-panel {padding:1rem;}
 .v2-section-head {align-items:flex-start;flex-direction:column;gap:.2rem;}
 .v2-section-meta {text-align:left;}
}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important;}}
</style>
"""

def apply_theme(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
