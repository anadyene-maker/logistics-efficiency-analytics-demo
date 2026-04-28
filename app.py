import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Semalo - Eficiência MT", layout="wide")

# --- FUNÇÃO DE LIMPEZA ---
def carregar_dados(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file, sep=None, engine='python', encoding='latin1')
    else:
        df = pd.read_excel(file)
    df.columns = [c.strip() for c in df.columns]
    for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    return df

# --- MAPEAMENTO REGIONAL ---
def definir_regiao(cidade):
    cidade = str(cidade).upper()
    if cidade in ['CUIABA', 'VARZEA GRANDE']: return 'Baixada Cuiabana'
    elif cidade in ['SINOP', 'SORRISO', 'LUCAS DO RIO VERDE']: return 'Norte (Eixo 163)'
    elif cidade in ['RONDONOPOLIS', 'PRIMAVERA DO LESTE']: return 'Sul/Sudeste'
    return 'Demais Regiões'

# --- SIDEBAR ---
st.sidebar.header("🕹️ Filtros de Operação")
arquivo = st.sidebar.file_uploader("Suba o relatório Sankhya", type=['csv', 'xlsx'])

if arquivo:
    df = carregar_dados(arquivo)
    df_mt = df[df['U.F'] == 'MT'].copy()
    df_mt['Regiao'] = df_mt['Cidade.'].apply(definir_regiao)

    regioes_sel = st.sidebar.multiselect("Regiões", df_mt['Regiao'].unique(), default=df_mt['Regiao'].unique())
    data_min, data_max = df_mt['Faturamento'].min().date(), df_mt['Faturamento'].max().date()
    periodo = st.sidebar.date_input("Período", [data_min, data_max])

    df_final = df_mt[df_mt['Regiao'].isin(regioes_sel)].copy()
    if len(periodo) == 2:
        df_final = df_final[(df_final['Faturamento'].dt.date >= periodo[0]) & (df_final['Faturamento'].dt.date <= periodo[1])]

    # CÁLCULOS
    df_final['OTD'] = np.where(df_final['Entrega'] <= df_final['Data Agendamento'], 1, 0)
    df_final['Lead_Time'] = (df_final['Entrega'] - df_final['Faturamento']).dt.days

    # DASHBOARD VISUAL
    st.title("📈 Performance Logística - Mato Grosso")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Pedidos", len(df_final))
    otd_geral = df_final['OTD'].mean() * 100
    m2.metric("OTD Médio (Eficiência)", f"{otd_geral:.1f}%")
    m3.metric("Lead Time Médio", f"{df_final['Lead_Time'].mean():.1f} dias")

    st.subheader("📊 Eficiência por Região (OTD%)")
    fig = px.bar(df_final.groupby('Regiao')['OTD'].mean().reset_index(), x='Regiao', y='OTD', text_auto='.1%')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔍 Detalhamento das Entregas")
    st.dataframe(df_final[['Ordem Carga', 'Cidade.', 'Regiao', 'Lead_Time', 'OTD']], use_container_width=True)

    # --- RELATÓRIO AUTOMÁTICO (Agora dentro do bloco correto) ---
    st.markdown("---")
    st.subheader("📝 Relatório de Análise Operacional")
    
    pior_regiao = df_final.groupby('Regiao')['OTD'].mean().idxmin()
    pior_valor = df_final.groupby('Regiao')['OTD'].mean().min() * 100

    relatorio = f"""
    **Data da Análise:** {pd.Timestamp.now().strftime('%d/%m/%Y')}  
    **Objeto:** Avaliação de Performance de Entrega - Mato Grosso.

    1. **Eficiência Geral:** O índice de OTD atual é de **{otd_geral:.1f}%**. 
    2. **Gargalo Regional:** A região com maior criticidade é **{pior_regiao}**, com apenas **{pior_valor:.1f}%** de sucesso. 
    3. **Conclusão:** Os dados indicam a necessidade de revisão operacional nas rotas críticas para atingir a meta de 90%.
    """
    st.info(relatorio)

else:
    st.info("Aguardando upload do arquivo...")
