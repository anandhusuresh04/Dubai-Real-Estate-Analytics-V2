"""Additive Phase 3 chart styling; preserve existing approved Phase 2 visual identity."""
CSS="""<style>
.v3-page-intro{display:flex;align-items:flex-end;justify-content:space-between;gap:1.5rem;flex-wrap:wrap;margin:0 0 1.25rem;}
.v3-page-intro h3{font-size:1.08rem;line-height:1.6;font-weight:550;color:#344E62;margin:.25rem 0 0;max-width:850px;}
.v3-eyebrow{font-size:.67rem;letter-spacing:.13em;font-weight:800;color:#177D81;}
.v3-scope{font-size:.68rem;font-weight:700;letter-spacing:.05em;color:#637D8A;white-space:normal;}
.v3-scope span{padding:0 .4rem;color:#1F9C8F;}
.v3-section{margin:2.25rem 0 .8rem;border-top:1px solid #D9E5E9;padding-top:1.05rem;}
.v3-index{font-size:.67rem;font-weight:820;color:#188B88;letter-spacing:.13em;}
.v3-section h2{font-size:1.26rem;letter-spacing:-.025em;color:#122B41;margin:.35rem 0 .2rem;}
.v3-section p{font-size:.87rem;line-height:1.55;color:#637988;margin:0;max-width:870px;}
.v3-chart-head{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;margin:.1rem 0 .4rem;}
.v3-chart-head span{color:#102D42;font-size:1rem;font-weight:760;letter-spacing:-.016em;}
.v3-chart-head small{font-size:.68rem;color:#637E8C;font-weight:690;white-space:nowrap;}
.v3-unavailable{background:#F4F7F9;border:1px solid #DFE9EC;border-radius:10px;padding:1.15rem;color:#476275;font-size:.82rem;line-height:1.65;min-height:100px;}
.v3-unavailable strong{display:block;color:#1B3B50;font-size:.9rem;margin-bottom:.35rem;}
.v3-status-item{background:#FFF;border:1px solid #DDE7EB;border-radius:12px;padding:1rem;min-height:90px;display:flex;flex-direction:column;gap:.7rem;}
.v3-status-item small{font-weight:700;color:#5E7788;font-size:.72rem;}
.v3-status-item strong{font-size:.93rem;color:#15364B;letter-spacing:.02em;}
[data-testid="stMetric"]{background:#FFF;border:1px solid #DDE7EB;border-radius:13px;padding:1rem 1.25rem;min-height:110px;}
[data-testid="stMetricLabel"]{font-size:.76rem;color:#637B8A;}
[data-testid="stMetricValue"]{font-size:1.65rem;letter-spacing:-.035em;color:#10243A;font-weight:790;}
[data-testid="stVerticalBlockBorderWrapper"]:has(.v3-chart-head){border-radius:15px;}
[data-testid="stPlotlyChart"]{border-radius:12px;overflow:hidden;}
[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label{font-size:.76rem;color:#4E6877;}
@media (max-width:900px){.v3-section{margin-top:1.65rem;}.v3-page-intro{gap:.75rem;}}
@media (max-width:720px){[data-testid="stHorizontalBlock"]:has(.v3-chart-head){flex-direction:column;align-items:stretch;}
[data-testid="stHorizontalBlock"]:has(.v3-chart-head) > [data-testid="stColumn"]{width:100%;flex:1 1 auto;min-width:0;}
.v3-scope{font-size:.61rem;}.v3-section h2{font-size:1.15rem;}}

/* Phase 3 review: readable scientific evidence and predictable narrow layouts. */
[data-testid="stDataFrame"]{max-width:100%;}
[data-testid="stExpander"]{border-radius:10px;}
[data-testid="stPlotlyChart"]{min-width:0;}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;}
@media(max-width:900px){
 .v3-chart-head{align-items:flex-start;}
 .v3-page-intro h3{font-size:1rem;}
 [data-testid="stMetric"]{min-height:90px;}
}
@media(max-width:720px){
 .v3-section{margin:1.5rem 0 .7rem;}
 .v3-section h2{font-size:1.1rem;}
 .v3-chart-head span{font-size:.94rem;}
 .v3-chart-head small{font-size:.66rem;}
 .v3-status-item{min-height:70px;}
 [data-testid="stMetricValue"]{font-size:1.4rem;}
}
</style>"""

def apply_phase3_theme(st):st.markdown(CSS,unsafe_allow_html=True)
