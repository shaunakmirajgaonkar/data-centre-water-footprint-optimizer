from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='AquaCompute Local', page_icon='💧', layout='wide')
st.markdown('''<style>
.stApp{background:#f7fafc;color:#172033}.block-container{max-width:1450px;padding-top:1.4rem}
[data-testid="stSidebar"]{background:#eef7f6;border-right:1px solid #d7e7e5}
h1,h2,h3{color:#172033!important}.stMarkdown,p,label{color:#435066}
.hero{background:linear-gradient(135deg,#e7fbf5,#f2f7ff);border:1px solid #d5e9e4;border-radius:24px;padding:28px 32px;margin-bottom:18px}
.badge{display:inline-block;background:#d8f5ed;color:#126b5a;border-radius:99px;padding:6px 11px;margin-right:6px;font-size:12px;font-weight:800}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e1e8ef;border-radius:16px;padding:12px}
</style>''', unsafe_allow_html=True)

DATA=Path(__file__).parent/'data'/'synthetic_datacentre_water_registry.csv'
REQUIRED=['record_id','site_code','date','region','workload_index','compute_hours','cooling_load_mwh','ambient_temp_c','relative_humidity_pct','pue','water_withdrawal_l','water_consumption_l','water_reuse_pct','electricity_renewable_pct','local_water_stress_score','cooling_efficiency_score','cooling_system','server_utilization_pct','peak_load_pct','rainfall_mm','grid_carbon_intensity_gco2_kwh','review_status']

def classify(x):
    if x<25:return 'Low Water Concern'
    if x<50:return 'Moderate Water Concern'
    if x<75:return 'High Water Concern'
    return 'Critical Water Concern'

def score(r):
    cooling=np.clip(r.cooling_load_mwh/260*100,0,100); heat=np.clip((r.ambient_temp_c-18)/20*100,0,100); humidity=np.clip((70-r.relative_humidity_pct)/45*100,0,100)
    return float(np.clip(.24*cooling+.22*r.local_water_stress_score+.14*(100-r.cooling_efficiency_score)+.12*heat+.10*(100-r.water_reuse_pct)+.07*r.workload_index+.06*r.server_utilization_pct+.05*humidity,0,100))

@st.cache_data
def load(): return pd.read_csv(DATA)

df=load(); up=st.sidebar.file_uploader('Upload authorized CSV',type='csv')
if up:
    try:
        x=pd.read_csv(up); missing=[c for c in REQUIRED if c not in x.columns]
        if missing: st.sidebar.error('Missing columns: '+', '.join(missing))
        else: df=x.copy(); st.sidebar.success(f'Loaded {len(df)} records locally')
    except Exception as e: st.sidebar.error(str(e))

df['date']=pd.to_datetime(df['date'],errors='coerce'); df['water_concern_score']=df.apply(score,axis=1); df['classification']=df.water_concern_score.map(classify)

st.sidebar.markdown('### Workspace'); sites=sorted(df.site_code.astype(str).unique()); regions=sorted(df.region.astype(str).unique())
sf=st.sidebar.multiselect('Sites',sites,sites); rf=st.sidebar.multiselect('Regions',regions,regions); threshold=st.sidebar.slider('Priority threshold',0,100,50)
v=df[df.site_code.astype(str).isin(sf)&df.region.astype(str).isin(rf)].copy(); p=v[v.water_concern_score>=threshold].sort_values('water_concern_score',ascending=False)

st.markdown('''<div class="hero"><span class="badge">100% LOCAL</span><span class="badge">NO EXTERNAL APIs</span><span class="badge">EXPLAINABLE</span><span class="badge">HUMAN REVIEW</span><h1>💧 AquaCompute Local</h1><p style="font-size:17px">Data-Centre Water Footprint Optimizer — screen water-pressure signals and compare transparent planning scenarios using cooling, weather, workload, reuse and local water-stress context.</p><p>Planning estimates only; not a certified water footprint, compliance assessment, or guarantee of savings.</p></div>''',unsafe_allow_html=True)

a,b,c,d=st.columns(4); a.metric('Records screened',f'{len(v):,}'); b.metric('Withdrawal',f'{v.water_withdrawal_l.sum()/1e6:.2f} ML'); c.metric('Consumption',f'{v.water_consumption_l.sum()/1e6:.2f} ML'); d.metric('Average reuse',f'{v.water_reuse_pct.mean():.1f}%')

st.header('Decision cockpit'); trend=v.groupby('date',as_index=False).agg(withdrawal=('water_withdrawal_l','sum'),consumption=('water_consumption_l','sum'))
fig=px.line(trend,x='date',y=['withdrawal','consumption'],markers=True,title='Water-use trajectory'); fig.update_layout(template='plotly_white',height=340); st.plotly_chart(fig,use_container_width=True)

c1,c2,c3=st.columns(3)
with c1:
    fig=px.scatter(v,x='cooling_load_mwh',y='water_consumption_l',size='workload_index',color='local_water_stress_score',hover_name='site_code',title='Cooling load vs consumption'); fig.update_layout(template='plotly_white',height=320); st.plotly_chart(fig,use_container_width=True)
with c2:
    z=v.groupby('cooling_system',as_index=False).water_consumption_l.mean(); fig=px.bar(z,x='cooling_system',y='water_consumption_l',title='Average consumption by cooling system'); fig.update_layout(template='plotly_white',height=320); st.plotly_chart(fig,use_container_width=True)
with c3:
    fig=px.scatter(v,x='ambient_temp_c',y='water_consumption_l',color='water_reuse_pct',size='peak_load_pct',hover_name='site_code',title='Weather and reuse context'); fig.update_layout(template='plotly_white',height=320); st.plotly_chart(fig,use_container_width=True)

st.header('Priority review')
if p.empty: st.info('No records meet the selected threshold.')
else:
    show=['record_id','site_code','date','region','water_concern_score','classification','water_consumption_l','local_water_stress_score','cooling_efficiency_score','water_reuse_pct']; st.dataframe(p[show],use_container_width=True,hide_index=True)

st.header('Explainable record view')
if len(v):
    rid=st.selectbox('Select record',v.record_id.astype(str).tolist()); r=v[v.record_id.astype(str)==rid].iloc[0]
    factors=pd.Series({'Water stress':r.local_water_stress_score,'Cooling load':np.clip(r.cooling_load_mwh/260*100,0,100),'Cooling inefficiency':100-r.cooling_efficiency_score,'Reuse gap':100-r.water_reuse_pct,'Ambient heat':np.clip((r.ambient_temp_c-18)/20*100,0,100),'Workload':r.workload_index,'Server utilization':r.server_utilization_pct}).sort_values()
    x1,x2=st.columns([.8,1.2]); x1.metric('Water-concern score',f'{r.water_concern_score:.1f}/100'); x1.write('**Classification:** '+r.classification); x1.write('**Cooling:** '+r.cooling_system); x1.write('**Water stress:** '+f'{r.local_water_stress_score:.0f}/100')
    fig=px.bar(factors,orientation='h',title='Driver index'); fig.update_layout(template='plotly_white',height=350); x2.plotly_chart(fig,use_container_width=True)

st.header('Optimization sandbox'); st.caption('Transparent scenario screening; not a calibrated physical cooling model.')
s1,s2,s3=st.columns(3); eff=s1.slider('Cooling-efficiency improvement',0,40,10,5); reuse=s2.slider('Water-reuse improvement',0,60,15,5); load=s3.slider('Workload reduction',0,30,5,5)
sc=v.copy(); sc['scenario_score']=np.clip(.24*np.clip(sc.cooling_load_mwh/260*100,0,100)+.22*sc.local_water_stress_score+.14*(100-np.clip(sc.cooling_efficiency_score+eff,0,100))+.12*np.clip((sc.ambient_temp_c-18)/20*100,0,100)+.10*(100-np.clip(sc.water_reuse_pct+reuse,0,100))+.07*np.clip(sc.workload_index-load,0,100)+.06*sc.server_utilization_pct+.05*np.clip((70-sc.relative_humidity_pct)/45*100,0,100),0,100)
base=v.water_concern_score.mean(); new=sc.scenario_score.mean(); q1,q2=st.columns(2); q1.metric('Baseline score',f'{base:.1f}'); q2.metric('Scenario score',f'{new:.1f}',delta=f'{new-base:.1f}')
st.dataframe(sc[['record_id','site_code','water_concern_score','scenario_score']].sort_values('scenario_score',ascending=False),use_container_width=True,hide_index=True)

st.header('Export'); out=v.copy(); out.water_concern_score=out.water_concern_score.round(2); st.download_button('⬇ Download scored registry',out.to_csv(index=False).encode(),'aquacompute_scored_registry.csv','text/csv'); st.info('Responsible use: synthetic or authorized local records only. Review consequential water-management decisions with qualified professionals.')
