import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Torre de Controle Semalo", layout="wide")

def limpar_valor(valor):
    """Limpa 'R$ 1.234,50' para 1234.50"""
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return pd.to_numeric(valor, errors='coerce')
    return valor

# --- INTERFACE ---
st.title("🚀 Torre de Controle & Compliance Semalo")
st.markdown("---")

arquivo = st.sidebar.file_uploader("📂 Arraste seu relatório do Sankhya aqui", type=['csv'])

if arquivo:
    # 1. LEITURA E TRATAMENTO (Padrão Sankhya)
    df = pd.read_csv(arquivo, sep=';', encoding='latin1')
    df.columns = [c.strip() for c in df.columns] # Remove espaços invisíveis

    # Tratamento de Moeda
    if 'Vlr. Nota' in df.columns:
        df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_valor)

    # Tratamento de Datas (Crucial para o Lead Time)
    for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    # --- 2. CÁLCULOS DE EFICIÊNCIA LOGÍSTICA ---
    # Lead Time: Dias entre faturamento e entrega real
    df['Lead_Time'] = (df['Entrega'] - df['Faturamento']).dt.days
    
    # OTD (On-Time Delivery): 1 se entregue até a data agendada, senão 0
    df['OTD'] = np.where(df['Entrega'] <= df['Data Agendamento'], 1, 0)

    # --- 3. CÁLCULOS DE AUDITORIA (COMPLIANCE) ---
    aliquota = st.sidebar.number_input("Alíquota ICMS (%)", value=12.0) / 100
    df['ICMS_Calc'] = df['Vlr. Nota'] * aliquota
    
    # Status de Auditoria (Regra de Negócio)
    df['Status_Auditoria'] = np.where(df['Vlr. Nota'] > 10000, "🚨 Revisar Jurídico", "✅ Ok")

    # --- 4. DASHBOARD (VISUALIZAÇÃO) ---
    
    # Linha 1: Métricas Principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total Pedidos", len(df))
    c2.metric("⏱️ Lead Time Médio", f"{df['Lead_Time'].mean():.1f} dias")
    c3.metric("✅ Eficiência OTD", f"{(df['OTD'].mean()*100):.1f}%")
    c4.metric("⚖️ Notas p/ Auditoria", len(df[df['Status_Auditoria'] != "✅ Ok"]))

    # Linha 2: Gráficos
    col_esq, col_dir = st.columns(2)
    
    with col_esq:
        st.subheader("Performance por Transportadora (OPL)")
        # Gráfico que você gosta: OPL vs Eficiência
        perf_opl = df.groupby('Logística Ent.').agg({'OTD': 'mean', 'Lead_Time': 'mean'}).reset_index()
        perf_opl['OTD'] *= 100
        fig_opl = px.bar(perf_opl, x='Logística Ent.', y='OTD', color='Lead_Time',
                         title="Eficiência OTD % (Cores = Lead Time Médio)",
                         color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig_opl, use_container_width=True)

    with col_dir:
        st.subheader("Distribuição Geográfica (Volume)")
        fig_uf = px.pie(df, values='Vlr. Nota', names='U.F', hole=0.4, title="Faturamento por Estado")
        st.plotly_chart(fig_uf, use_container_width=True)

    # Linha 3: Tabela Detalhada com Status
    st.markdown("---")
    st.subheader("🔍 Auditoria Detalhada de Cargas")
    
    # Estilizando a tabela
    def style_rows(row):
        return ['background-color: #ffcccc' if row.Status_Auditoria != '✅ Ok' else '' for _ in row]

    st.dataframe(
        df[['Ordem Carga', 'Logística Ent.', 'U.F', 'Vlr. Nota', 'Lead_Time', 'OTD', 'Status_Auditoria']]
        .style.apply(style_rows, axis=1), 
        use_container_width=True
    )

else:
    st.info("Aguardando upload da planilha Sankhya...")
