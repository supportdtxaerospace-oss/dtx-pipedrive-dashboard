import base64
import io
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from sqlalchemy import create_engine

load_dotenv()
TZ = ZoneInfo("America/Sao_Paulo")

def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

def to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

def _b64(path, mime):
    with open(path, "rb") as f:
        return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"

logo1_b64 = _b64("logo1.jpg", "jpeg")
logo2_b64 = _b64("logo2.png", "png")
logo1_img  = Image.open("logo1.jpg")

st.set_page_config(
    page_title="DTX Aerospace | Commercial Pipeline",
    page_icon=logo1_img,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #F7F8FA; }
.block-container { padding: 2rem 3rem 2rem 3rem; max-width: 1400px; }

/* ── Topo ─────────────────────────── */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0A1F44;
    border-radius: 14px;
    padding: 22px 32px;
    margin-bottom: 28px;
}
.top-bar-left h1 {
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 700;
    margin: 0;
    letter-spacing: .4px;
}
.top-bar-left p {
    color: #7FA4C9;
    font-size: 12px;
    margin: 5px 0 0 0;
}
.top-bar-right {
    text-align: right;
    color: #7FA4C9;
    font-size: 12px;
    line-height: 1.8;
}
.top-bar-right span {
    color: #FFFFFF;
    font-weight: 600;
}

/* ── KPI Cards ────────────────────── */
.kpi {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px 24px;
    box-shadow: 0 1px 6px rgba(0,0,0,.07);
    border-top: 4px solid #0A1F44;
    height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi.green  { border-top-color: #10B981; }
.kpi.red    { border-top-color: #EF4444; }
.kpi.amber  { border-top-color: #F59E0B; }

.kpi-label { font-size: 11px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: .6px; }
.kpi-value { font-size: 30px; font-weight: 700; color: #0A1F44; line-height: 1; }
.kpi.green .kpi-value { color: #10B981; }
.kpi.red   .kpi-value { color: #EF4444; }
.kpi.amber .kpi-value { color: #F59E0B; }
.kpi-sub   { font-size: 11px; color: #9CA3AF; }

/* ── Section title ────────────────── */
.sec {
    font-size: 13px;
    font-weight: 700;
    color: #374151;
    text-transform: uppercase;
    letter-spacing: .6px;
    margin: 0 0 10px 2px;
}

/* ── Chart card ───────────────────── */
.chart-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 6px rgba(0,0,0,.07);
    margin-bottom: 20px;
}

/* ── Tabs ─────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 4px 6px;
    gap: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    margin-bottom: 20px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 22px;
    font-size: 13px;
    font-weight: 600;
    color: #6B7280;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #0A1F44 !important;
    color: #FFFFFF !important;
}

/* ── Table ────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

</style>
""", unsafe_allow_html=True)

def check_password():
    if st.session_state.get("authenticated"):
        return
    st.markdown(f"""
    <div style="max-width:400px;margin:80px auto;background:#FFFFFF;border-radius:16px;
                padding:40px;box-shadow:0 4px 24px rgba(0,0,0,.10);">
        <div style="text-align:center;margin-bottom:28px;">
            <img src="{logo1_b64}" style="height:90px;object-fit:contain;margin-bottom:12px;">
            <div style="font-size:13px;color:#9CA3AF;">
                Commercial Pipeline Dashboard
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        pwd = st.text_input("Senha de acesso", type="password", placeholder="Digite a senha")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if pwd == get_secret("APP_PASSWORD"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

check_password()

PALETTE = ["#0A1F44", "#1D6FA4", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"]
CHART_CFG = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Inter, sans-serif", color="#374151", size=12),
    margin=dict(t=20, b=20, l=20, r=20),
)


@st.cache_data(ttl=300)
def load():
    engine = create_engine(get_secret("DATABASE_URL"))
    df = pd.read_sql("SELECT * FROM deals", engine)
    df["end_of_lease"]  = pd.to_datetime(df["end_of_lease"],  errors="coerce")
    df["close_date"]    = pd.to_datetime(df["close_date"],    errors="coerce", utc=True)
    df["synced_at"]     = pd.to_datetime(df["synced_at"],     errors="coerce", utc=True)
    df["value"]         = pd.to_numeric(df["value"],          errors="coerce").fillna(0)
    df["lease_fee"]     = pd.to_numeric(df["lease_fee"],      errors="coerce")
    df["monthly_costs"] = pd.to_numeric(df["monthly_costs"],  errors="coerce")
    return df


deals = load()
now   = datetime.now(TZ)

# ── Top bar ───────────────────────────────────────────────────────────────────
last_sync = deals["synced_at"].max()
last_sync_str = last_sync.astimezone(TZ).strftime("%d/%m/%Y %H:%M") if pd.notna(last_sync) else "—"

st.markdown(f"""
<div class="top-bar">
  <div class="top-bar-left" style="display:flex;align-items:center;gap:18px;">
    <div style="background:#FFFFFF;border-radius:10px;padding:6px 10px;flex-shrink:0;">
      <img src="{logo2_b64}" style="height:64px;object-fit:contain;display:block;">
    </div>
    <div>
      <h1>Commercial Pipeline</h1>
      <p>Pipeline: DTX LDG &nbsp;·&nbsp; Dados atualizados automaticamente via Pipedrive</p>
    </div>
  </div>
  <div class="top-bar-right">
    🔄 Última sync &nbsp;<span>{last_sync_str} BRT</span><br>
    🕐 Agora &nbsp;<span>{now.strftime("%d/%m/%Y %H:%M")} BRT</span><br>
    📦 <span>{len(deals)} deals</span> carregados
  </div>
</div>
""", unsafe_allow_html=True)

# ── Botão de sync manual ───────────────────────────────────────────────────────
_, sync_col = st.columns([5, 1])
with sync_col:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        os.environ["DATABASE_URL"]    = get_secret("DATABASE_URL") or ""
        os.environ["PIPEDRIVE_TOKEN"] = get_secret("PIPEDRIVE_TOKEN") or ""
        import importlib, sync as sync_mod
        importlib.reload(sync_mod)
        with st.spinner("Sincronizando com Pipedrive..."):
            try:
                sync_mod.main()
                st.cache_data.clear()
                st.success("Dados atualizados!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro na sincronização: {e}")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["  Visão Executiva  ", "  Pipeline Comercial  ", "  Portfolio de Ativos  "])


def chart(fig, height=320):
    fig.update_layout(height=height, **CHART_CFG)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def interactive_chart(fig, height, key, df_source, filter_fn):
    fig.update_layout(height=height, **CHART_CFG)
    sel = st.plotly_chart(
        fig, use_container_width=True,
        config={"displayModeBar": False},
        on_select="rerun", key=key,
    )
    if sel and sel.selection and sel.selection.points:
        pt = sel.selection.points[0]
        filtered, titulo = filter_fn(pt, df_source)
        if filtered is not None and not filtered.empty:
            mostrar_deals(titulo, filtered)


@st.dialog("Detalhes dos Deals", width="large")
def mostrar_deals(titulo, df_modal):
    st.markdown(f'<p class="sec">{titulo}</p>', unsafe_allow_html=True)
    disp = df_modal[["title", "value", "status", "product", "platform", "revenue_type"]].copy()
    disp.columns = ["Deal", "Valor (USD)", "Status", "Produto", "Plataforma", "Tipo de Receita"]
    disp["Valor (USD)"]    = disp["Valor (USD)"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    disp["Status"]         = disp["Status"].map({"open": "🔵 Aberto", "won": "🟢 Ganho", "lost": "🔴 Perdido"})
    disp["Produto"]        = disp["Produto"].fillna("—")
    disp["Plataforma"]     = disp["Plataforma"].fillna("—")
    disp["Tipo de Receita"]= disp["Tipo de Receita"].fillna("—")
    st.dataframe(disp, use_container_width=True, hide_index=True)
    st.caption(f"{len(df_modal)} deal(s)  ·  Total: $ {df_modal['value'].sum():,.0f}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 · Visão Executiva
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    df = deals.copy()

    # ── Filtro de período ─────────────────────────────────────────────────────
    st.markdown('<p class="sec">Período de análise</p>', unsafe_allow_html=True)
    periodo_col, _ = st.columns([2, 5])
    with periodo_col:
        periodo = st.selectbox(
            "", ["Todos", "Últimos 30 dias", "Últimos 90 dias", "Últimos 180 dias", "Este ano"],
            label_visibility="collapsed",
        )

    hoje = now.date()
    if periodo == "Últimos 30 dias":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.date >= hoje - timedelta(days=30))]
    elif periodo == "Últimos 90 dias":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.date >= hoje - timedelta(days=90))]
    elif periodo == "Últimos 180 dias":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.date >= hoje - timedelta(days=180))]
    elif periodo == "Este ano":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.year == hoje.year)]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 5 KPIs ────────────────────────────────────────────────────────────────
    open_v      = df[df.status == "open"]["value"].sum()
    n_open      = (df.status == "open").sum()
    n_lost      = (df.status == "lost").sum()
    total_deals = len(df)
    book_total  = deals["book_value"].dropna().sum()
    maior_v     = deals[deals.status == "open"]["value"].max() if n_open > 0 else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    ticket_str = f"$ {open_v/n_open:,.0f}" if n_open > 0 else "—"

    k1.markdown(f'<div class="kpi"><div class="kpi-label">Pipeline Aberto</div><div class="kpi-value">$ {open_v:,.0f}</div><div class="kpi-sub">{n_open} deals ativos</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi green"><div class="kpi-label">Book Value Total</div><div class="kpi-value">$ {book_total:,.0f}</div><div class="kpi-sub">valor contábil dos ativos</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi red"><div class="kpi-label">Deals Perdidos</div><div class="kpi-value">{n_lost}</div><div class="kpi-sub">de {total_deals} no total</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi amber"><div class="kpi-label">Maior Deal</div><div class="kpi-value">$ {maior_v:,.0f}</div><div class="kpi-sub">maior deal em aberto</div></div>', unsafe_allow_html=True)
    k5.markdown(f'<div class="kpi"><div class="kpi-label">Ticket Médio</div><div class="kpi-value">{ticket_str}</div><div class="kpi-sub">média pipeline aberto</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Card maior deal em aberto ─────────────────────────────────────────────
    maior_deal = deals[(deals.status == "open") & (deals["value"] > 0)].nlargest(1, "value")
    if not maior_deal.empty:
        d = maior_deal.iloc[0]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0A1F44,#1D6FA4);border-radius:12px;
                    padding:18px 28px;margin-bottom:20px;display:flex;
                    align-items:center;justify-content:space-between;">
            <div>
                <div style="color:#7FA4C9;font-size:11px;font-weight:600;
                            text-transform:uppercase;letter-spacing:.6px;">
                    🎯 Maior Deal em Aberto
                </div>
                <div style="color:#FFFFFF;font-size:20px;font-weight:700;margin-top:4px;">
                    {d['title']}
                </div>
                <div style="color:#A8C4E0;font-size:13px;margin-top:2px;">
                    {d['org_name'] or '—'} &nbsp;·&nbsp; {d['product'] or '—'}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#10B981;font-size:28px;font-weight:700;">
                    $ {d['value']:,.0f}
                </div>
                <div style="color:#7FA4C9;font-size:12px;">
                    {d['revenue_type'] or '—'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Treemap (largura total) ───────────────────────────────────────────────
    st.markdown('<p class="sec">Distribuição de Valor por Produto e Organização</p>', unsafe_allow_html=True)
    tm = df.copy()
    tm["product"]  = tm["product"].fillna("Sem Produto")
    tm["org_name"] = tm["org_name"].fillna("Sem Organização")
    tm = tm[tm["value"] > 0]
    fig = px.treemap(
        tm, path=["product", "org_name"], values="value",
        color="product", color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$ %{value:,.0f}",
        textfont=dict(size=13),
        marker=dict(line=dict(width=2, color="white")),
    )
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))

    def filtro_treemap(pt, src):
        label  = pt.get("label", "")
        parent = pt.get("parent", "")
        if not label:
            return None, ""
        if parent and parent not in ("", "/"):
            filtered = src[src["org_name"].fillna("Sem Organização") == label]
            return filtered, f"Deals — {label}"
        else:
            filtered = src[src["product"].fillna("Sem Produto") == label]
            return filtered, f"Deals — Produto: {label}"

    interactive_chart(fig, 420, "treemap", deals, filtro_treemap)

    # ── Valor por Plataforma (largura total) ──────────────────────────────────
    st.markdown('<p class="sec">Valor por Plataforma</p>', unsafe_allow_html=True)
    pf_raw = df[df["platform"].notna()][["platform", "value"]].copy()
    pf_raw["platform"] = pf_raw["platform"].str.split(", ")
    pf_exp = pf_raw.explode("platform")
    pf_exp["platform"] = pf_exp["platform"].str.strip()
    pf = pf_exp.groupby("platform")["value"].sum().reset_index().sort_values("value", ascending=False)
    if not pf.empty:
        altura = max(300, len(pf) * 46)
        fig = px.bar(
            pf, x="value", y="platform", orientation="h",
            color_discrete_sequence=["#1D6FA4"],
            text=pf["value"].apply(lambda x: f"$ {x:,.0f}"),
        )
        fig.update_traces(textposition="inside", textfont=dict(color="white", size=12))
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis=dict(title="", showticklabels=False, showgrid=False),
            yaxis_title="", margin=dict(t=10, b=10, l=10, r=20),
        )

        def filtro_platform(pt, src):
            plat = pt.get("y", "")
            filtered = src[src["platform"].fillna("").str.contains(plat, regex=False)]
            return filtered, f"Deals — Plataforma: {plat}"

        interactive_chart(fig, altura, "platform", deals, filtro_platform)
    else:
        st.info("Nenhum deal com plataforma preenchida.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Deals por Estágio ─────────────────────────────────────────────────────
    st.markdown('<p class="sec">Pipeline por Estágio — Quantidade e Valor</p>', unsafe_allow_html=True)
    STAGE_NAMES = {
        13: "Quote / Offer",
        14: "Negotiation",
        15: "Contract / PO / LOI",
        16: "Execution / Delivery",
        17: "Post-Sale",
        18: "New Stage",
    }
    STAGE_IDS = {v: k for k, v in STAGE_NAMES.items()}

    estagio = deals[deals.status == "open"].groupby("stage_id").agg(
        quantidade=("pipedrive_id", "count"),
        valor=("value", "sum"),
    ).reset_index().sort_values("valor", ascending=True)
    estagio["stage"] = estagio["stage_id"].map(STAGE_NAMES).fillna("Estágio " + estagio["stage_id"].astype(str))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Valor (USD)", y=estagio["stage"], x=estagio["valor"],
        orientation="h", marker_color="#1D6FA4",
        text=estagio["valor"].apply(lambda x: f"$ {x:,.0f}"),
        textposition="inside", textfont=dict(color="white", size=12),
    ))
    fig.add_trace(go.Scatter(
        name="Qtd. Deals", y=estagio["stage"], x=estagio["valor"],
        mode="text",
        text=estagio["quantidade"].apply(lambda x: f"  {x} deal{'s' if x > 1 else ''}"),
        textposition="middle right", textfont=dict(color="#374151", size=12),
    ))
    fig.update_layout(
        showlegend=False,
        xaxis=dict(title="", showticklabels=False, showgrid=False),
        yaxis_title="", margin=dict(t=10, b=10, l=10, r=100),
    )

    def filtro_estagio(pt, src):
        stage_name = pt.get("y", "")
        stage_id   = STAGE_IDS.get(stage_name)
        if stage_id:
            filtered = src[src["stage_id"] == stage_id]
        else:
            filtered = src[src["stage_id"].astype(str) == stage_name.replace("Estágio ", "")]
        return filtered, f"Deals — {stage_name}"

    interactive_chart(fig, max(280, len(estagio) * 52), "estagio", deals, filtro_estagio)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top 5 Deals ───────────────────────────────────────────────────────────
    st.markdown('<p class="sec">Top 5 Maiores Deals</p>', unsafe_allow_html=True)
    top5 = df.nlargest(5, "value")[["title", "value", "status", "product", "revenue_type"]].copy()
    top5.columns = ["Deal", "Valor (USD)", "Status", "Produto", "Tipo de Receita"]
    top5["Valor (USD)"] = top5["Valor (USD)"].apply(lambda x: f"$ {x:,.0f}")
    top5["Status"] = top5["Status"].map({"open": "🔵 Aberto", "won": "🟢 Ganho", "lost": "🔴 Perdido"})
    st.dataframe(top5, use_container_width=True, hide_index=True)
    st.download_button("📥 Exportar Excel", to_excel_bytes(top5), "top5_deals.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="dl_top5")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 · Pipeline Comercial
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    df = deals.copy()

    STAGE_NAMES_T2 = {
        13: "Quote / Offer",
        14: "Negotiation",
        15: "Contract / PO / LOI",
        16: "Execution / Delivery",
        17: "Post-Sale",
        18: "New Stage",
    }
    STAGE_IDS_T2 = {v: k for k, v in STAGE_NAMES_T2.items()}

    # ── Filtro de período ─────────────────────────────────────────────────────
    st.markdown('<p class="sec">Período de análise</p>', unsafe_allow_html=True)
    periodo_col2, _ = st.columns([2, 5])
    with periodo_col2:
        periodo_t2 = st.selectbox(
            "", ["Todos", "Últimos 30 dias", "Últimos 90 dias", "Últimos 180 dias", "Este ano"],
            label_visibility="collapsed", key="periodo_t2",
        )

    hoje_t2 = now.date()
    if periodo_t2 == "Últimos 30 dias":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.date >= hoje_t2 - timedelta(days=30))]
    elif periodo_t2 == "Últimos 90 dias":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.date >= hoje_t2 - timedelta(days=90))]
    elif periodo_t2 == "Últimos 180 dias":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.date >= hoje_t2 - timedelta(days=180))]
    elif periodo_t2 == "Este ano":
        df = df[df["close_date"].notna() & (df["close_date"].dt.tz_convert(TZ).dt.year == hoje_t2.year)]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    n_open_t2    = (df.status == "open").sum()
    n_won_t2     = (df.status == "won").sum()
    n_lost_t2    = (df.status == "lost").sum()
    n_closed_t2  = n_won_t2 + n_lost_t2
    open_val_t2  = df[df.status == "open"]["value"].sum()
    ticket_t2    = f"$ {open_val_t2/n_open_t2:,.0f}" if n_open_t2 > 0 else "—"
    conv_rate_t2 = f"{n_won_t2/n_closed_t2*100:.1f}%" if n_closed_t2 > 0 else "—"

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi"><div class="kpi-label">Deals Abertos</div><div class="kpi-value">{n_open_t2}</div><div class="kpi-sub">deals ativos no pipeline</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><div class="kpi-label">Valor Total Pipeline</div><div class="kpi-value">$ {open_val_t2:,.0f}</div><div class="kpi-sub">soma dos deals abertos</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi amber"><div class="kpi-label">Ticket Médio</div><div class="kpi-value">{ticket_t2}</div><div class="kpi-sub">média por deal aberto</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi green"><div class="kpi-label">Taxa de Conversão</div><div class="kpi-value">{conv_rate_t2}</div><div class="kpi-sub">{n_won_t2} ganhos de {n_closed_t2} fechados</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Funil por Estágio (largura total) ────────────────────────────────────
    st.markdown('<p class="sec">Funil por Estágio</p>', unsafe_allow_html=True)
    sd = df.groupby("stage_id")["value"].sum().reset_index().sort_values("value", ascending=False)
    sd["stage"] = sd["stage_id"].map(STAGE_NAMES_T2).fillna("Estágio " + sd["stage_id"].astype(str))
    fig = px.funnel(sd, x="value", y="stage",
                    color_discrete_sequence=["#1D6FA4"])
    fig.update_traces(texttemplate="$ %{x:,.0f}", textfont=dict(size=12))
    fig.update_layout(yaxis_title="", xaxis_title="")

    def filtro_funil(pt, src):
        stage_name = pt.get("y", "")
        sid = STAGE_IDS_T2.get(stage_name)
        filtered = src[src["stage_id"] == sid] if sid else src
        return filtered, f"Deals — {stage_name}"

    interactive_chart(fig, 320, "funil_t2", deals, filtro_funil)

    # ── Valor por Produto (largura total) ────────────────────────────────────
    st.markdown('<p class="sec">Valor por Produto</p>', unsafe_allow_html=True)
    prod_df = df[df["product"].notna()].groupby("product")["value"].sum().reset_index().sort_values("value", ascending=False)
    fig = px.bar(prod_df, x="product", y="value",
                 color="product", color_discrete_sequence=PALETTE,
                 text=prod_df["value"].apply(lambda x: f"$ {x:,.0f}"))
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Valor (USD)",
                      margin=dict(t=30, b=10))

    def filtro_produto_t2(pt, src):
        prod = pt.get("x", "")
        filtered = src[src["product"].fillna("").str.contains(prod, regex=False)]
        return filtered, f"Deals — Produto: {prod}"

    interactive_chart(fig, 320, "produto_t2", deals, filtro_produto_t2)

    # ── Taxa de Conversão por Produto ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sec">Taxa de Conversão por Produto</p>', unsafe_allow_html=True)
    conv_src = deals[deals["product"].notna() & deals["status"].isin(["won", "lost"])].copy()
    if not conv_src.empty:
        conv_g = conv_src.groupby("product").agg(
            won=("status", lambda x: (x == "won").sum()),
            total=("status", "count"),
        ).reset_index()
        conv_g["taxa"] = (conv_g["won"] / conv_g["total"] * 100).round(1)
        conv_g = conv_g.sort_values("taxa", ascending=True)
        fig = px.bar(
            conv_g, x="taxa", y="product", orientation="h",
            color="taxa",
            color_continuous_scale=[[0, "#EF4444"], [0.5, "#F59E0B"], [1, "#10B981"]],
            text=conv_g["taxa"].apply(lambda x: f"{x:.1f}%"),
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            coloraxis_showscale=False,
            xaxis=dict(title="", ticksuffix="%", range=[0, 115], showgrid=False),
            yaxis_title="",
            margin=dict(t=10, b=10, l=10, r=60),
        )
        chart(fig, max(260, len(conv_g) * 56))
    else:
        st.info("Sem deals ganhos ou perdidos para calcular conversão por produto.")

    # ── Matrix Organização × Estágio ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sec">Matrix Organização × Estágio — Valor (USD)</p>', unsafe_allow_html=True)

    mx = deals[deals["org_name"].notna()].copy()
    mx["stage_name"] = mx["stage_id"].map(STAGE_NAMES_T2).fillna("Estágio " + mx["stage_id"].astype(str))
    stage_order = [STAGE_NAMES_T2[k] for k in sorted(STAGE_NAMES_T2) if STAGE_NAMES_T2[k] in mx["stage_name"].values]

    pivot = mx.pivot_table(index="org_name", columns="stage_name", values="value", aggfunc="sum").fillna(0)
    pivot = pivot.reindex(columns=[s for s in stage_order if s in pivot.columns])
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig = px.imshow(
        pivot,
        color_continuous_scale=[[0, "#F0F4FF"], [0.01, "#C7D9F5"], [1, "#0A1F44"]],
        text_auto=False,
        aspect="auto",
    )
    fig.update_traces(
        text=[[f"$ {v:,.0f}" if v > 0 else "—" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=11),
    )
    fig.update_layout(
        xaxis_title="", yaxis_title="",
        coloraxis_showscale=False,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    chart(fig, max(300, len(pivot) * 38))

    # ── Tabela completa de deals ──────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sec">Todos os Deals do Pipeline</p>', unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    f_stage   = fc1.selectbox("Estágio",  ["Todos"] + [STAGE_NAMES_T2.get(s, str(s)) for s in sorted(df["stage_id"].dropna().unique())], key="f_stage")
    f_product = fc2.selectbox("Produto",  ["Todos"] + sorted(df["product"].dropna().unique()), key="f_product")
    f_org     = fc3.selectbox("Organização", ["Todos"] + sorted(df["org_name"].dropna().unique()), key="f_org")

    tbl = df.copy()
    if f_stage   != "Todos": tbl = tbl[tbl["stage_id"] == STAGE_IDS_T2.get(f_stage)]
    if f_product != "Todos": tbl = tbl[tbl["product"].fillna("").str.contains(f_product, regex=False)]
    if f_org     != "Todos": tbl = tbl[tbl["org_name"] == f_org]

    disp_tbl = tbl[["title", "value", "status", "product", "platform", "stage_id"]].copy()
    disp_tbl["stage_id"] = disp_tbl["stage_id"].map(STAGE_NAMES_T2).fillna("—")
    disp_tbl["status"]   = disp_tbl["status"].map({"open": "🔵 Aberto", "won": "🟢 Ganho", "lost": "🔴 Perdido"})
    disp_tbl["value"]    = disp_tbl["value"].apply(lambda x: f"$ {x:,.0f}")
    disp_tbl.columns     = ["Deal", "Valor (USD)", "Status", "Produto", "Plataforma", "Estágio"]
    disp_tbl = disp_tbl.fillna("—")

    st.caption(f"{len(tbl)} deal(s) · Total: $ {tbl['value'].sum():,.0f}")
    st.dataframe(disp_tbl, use_container_width=True, hide_index=True)
    st.download_button("📥 Exportar Excel", to_excel_bytes(disp_tbl), "pipeline_comercial.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="dl_pipeline")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 · Portfolio de Ativos
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    df = deals.copy()
    in_180 = now.date() + timedelta(days=180)

    lease_df = df[df.end_of_lease.notna()].copy()
    lease_df["eol_date"] = lease_df.end_of_lease.dt.date

    # ── KPIs ──────────────────────────────────────────────────────────────────
    ativos_lease  = df["end_of_lease"].notna().sum()
    receita_mens  = df["lease_fee"].fillna(0).sum()
    custo_mens    = df["monthly_costs"].fillna(0).sum()
    margem_bruta  = receita_mens - custo_mens
    mg_class      = "green" if margem_bruta >= 0 else "red"

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi"><div class="kpi-label">Ativos com Lease</div><div class="kpi-value">{ativos_lease}</div><div class="kpi-sub">com data de vencimento</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi green"><div class="kpi-label">Receita Mensal</div><div class="kpi-value">$ {receita_mens:,.0f}</div><div class="kpi-sub">soma dos lease fees</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi red"><div class="kpi-label">Custo Mensal</div><div class="kpi-value">$ {custo_mens:,.0f}</div><div class="kpi-sub">soma dos custos mensais</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi {mg_class}"><div class="kpi-label">Margem Bruta</div><div class="kpi-value">$ {margem_bruta:,.0f}</div><div class="kpi-sub">lease fee − custo mensal</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Margem por Ativo ──────────────────────────────────────────────────────
    st.markdown('<p class="sec">Margem por Ativo (Lease Fee − Custo Mensal)</p>', unsafe_allow_html=True)
    mg_df = df[df["lease_fee"].notna() & df["monthly_costs"].notna()].copy()
    if not mg_df.empty:
        mg_df["margem"] = mg_df["lease_fee"] - mg_df["monthly_costs"]
        mg_df = mg_df.sort_values("margem", ascending=True)
        colors_mg = ["#10B981" if v >= 0 else "#EF4444" for v in mg_df["margem"]]
        fig = go.Figure(go.Bar(
            x=mg_df["margem"], y=mg_df["title"], orientation="h",
            marker_color=colors_mg,
            text=mg_df["margem"].apply(lambda x: f"$ {x:,.0f}"),
            textposition="outside",
        ))
        fig.update_layout(
            xaxis=dict(title="", showgrid=False, zeroline=True, zerolinecolor="#D1D5DB"),
            yaxis_title="", margin=dict(t=10, b=10, l=10, r=90),
        )
        chart(fig, max(300, len(mg_df) * 54))
    else:
        st.info("Sem dados suficientes para calcular margem por ativo.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Book Value vs Valor do Deal ───────────────────────────────────────────
    st.markdown('<p class="sec">Book Value vs Valor do Deal</p>', unsafe_allow_html=True)
    bv_df = df[df["book_value"].notna() & (df["value"] > 0)].copy()
    if not bv_df.empty:
        bv_df = bv_df.sort_values("book_value", ascending=False)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Book Value", x=bv_df["title"], y=bv_df["book_value"],
            marker_color="#0A1F44",
            text=bv_df["book_value"].apply(lambda x: f"$ {x:,.0f}"),
            textposition="outside",
        ))
        fig.add_trace(go.Bar(
            name="Valor do Deal", x=bv_df["title"], y=bv_df["value"],
            marker_color="#1D6FA4",
            text=bv_df["value"].apply(lambda x: f"$ {x:,.0f}"),
            textposition="outside",
        ))
        fig.update_layout(
            barmode="group", xaxis_tickangle=-30,
            legend=dict(orientation="h", y=1.1),
            xaxis_title="", yaxis_title="USD",
            margin=dict(t=40, b=60),
        )
        chart(fig, 380)
    else:
        st.info("Sem dados de book value para comparação.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Distribuição por Plataforma e Status ──────────────────────────────────
    st.markdown('<p class="sec">Distribuição por Plataforma e Status</p>', unsafe_allow_html=True)
    ps_src = df[df["platform"].notna()].copy()
    if not ps_src.empty:
        ps_src["platform"] = ps_src["platform"].str.split(", ")
        ps_exp = ps_src.explode("platform")
        ps_exp["platform"] = ps_exp["platform"].str.strip()
        ps_exp["status_label"] = ps_exp["status"].map({"open": "Aberto", "won": "Ganho", "lost": "Perdido"})
        ps_grp = ps_exp.groupby(["platform", "status_label"]).size().reset_index(name="count")
        fig = px.bar(
            ps_grp, x="platform", y="count", color="status_label",
            color_discrete_map={"Aberto": "#1D6FA4", "Ganho": "#10B981", "Perdido": "#EF4444"},
            barmode="group", text="count",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="", yaxis_title="Qtd. Deals",
            legend_title="Status", legend=dict(orientation="h", y=1.1),
            margin=dict(t=40, b=10),
        )
        chart(fig, max(320, ps_grp["platform"].nunique() * 70))
    else:
        st.info("Sem dados de plataforma para distribuição.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabela de ativos enriquecida ──────────────────────────────────────────
    st.markdown('<p class="sec">Todos os Ativos do Portfolio</p>', unsafe_allow_html=True)

    all_plats = sorted(df["platform"].dropna().str.split(", ").explode().str.strip().unique())
    tf1, tf2 = st.columns(2)
    f_plat_t3   = tf1.selectbox("Plataforma", ["Todas"] + all_plats, key="f_plat_t3")
    f_status_t3 = tf2.selectbox("Status", ["Todos", "🔵 Aberto", "🟢 Ganho", "🔴 Perdido"], key="f_status_t3")

    tbl3 = df.copy()
    if f_plat_t3 != "Todas":
        tbl3 = tbl3[tbl3["platform"].fillna("").str.contains(f_plat_t3, regex=False)]
    status_rev = {"🔵 Aberto": "open", "🟢 Ganho": "won", "🔴 Perdido": "lost"}
    if f_status_t3 != "Todos":
        tbl3 = tbl3[tbl3["status"] == status_rev[f_status_t3]]

    t3d = tbl3[["title", "platform", "status", "end_of_lease",
                 "lease_fee", "monthly_costs", "book_value"]].copy()
    t3d["margem"]    = t3d["lease_fee"] - t3d["monthly_costs"]
    t3d["dias_venc"] = t3d["end_of_lease"].apply(
        lambda x: (x.date() - now.date()).days if pd.notna(x) else None
    )
    t3d["status"]       = t3d["status"].map({"open": "🔵 Aberto", "won": "🟢 Ganho", "lost": "🔴 Perdido"})
    t3d["end_of_lease"] = t3d["end_of_lease"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "—")
    t3d["lease_fee"]    = t3d["lease_fee"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    t3d["monthly_costs"]= t3d["monthly_costs"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    t3d["book_value"]   = t3d["book_value"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    t3d["margem"]       = t3d["margem"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    t3d["dias_venc"]    = t3d["dias_venc"].apply(lambda x: f"{int(x)}d" if pd.notna(x) else "—")
    t3d.columns = ["Deal", "Plataforma", "Status", "Vencimento",
                   "Lease Fee", "Custo Mensal", "Book Value", "Margem", "Dias p/ Vencer"]
    t3d = t3d.fillna("—")

    st.caption(f"{len(tbl3)} ativo(s) · Receita: $ {tbl3['lease_fee'].sum():,.0f} · Custo: $ {tbl3['monthly_costs'].sum():,.0f}")
    st.dataframe(t3d, use_container_width=True, hide_index=True)
    st.download_button("📥 Exportar Excel", to_excel_bytes(t3d), "portfolio_ativos.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="dl_portfolio")
