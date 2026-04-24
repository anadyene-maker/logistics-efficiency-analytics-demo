import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Semalo - Eficiência Logística & Compliance 4.0 ", layout="wide")

# --- FUNÇÕES DE APOIO (A "Lógica" por trás) ---
def limpar_moeda(valor):
    """Explicação: O Sankhya traz R$ e pontos. Essa função limpa isso para o Python somar."""
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return pd.to_numeric(valor, errors='coerce')
    return valor

# --- INTERFACE PRINCIPAL ---
st.title("🚀 Torre de Controle Semalo PRO")
st.markdown("---")

# 1. Upload do Arquivo (Substituindo o nome de arquivo fixo)
arquivo = st.sidebar.file_uploader("Upload do Relatório Sankhya (CSV)", type=['csv'])

if arquivo is not None:
    # Lendo o arquivo - sep=None faz o pandas descobrir se é , ou ; sozinho
    df = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin1')
    
    # Tratamento inicial de colunas (Lógica de Código Limpo)
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento de Datas
    for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    
    # Tratamento de Valores
    if 'Vlr. Nota' in df.columns:
        df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_moeda)

    # --- NOVO: LÓGICA TRIBUTÁRIA (COMPLIANCE) ---
    # Aqui simulamos uma conferência: se o frete ou imposto for maior que 15% da nota, avisamos.
    aliquota_limite = 0.15 
    df['Check_Compliance'] = df['Vlr. Nota'] * aliquota_limite

    # --- FILTROS DINÂMICOS ---
    st.sidebar.subheader("Filtros de Data")
    if not df['Faturamento'].dropna().empty:
        min_faturamento = df['Faturamento'].min().date()
        max_faturamento = df['Faturamento'].max().date()
        periodo = st.sidebar.date_input("Período", [min_faturamento, max_faturamento])
        
        # Aplicando filtro de data
        if len(periodo) == 2:
            df = df[(df['Faturamento'].dt.date >= periodo[0]) & (df['Faturamento'].dt.date <= periodo[1])]

    # --- DASHBOARD ---
    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Total de Notas", len(df))
    m2.metric("Valor Total (R$)", f"{df['Vlr. Nota'].sum():,.2f}")
    
    # Gráfico Plotly
    fig = px.bar(df, x='U.F', y='Vlr. Nota', color='Logística Ent.', title="Volume por Estado e Transportador")
    st.plotly_chart(fig, use_container_width=True)

    # Tabela de conferência
    st.subheader("🔍 Auditoria de Notas")
    st.dataframe(df)
else:
    st.info("Aguardando o upload do arquivo para processar...")
