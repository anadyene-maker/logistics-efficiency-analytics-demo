import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Torre de Controle Semalo PRO", layout="wide")

st.title("🚀 Torre de Controle Logística - Semalo")
st.markdown("---")

st.sidebar.header("Painel de Controle")
uploaded_file = st.sidebar.file_uploader("Suba o arquivo CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
    
    # 1. LIMPEZA DE DADOS VAZIOS
    df = df.dropna(subset=['U.F', 'Logística Ent.']) # Remove linhas totalmente vazias
    
    # 2. PADRONIZAÇÃO DE COLUNAS
    if 'Logística Ent.' in df.columns: df['OPL'] = df['Logística Ent.']
    
    # 3. CONVERSÃO DE VALOR (Corrige o erro do print)
    if df['Vlr. Nota'].dtype == 'object':
        df['Vlr. Nota'] = df['Vlr. Nota'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

    # 4. TRATAMENTO DE DATAS
    colunas_data = ['Faturamento', 'Entrega', 'Data Agendamento']
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    df['Lead_Time'] = (df['Entrega'] - df['Faturamento']).dt.days
    df['OTD'] = (df['Entrega'] <= df['Data Agendamento']).astype(int)
    
    # --- FILTROS ---
    st.sidebar.subheader("Filtros de Região")
    ufs_disponiveis = sorted([x for x in df['U.F'].unique() if pd.notna(x)])
    uf_selecionada = st.sidebar.multiselect("Selecione o Estado (U.F)", options=ufs_disponiveis, default=ufs_disponiveis)
    
    df_filtrado = df[df['U.F'].isin(uf_selecionada)]

    # --- MÉTRICAS DE TOPO ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total Entregas", len(df_filtrado))
    c2.metric("⏱️ Lead Time Médio", f"{df_filtrado['Lead_Time'].mean():.1f} dias")
    c3.metric("✅ Eficiência OTD", f"{(df_filtrado['OTD'].mean()*100):.1f}%")
    
    # Formatação de Moeda Brasileira
    valor_total = df_filtrado['Vlr. Nota'].sum()
    c4.metric("💰 Valor Total", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # --- GRÁFICOS ---
    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.subheader("Performance por Operador")
        ranking = df_filtrado.groupby('OPL').agg(
            Eficiencia=('OTD', 'mean'),
            Prazo=('Lead_Time', 'mean'),
            Volume=('Vlr. Nota', 'count')
        ).reset_index()
        ranking['Eficiencia'] *= 100

        fig_bar = px.bar(ranking, x='OPL', y='Eficiencia', color='Prazo',
                         text_auto='.1f', title="Pontualidade % vs Velocidade (Cor)",
                         color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_dir:
        st.subheader("Análise de Risco (Volume vs Prazo)")
        fig_scatter = px.scatter(ranking, x='Prazo', y='Eficiencia', size='Volume', color='OPL',
                                 hover_name='OPL', title="Bolha maior = Mais Cargas")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.subheader("🔍 Detalhamento dos Dados")
    st.dataframe(df_filtrado[['Ordem Carga', 'OPL', 'Cidade.', 'U.F', 'Lead_Time', 'OTD', 'Vlr. Nota']], use_container_width=True)

else:
    st.info("Aguardando o envio da base de dados...")
