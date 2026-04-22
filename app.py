import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Torre de Controle Semalo PRO", layout="wide")

st.title("🚀 Torre de Controle Logística - Semalo")
st.markdown("---")

# Barra lateral
st.sidebar.header("Painel de Controle")
uploaded_file = st.sidebar.file_uploader("Suba o arquivo CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
    df = df.dropna(subset=['Logística Ent.', 'U.F'])
    df['OPL'] = df['Logística Ent.']
    
    # Limpeza de valores
    def limpar_valor(valor):
        if isinstance(valor, str):
            valor = valor.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            try: return float(valor)
            except: return 0.0
        return float(valor) if pd.notna(valor) else 0.0

    df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_valor)

    # Tratamento de Datas
    colunas_data = ['Faturamento', 'Entrega', 'Data Agendamento']
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    df['Lead_Time'] = (df['Entrega'] - df['Faturamento']).dt.days
    df['OTD'] = (df['Entrega'] <= df['Data Agendamento']).astype(int)
    
    # Filtros
    ufs_limpas = sorted([str(x) for x in df['U.F'].unique() if pd.notna(x)])
    uf_selecionada = st.sidebar.multiselect("Selecione o Estado (U.F)", options=ufs_limpas, default=ufs_limpas)
    df_filtrado = df[df['U.F'].isin(uf_selecionada)].copy()

    # --- MÉTRICAS COM CORES ---
    st.subheader("Indicadores de Performance")
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("📦 Total Entregas", len(df_filtrado))
    
    lt_medio = df_filtrado['Lead_Time'].mean()
    c2.metric("⏱️ Lead Time Médio", f"{lt_medio:.1f} dias", delta=f"{lt_medio-7:.1f} (Meta 7)", delta_color="inverse")
    
    otd_medio = (df_filtrado['OTD'].mean() * 100)
    c3.metric("✅ Eficiência OTD", f"{otd_medio:.1f}%", delta=f"{otd_medio-85:.1f}% (Meta 85%)")
    
    vlr_total = df_filtrado['Vlr. Nota'].sum()
    c4.metric("💰 Faturamento em Trânsito", f"R$ {vlr_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # --- GRÁFICOS MELHORADOS ---
    col_esq, col_dir = st.columns(2)

    with col_esq:
        ranking = df_filtrado.groupby('OPL').agg(
            Eficiencia=('OTD', 'mean'),
            Prazo=('Lead_Time', 'mean')
        ).reset_index()
        ranking['Eficiencia'] *= 100

        # Gráfico com linha de meta
        fig_bar = px.bar(ranking, x='OPL', y='Eficiencia', color='Prazo',
                         text_auto='.1f', title="Nível de Serviço por OPL (Meta 85%)",
                         color_continuous_scale='RdYlGn_r')
        fig_bar.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="META OTD")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_dir:
        # Novo Gráfico: Faturamento por Estado
        fat_uf = df_filtrado.groupby('U.F')['Vlr. Nota'].sum().reset_index()
        fig_pie = px.pie(fat_uf, values='Vlr. Nota', names='U.F', title="Distribuição de Valor por Estado",
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico de Bolhas no final (Visão Geral)
    st.markdown("---")
    st.subheader("Mapa de Calor: Eficiência vs Velocidade")
    ranking_full = df_filtrado.groupby('OPL').agg(
        Eficiencia=('OTD', 'mean'),
        Prazo=('Lead_Time', 'mean'),
        Volume=('Vlr. Nota', 'count'),
        Valor=('Vlr. Nota', 'sum')
    ).reset_index()
    ranking_full['Eficiencia'] *= 100
    
    fig_scatter = px.scatter(ranking_full, x='Prazo', y='Eficiencia', size='Valor', color='OPL',
                             hover_name='OPL', title="Bolha maior = Maior Valor Financeiro Transportado")
    st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.info("Aguardando upload do CSV...")
