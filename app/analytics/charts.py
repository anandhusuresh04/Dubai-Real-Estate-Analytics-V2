"""Plotly visual grammar. All input values must come from a verified exhibit frame."""
from __future__ import annotations
import pandas as pd
import re
from .catalog import Exhibit
from .gateway import EvidenceUnavailable, select_columns

COLORS=('#1879A2','#1C988D','#E3A54A','#627A9B','#A16894','#3D586C')
# Exact source bin edges are from Notebook 02 (COARSE), not inferred from values.
SIZE_EDGES={'Unit':(0,45,65,90,125,175,250,None),
            'Villa':(0,150,225,300,400,550,750,1100,None)}


def size_band_label(code:object)->str:
    import re
    match=re.fullmatch(r'(Unit|Villa):(\d{2})',str(code))
    if not match:return str(code)
    edges=SIZE_EDGES[match.group(1)]
    idx=int(match.group(2))
    if idx>=len(edges)-1:return str(code)
    lo,hi=edges[idx],edges[idx+1]
    return f'{lo:g}–{hi:g} m²' if hi is not None else f'>{lo:g} m²'


REGISTRATION_COLORS={'Ready':'#1879A2','Off-Plan':'#1C988D','Off Plan':'#1C988D',
                     'READY':'#1879A2','OFF_PLAN':'#1C988D','Off-plan':'#1C988D'}


def validated_chart_frame(frame:pd.DataFrame, spec:Exhibit)->tuple[pd.DataFrame,str,str,str|None]:
    x,y,color=select_columns(frame,spec)
    data=frame.copy()
    if spec.id=='size_elasticity':
        required={'property_type_label','outcome','beta'}
        if not required.issubset(data.columns):
            raise EvidenceUnavailable('Size–price model requires the Notebook 05 outcome, beta and property-type fields.')
        if data.duplicated(['property_type_label','outcome']).any():
            raise EvidenceUnavailable('Size–price model contains duplicate coefficient cells.')
        if not data['outcome'].isin(('log_price','log_psm')).all():
            raise EvidenceUnavailable('Unrecognized model outcome; no coefficient will be published.')
        if not pd.to_numeric(data['beta'],errors='coerce').notna().all():
            raise EvidenceUnavailable('Size–price model coefficient contains nonnumeric values.')
    if spec.kind!='table':
        if spec.kind!='bar' or spec.id not in ('index_endpoint','community_growth','contributions','size_mix'):
            # Prevent plotting synthetic trends from arbitrary duplicate cells.
            keys=[x]+([color] if color else [])
            if data.duplicated(keys).any():
                raise EvidenceUnavailable('This artifact contains multiple observations for the selected chart grain. Choose an approved design or narrower source grain.')
        data[y]=pd.to_numeric(data[y],errors='coerce')
        if not data[y].notna().any():
            raise EvidenceUnavailable('The expected approved numeric measure is absent or invalid.')
        data=data.loc[data[y].notna()].copy()
    if spec.kind=='scatter':
        data[x]=pd.to_numeric(data[x],errors='coerce')
        data=data.loc[data[x].notna()].copy()
    if data.empty:raise EvidenceUnavailable('No valid precomputed observations for this view.')
    return data,x,y,color


def make_figure(frame:pd.DataFrame, spec:Exhibit, *, area_names:dict[str,str]|None=None):
    """Build a figure without modifying the empirical estimator or aggregating."""
    import plotly.express as px
    from plotly import graph_objects as go
    df,x,y,color=validated_chart_frame(frame,spec)
    if spec.kind=='table':raise ValueError('Tables render with Streamlit dataframe, not Plotly.')
    # Display-only translation from audited community ID/name pairs; no row
    # joins, population changes, or regenerated price estimates.
    if spec.id in ('community_activity','community_prices') and color in ('area_key','area_id'):
        labels=area_names or {}
        if not labels and {'area_key','area_name'}.issubset(df.columns):
            pairs=df[['area_key','area_name']].dropna().drop_duplicates()
            pairs['id']=pairs['area_key'].astype(str).str.replace(r'\.0$', '',regex=True)
            if not pairs.groupby('id')['area_name'].nunique().gt(1).any():
                labels=dict(zip(pairs['id'],pairs['area_name'].astype(str)))
        def display_area(value):
            identifier=str(value).removesuffix('.0')
            name=labels.get(identifier)
            return f'{name} ({identifier})' if name else identifier
        df=df.copy()
        df['__community_label']=df[color].map(display_area)
        color='__community_label'
    if spec.id in ('budget','tail') and color is not None:
        def display_cutoff(value):
            try:
                number=float(value)
                if spec.id=='budget':return f'AED {number/1e6:g}M'
                return f'Top {number*100:g}%'
            except (ValueError,TypeError):
                return str(value)
        df=df.copy()
        df['__threshold_label']=df[color].map(display_cutoff)
        color='__threshold_label'
    kwargs={'x':x,'y':y,'color':color,'color_discrete_sequence':list(COLORS),
            'color_discrete_map':REGISTRATION_COLORS,'template':'plotly_white'}
    if spec.kind=='line':fig=px.line(df,markers=True,**kwargs)
    elif spec.kind=='bar':fig=px.bar(df,**kwargs)
    elif spec.kind=='scatter':fig=px.scatter(df,**kwargs)
    else:raise EvidenceUnavailable(f'Unsupported chart type: {spec.kind}')
    fig.update_layout(
        height=350,margin=dict(l=9,r=10,t=18,b=25),paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Arial, sans-serif',color='#264458',size=12),
        hovermode='x unified' if spec.kind=='line' else 'closest',
        legend=dict(orientation='h',yanchor='bottom',y=1.01,x=0,title=None,font=dict(size=11)),
        xaxis_title=None,yaxis_title=spec.unit,
    )
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor='#DAE6EB',tickfont=dict(color='#607788'))
    fig.update_yaxes(showgrid=True,gridcolor='#EDF2F5',zeroline=False,tickfont=dict(color='#607788'))
    if spec.kind=='line':fig.update_traces(line=dict(width=2.5),marker=dict(size=5))
    # Source contains endpoint observations, not interpolated annual values.
    if spec.id=='community_dispersion':
        fig.update_traces(mode='markers', marker=dict(size=11, symbol='circle'))
        fig.update_layout(hovermode='closest')
    if spec.id=='quarterly':
        # Categorical quarter labels: show sparse ticks, exact quarters remain in hover.
        unique=list(dict.fromkeys(df[x].astype(str).tolist()))
        step=max(1,(len(unique)+5)//6)
        tickvals=[unique[i] for i in range(0,len(unique),step)]
        ticktext=[re.sub(r'^(\d{4})[- ]?Q([1-4])$',r'\1 Q\2',v) for v in tickvals]
        fig.update_xaxes(type='category',tickmode='array',tickvals=tickvals,ticktext=ticktext,
                         tickangle=0,automargin=True)
    if spec.id=='size_price':
        fig.update_xaxes(title_text='Recorded area (m²)')
        fig.update_yaxes(tickformat='~s')
    if spec.id=='size_mix':
        codes=list(dict.fromkeys(df[x].astype(str)))
        fig.update_xaxes(tickmode='array',tickvals=codes,
                         ticktext=[size_band_label(code) for code in codes],tickangle=-25)
    if spec.id=='contributions':
        fig.update_yaxes(title_text='Change in registered transactions')
    # Do not overwrite Plotly Express per-point hover labels with a generic template.
    return fig


def exact_value(frame:pd.DataFrame, value_column:str, *, row:int=0):
    """Single already-computed source cell; not a summary across incompatible rows."""
    if value_column not in frame or len(frame)<=row:raise EvidenceUnavailable('KPI source cell missing.')
    value=pd.to_numeric(pd.Series([frame.iloc[row][value_column]]),errors='coerce').iloc[0]
    if pd.isna(value):raise EvidenceUnavailable('KPI measure not numeric.')
    return float(value)
