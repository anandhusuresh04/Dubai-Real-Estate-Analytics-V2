"""Interactive, source-labeled exhibit panels with explicit unavailable states."""
from __future__ import annotations
from html import escape
from dataclasses import replace
from pathlib import Path
import logging
import re
import pandas as pd
from .catalog import BY_ID, PAGE_EXHIBITS, Exhibit, MEASURE_OPTIONS, CLAIM_EXHIBIT_BINDINGS
from .gateway import EvidenceUnavailable, load_exhibit, published_claims, exact_period
from .charts import make_figure, validated_chart_frame, exact_value
from app_core.claim_permissions import Permissions
from app_core.artifact_registry import get_artifact

logger=logging.getLogger(__name__)


def _nice_float(value:float,unit:str)->str:
    if unit=='AED':
        return f'AED {value/1e9:,.2f} bn' if abs(value)>=1e9 else f'AED {value:,.0f}'
    if unit=='transactions':return f'{value:,.0f}'
    if unit=='percent':return f'{value:,.2f}%'
    return f'{value:,.2f}'


def _safe_note(st,msg:str):
    st.markdown('<div class="v3-unavailable"><strong>Evidence not available for this view</strong>'
                f'<div>{escape(str(msg))}</div></div>',unsafe_allow_html=True)


def _claim_control(st,root:Path,spec:Exhibit)->str|None:
    try:
        perms=Permissions.load(root)
        claims=tuple(x for x in published_claims(perms,spec.rq) if x in CLAIM_EXHIBIT_BINDINGS.get(spec.id,()))
    except Exception:
        logger.exception('Claim permission check failed for %s',spec.id)
        claims=()
    if not claims:
        _safe_note(st,'The chart requires an individually published claim AND an audited source-to-claim binding. The current Notebook 06 register does not authorize publication of this estimate.')
        return None
    return st.selectbox('Individually authorized claim',claims,key=f'claim_{spec.id}',
                        help='Only claims with published=True in the frozen subclaim register are selectable.')


def _filters(st,frame:pd.DataFrame,spec:Exhibit,*,area_names:dict[str,str]|None=None)->pd.DataFrame:
    """Only subset source rows. Never build a new estimator by grouping."""
    df=frame
    # 2026 is a provisional source year, not part of the frozen full-year
    # dashboard; reject it before any facet or trend is displayed.
    if 'year' in df.columns:
        df=exact_period(df)
    if 'year' in df.columns and 'year' not in spec.facets:
        ys=pd.to_numeric(df['year'],errors='coerce')
        years=sorted(set(ys.dropna().astype(int)) & set(range(2010,2026)))
        if years:
            if len(years)>1:
                start,end=st.select_slider('Historical window',options=years,value=(years[0],years[-1]),key=f'years_{spec.id}')
            else:start=end=years[0]
            df=exact_period(df,'year',start=start,end=end)
    # Extra dimensions are kept at one original recorded level, so no source
    # groups are averaged together merely for visualization.
    for facet in spec.facets:
        if facet not in df.columns:continue
        options=sorted(df[facet].dropna().astype(str).unique().tolist())
        if not options:raise EvidenceUnavailable(f'No recorded values for required facet {facet}.')
        preferred=('Residential' if facet=='usage_group' and 'Residential' in options else
                   'ALL_RESIDENTIAL' if 'ALL_RESIDENTIAL' in options else
                   'log_price' if facet=='outcome' and 'log_price' in options else
                   'True' if facet=='room_known' and 'True' in options else None)
        initial=options.index(preferred) if preferred is not None else (len(options)-1 if facet=='year' else 0)
        selected=st.selectbox(f'Fixed {facet.replace("_"," ")}',options,index=initial,key=f'facet_{spec.id}_{facet}',
                        help='Exact selection of an existing source dimension, never an aggregate of levels.')
        df=df.loc[df[facet].notna() & df[facet].astype(str).eq(selected)]
    if spec.id in ('decisions','claim_registry'):
        query=st.text_input('Search the research evidence catalog',key=f'search_{spec.id}',
             placeholder='Search RQ, claim ID, status or methodological restriction')
        if query.strip():
            searchable=[c for c in ('rq_id','upstream_claim_id','final_status',
                 'final_publication_status','restriction','reason','interpretation') if c in df.columns]
            if searchable:
                hit=pd.Series(False,index=df.index)
                for col in searchable:
                    hit=hit | df[col].astype('string').str.contains(query.strip(),case=False,regex=False,na=False)
                df=df.loc[hit]
    # A categorical selection is always a subset of a documented source dimension.
    if spec.segment:
        field=next((f for f in spec.segment if f in df.columns),None)
        if field:
            opts=sorted(df[field].dropna().astype(str).unique().tolist())
            if len(opts)>1:
                # Area comparisons limited to three, to keep the source grain readable.
                default=opts[:min(3,len(opts))] if field in ('area_id','area_key') else opts
                friendly={}
                if field in ('area_id','area_key') and 'area_name' in df.columns:
                    labels=df[[field,'area_name']].dropna().drop_duplicates()
                    if not labels[field].duplicated().any():
                        friendly={str(k):str(v) for k,v in zip(labels[field],labels.area_name)}
                if field=='budget_aed':
                    for v in opts:
                        try:friendly[v]=f'AED {float(v)/1e6:g}M'
                        except ValueError:pass
                if field=='tail_fraction':
                    for v in opts:
                        try:friendly[v]=f'Top {float(v)*100:g}%'
                        except ValueError:pass
                if area_names and field in ('area_id','area_key'):
                    friendly.update({v:area_names[_readable_id(v)] for v in opts
                        if _readable_id(v) in area_names and v not in friendly})
                chosen=st.multiselect(f'Compare {field.replace("_"," ")}',opts,
                        default=default,max_selections=3 if field in ('area_id','area_key') else None,
                        format_func=lambda v:(f'{friendly[v]} ({_readable_id(v)})'
                            if v in friendly and field in ('area_id','area_key')
                            else friendly.get(v,_readable_id(v))),
                        key=f'segment_{spec.id}')
                if not chosen:raise EvidenceUnavailable('Select at least one observed category.')
                df=df.loc[df[field].astype(str).isin(chosen)]
    if 'design' in df.columns and spec.id in ('matched_index','index_endpoint','matched_gap'):
        opts=sorted(df['design'].dropna().astype(str).unique().tolist())
        if len(opts)>1:
            design=st.selectbox('Fixed matching design',opts,key=f'design_{spec.id}')
            df=df.loc[df['design'].astype(str)==design]
    if df.empty:raise EvidenceUnavailable('No approved observations for the selected period or categories.')
    return df


def _readable_id(value:object)->str:
    """Presentation-only canonicalization; no changes to identifiers in source rows."""
    value=str(value)
    return value[:-2] if re.fullmatch(r"\d+\.0",value) else value


def _render_verified_table(st,filtered:pd.DataFrame,spec:Exhibit)->None:
    """Keep a short overview and provide every complete source field on demand."""
    data,x,y,_=validated_chart_frame(filtered,spec)
    priority=(x,y,'outcome','beta','se_cluster','n','communities','final_status',
              'final_publication_status','published','decision','restriction',
              'source_notebook','reason','cohort','status')
    cols=list(dict.fromkeys(c for c in priority if c in data.columns))
    if not cols:raise EvidenceUnavailable('Verified table has no approved display fields.')
    overview=data[cols].copy()
    for field in ('area_key','area_id'):
        if field in overview.columns:overview[field]=overview[field].map(_readable_id)
    if spec.id=='bedrooms' and 'term' in overview.columns:
        labels={'bed_0':'Studio','bed_2':'2 bedrooms','bed_3':'3 bedrooms',
                'bed_4':'4 bedrooms','bed_5':'5+ bedrooms'}
        overview['term']=overview['term'].astype(str).map(
            lambda v:f'{labels[v]} ({v})' if v in labels else v)
    if spec.id=='community_eligibility' and y=='matched_price_eligible':
        overview[y]=overview[y].astype(str).str.lower().map(
            {'true':'Eligible','false':'Not eligible'}).fillna('Not established')
    if spec.id=='source':
        # Hash and verification metadata are more useful as copyable provenance text
        # than as a mostly-empty seven-row table.
        st.caption('Frozen source digest (SHA-256) — exact recorded value')
        for digest in data[x].dropna().astype(str).unique():st.code(digest,language=None)
        if y in data.columns:st.caption(f'Verification field: {y} = {data[y].iloc[0]}')
        return
    st.dataframe(overview,hide_index=True,width='stretch',height=min(410,max(135,35*(len(overview)+1))),
                 column_config={c:st.column_config.TextColumn(c,width='large')
                                for c in ('restriction','reason','interpretation') if c in overview.columns}
                 if hasattr(st,'column_config') else None)
    # Show full untruncated restrictions and preserve all other source fields.
    if any(c in data.columns for c in ('restriction','reason','interpretation','final_publication_status')):
        with st.expander('Read complete evidence record',expanded=False):
            labels=[f'{i+1:02d} · {_readable_id(data.iloc[i][x])}' for i in range(len(data))]
            selected=st.selectbox('Source row',list(range(len(data))),
                format_func=lambda i:labels[i],key=f'record_{spec.id}')
            row=data.iloc[selected]
            for field,value in row.items():
                if pd.isna(value):continue
                st.markdown(f'**{field.replace("_"," ").title()}**')
                st.write(str(value))


def _render_parking_feasibility(st,df:pd.DataFrame,spec:Exhibit)->None:
    """Present exact support diagnostics, never a parking-effect estimate."""
    if len(df)!=1 or not {'parent_n','overlap_communities'}.issubset(df.columns):
        _render_verified_table(st,df,spec)
        return
    parent=exact_value(df,'parent_n')
    communities=exact_value(df,'overlap_communities')
    cols=st.columns(2,gap='small')
    with cols[0]:st.metric('Source parent observations',f'{parent:,.0f}')
    with cols[1]:st.metric('Communities with overlap',f'{communities:,.0f}')
    st.warning('Parking association: NOT ESTIMABLE under the research identification '
               'requirements. No parking premium is presented.')


def _chart_context(st,df:pd.DataFrame,spec:Exhibit)->None:
    """Source-driven editorial semantics without new statistical estimates."""
    if spec.id=='size_mix':
        st.caption('Notebook 02 fixed floor-area bands (m²) for Unit/Villa. '
                   'Selected metadata and registration filters can create narrow cohorts; '
                   'the chart shows source-recorded counts, not a population-normalized share.')
    elif spec.id=='budget':
        st.caption('Cumulative thresholds: each line is the share at or below its AED cutoff. '
                   'The lines overlap; do not add their percentages.')
    elif spec.id=='tail':
        st.caption('Tail fractions are source-defined: 0.01 = top 1%; 0.1 = top 10% '
                   'of transactions, with value shares precomputed upstream.')
    elif spec.id=='community_dispersion':
        st.caption('Only recorded endpoint observations are shown as separate markers; '
                   'intervening years have not been estimated.')
    elif spec.id=='contributions':
        st.caption('Signed contribution to the 2021–2025 difference in registered transactions, '
                   'using the frozen Notebook 03 category bridge. These are changes, not totals.')
    elif spec.id=='selection':
        st.caption('Population cohorts are separate audited selections, not additive funnel stages.')
    elif spec.id=='size_price':
        st.caption('Precomputed size bins, not individual transaction observations; '
                   'high-price Villas can widen the displayed scale.')


def _verified_area_names(root:Path)->dict[str,str]:
    """Optional labels from a separately verified Notebook 04 export; never infer names."""
    names={}
    try:
        profile=load_exhibit(root,BY_ID['community_prices'])
        if not {'area_key','area_name'}.issubset(profile.columns):return names
        clean=profile[['area_key','area_name']].dropna().drop_duplicates()
        clean['canonical']=clean.area_key.astype(str).map(_readable_id)
        # Refuse conflicting source names for the same identifier.
        if clean.groupby('canonical').area_name.nunique().gt(1).any():return names
        names=dict(zip(clean['canonical'],clean['area_name'].astype(str)))
    except Exception:
        logger.debug('Verified community-name source unavailable',exc_info=True)
    return names


def render_exhibit(st,root:Path,exhibit_id:str,*,compact:bool=False)->bool:
    spec=BY_ID[exhibit_id]
    with st.container(border=True):
        st.markdown(f'<div class="v3-chart-head"><span>{escape(spec.title)}</span>'
                    f'<small>{escape(spec.rq)} · {escape(spec.unit)}</small></div>',unsafe_allow_html=True)
        if spec.claim_sensitive:
            claim_id=_claim_control(st,root,spec)
            if not claim_id:return False
        else:claim_id=None
        try:
            df=load_exhibit(root,spec,claim_id=claim_id)
            if spec.id=='claim_registry':
                # A permission ledger can show withheld rows only as clearly
                # labeled audit records, never as a chart of findings.
                df=df.copy()
            names=_verified_area_names(root) if spec.id=='community_activity' else {}
            filtered=_filters(st,df,spec,area_names=names)
            allowed=[item for item in MEASURE_OPTIONS.get(spec.id,()) if item[0] in filtered.columns]
            if len(allowed)>1 and spec.kind!='table':
                lookup={label:(column,unit) for column,label,unit in allowed}
                choice=st.selectbox('Chart measure',list(lookup),key=f'measure_{spec.id}',
                    help='Switch between separately precomputed measures in this same approved cohort.')
                measure,unit=lookup[choice]
                spec=replace(spec,value=(measure,),unit=unit)
            if spec.kind=='table':
                if spec.id=='parking':_render_parking_feasibility(st,filtered,spec)
                else:_render_verified_table(st,filtered,spec)
            else:
                fig=make_figure(filtered,spec,area_names=names if spec.id=='community_activity' else None)
                st.plotly_chart(fig,width='stretch',config={'displaylogo':False,
                                'modeBarButtonsToRemove':['lasso2d','select2d']},key=f'chart_{spec.id}')
                _chart_context(st,filtered,spec)
            with st.expander('Source, population, and interpretation',expanded=False):
                source=get_artifact(spec.artifact)
                st.caption(f'Artifact: {source.relative_path.as_posix()} · Population/grain: {source.grain} · Research: {spec.rq}')
                st.write(spec.detail)
                if spec.claim_sensitive:st.caption(f'Individually authorized claim: {claim_id}')
                st.caption('Only source rows are presented. No median, price index, matched estimate, or model is recomputed in Streamlit.')
                st.download_button('Download verified view (CSV)',data=filtered.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f'{spec.id}_approved_view.csv',mime='text/csv',key=f'download_{spec.id}')
            return True
        except EvidenceUnavailable as exc:
            _safe_note(st,str(exc))
            with st.expander('Required source'):
                st.code(str(get_artifact(spec.artifact).relative_path))
                st.caption(spec.detail)
            return False
        except Exception:
            logger.exception('Unexpected dashboard presentation failure for exhibit: %s',spec.id)
            _safe_note(st,'Unexpected presentation failure. The analytical result has been withheld; inspect local app logs.')
            return False


def render_exhibit_grid(st,root:Path,ids:tuple[str,...]):
    """Render approved exhibits; consolidate repetitive unreleased-estimate cards."""
    sensitive=tuple(k for k in ids if BY_ID[k].claim_sensitive)
    # Only consolidate where *none* has a registered source-to-claim binding.
    # A later audited binding restores the original per-exhibit control.
    group_restricted=(len(sensitive)>=2 and
        all(not CLAIM_EXHIBIT_BINDINGS.get(k) for k in sensitive))
    visible=tuple(k for k in ids if k not in sensitive) if group_restricted else ids
    for k in range(0,len(visible),2):
        left,right=st.columns(2,gap='medium')
        with left:render_exhibit(st,root,visible[k])
        if k+1<len(visible):
            with right:render_exhibit(st,root,visible[k+1])
    if group_restricted:
        with st.container(border=True):
            st.markdown('<div class="v3-chart-head"><span>Qualified research — '
                'individual publication not authorized</span>'
                '<small>NOTEBOOK 06 · RELEASE CONTROL</small></div>',unsafe_allow_html=True)
            st.caption('The following frozen research exhibits are registered but cannot '
                'publish estimates until a claim is individually released and explicitly '
                'bound to its approved source:')
            for key in sensitive:
                spec=BY_ID[key]
                st.markdown(f'**{escape(spec.title)}** · {escape(spec.rq)}')
            st.info('This is an individual-claim publication restriction, not a missing '
                'dataset or a failed research notebook. The dashboard will not infer '
                'authorization from a qualified RQ-level decision.')


def render_annual_kpis(st,root:Path):
    """Only actual source cells for a single verified complete historical year."""
    spec=BY_ID['annual_count']
    cols=st.columns(3,gap='small')
    try:
        df=load_exhibit(root,spec)
        if 'year' not in df or 'n_transactions' not in df:raise EvidenceUnavailable('Annual count schema unavailable.')
        years=pd.to_numeric(df.year,errors='coerce')
        df=df.loc[years.between(2010,2025)].copy().sort_values('year')
        if df.empty or df.year.duplicated().any():raise EvidenceUnavailable('Historical year rows are not unique.')
        year=int(df.iloc[-1]['year'])
        row=df.loc[pd.to_numeric(df.year)==year]
        count=exact_value(row,'n_transactions')
        with cols[0]:st.metric(f'Registered transactions · {year}',_nice_float(count,'transactions'),help='P0 historical registered sales; not unique properties.')
        value_col='recorded_gross_value_aed'
        if value_col not in row:raise EvidenceUnavailable('Registered consideration column unavailable.')
        amount=exact_value(row,value_col)
        with cols[1]:st.metric(f'Nominal registered value · {year}',_nice_float(amount,'AED'),help='Recorded nominal AED; not market capitalization.')
        with cols[2]:st.metric('Historical observation period','2010–2025',help='2026 is provisional and excluded from these views.')
    except EvidenceUnavailable as exc:
        with cols[0]:st.metric('Registered transactions','Unavailable')
        with cols[1]:st.metric('Nominal recorded value','Unavailable')
        with cols[2]:st.metric('Observation period','2010–2025')
        st.caption(f'KPI publication withheld: {exc}')


def render_decision_summary(st,root:Path):
    """Only Notebook 06 research-decision metadata, never inferred market results."""
    try:
        df=load_exhibit(root,BY_ID['decisions'])
        statuses={str(row.rq_id):str(row.final_status) for row in df.itertuples(index=False)}
        important=[('RQ04','Registered activity'),('RQ05','Registration mix'),
                   ('RQ06','Predictive signal'),('RQ11','Matched registration comparison')]
        st.markdown('<div class="v3-section"><span class="v3-index">EVIDENCE SNAPSHOT</span>'
                    '<h2>What the research establishes</h2><p>Research-question status is not individual-claim authorization.</p></div>',
                    unsafe_allow_html=True)
        cards=st.columns(4)
        for i,(rq,label) in enumerate(important):
            with cards[i]:
                status=statuses.get(rq,'UNAVAILABLE')
                st.markdown(f'<div class="v3-status-item"><small>{escape(rq)} · {escape(label)}</small>'
                            f'<strong>{escape(status)}</strong></div>',unsafe_allow_html=True)
        st.caption('These are decisions from the verified Notebook 06 register, not guarantees for every subclaim.')
    except EvidenceUnavailable:
        _safe_note(st,'Notebook 06 research-decision metadata are not available.')
