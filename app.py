import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Semalo - Control Tower PRO", layout="wide")

def limpar_valor(valor):
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return pd.to_numeric(valor, errors='coerce')
    return valor

# --- SIDEBAR (FILTROS E PARÂMETROS) ---
st.sidebar.header("⚙️ Configurações e Filtros")

arquivo = st.sidebar.file_uploader("1. Suba o relatório Sankhya", type=['csv'])

# Só mostramos os outros filtros se o arquivo existir
if arquivo:
    df = pd.read_csv(arquivo, sep=';', encoding='latin1')
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamentos Essenciais
    df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_valor)
    for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    # --- FILTRO DE UF ---
    st.sidebar.markdown("---")
    lista_ufs = sorted(df['U.F'].unique().astype(str))
    ufs_selecionadas = st.sidebar.multiselect("2. Selecione as UFs", options=lista_ufs, default=lista_ufs)

    # --- FILTRO DE DATAS ---
    min_date = df['Faturamento'].min().date()
    max_date = df['Faturamento'].max().date()
    periodo = st.sidebar.date_input("3. Período de Faturamento", [min_date, max_date])

    # --- PARÂMETRO DE AUDITORIA ---
    st.sidebar.markdown("---")
    aliquota = st.sidebar.number_input("4. Alíquota ICMS (%)", value=12.0) / 100

    # --- APLICAÇÃO DOS FILTROS NO DF ---
    mask = (df['U.F'].isin(ufs_selecionadas))
    if len(periodo) == 2:
        mask = mask & (df['Faturamento'].dt.date >= periodo[0]) & (df['Faturamento'].dt.date <= periodo[1])
    
    df_filtrado = df.loc[mask].copy()

    # --- CÁLCULOS LOGÍSTICOS E TRIBUTÁRIOS ---
    df_filtrado['Lead_Time'] = (df_filtrado['Entrega'] - df_filtrado['Faturamento']).dt.days
    df_filtrado['OTD'] = np.where(df_filtrado['Entrega'] <= df_filtrado['Data Agendamento'], 1, 0)
    df_filtrado['ICMS_Esperado'] = df_filtrado['Vlr. Nota'] * aliquota
    df_filtrado['Status_Auditoria'] = np.where(df_filtrado['Vlr. Nota'] > 10000, "🚨 Revisar", "✅ OK")

    # --- DASHBOARD ---
    st.title("🚀 Torre de Controle Semalo")
    
    # Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Pedidos", len(df_filtrado))
    m2.metric("OTD Médio", f"{(df_filtrado['OTD'].mean()*100):.1f}%")
    m3.metric("Lead Time Médio", f"{df_filtrado['Lead_Time'].mean():.1f} dias")
    m4.metric("Vlr Total Filtrado", f"R$ {df_filtrado['Vlr. Nota'].sum():,.2f}")

    # Gráfico de Eficiência por UF
    st.subheader("Performance por Estado")
    fig_uf = px.bar(df_filtrado.groupby('U.F')['OTD'].mean().reset_index(), 
                    x='U.F', y='OTD', text_auto='.2%',
                    title="Nível de Serviço (OTD) por UF",
                    color_discrete_sequence=['#636EFA'])
    st.plotly_chart(fig_uf, use_container_width=True)

    # Tabela com Auditoria
    st.subheader("🔍 Detalhe de Cargas e Compliance")
    st.dataframe(df_filtrado[['Ordem Carga', 'Logística Ent.', 'U.F', 'Vlr. Nota', 'Lead_Time', 'Status_Auditoria']], 
                 use_container_width=True)

else:
    st.info("Aguardando upload do arquivo para carregar os filtros...")
