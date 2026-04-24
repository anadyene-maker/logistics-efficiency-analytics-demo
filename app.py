import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Semalo - Control Tower PRO", layout="wide")

# --- FUNÇÕES DE TRATAMENTO ---
def limpar_valor(valor):
    """Converte 'R$ 1.234,50' ou formatos mistos para número decimal."""
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', '').strip()
        return pd.to_numeric(valor, errors='coerce')
    return valor

# --- SIDEBAR (CONTROLES) ---
st.sidebar.header("🕹️ Painel de Controle")

# Agora aceitamos os dois formatos novamente
arquivo = st.sidebar.file_uploader("1. Importar Relatório (Sankhya)", type=['csv', 'xlsx'])

if arquivo:
    try:
        # LÓGICA DE LEITURA HÍBRIDA
        if arquivo.name.endswith('.csv'):
            # sep=None com engine='python' detecta se é ; ou , automaticamente
            df = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin1')
        else:
            df = pd.read_excel(arquivo)
        
        # Limpeza de nomes de colunas
        df.columns = [c.strip() for c in df.columns]

        # --- PROCESSAMENTO DE DADOS ---
        # 1. Valores Monetários
        if 'Vlr. Nota' in df.columns:
            df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_valor)

        # 2. Datas (Crucial para Eficiência)
        colunas_data = ['Faturamento', 'Entrega', 'Data Agendamento']
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        # --- FILTROS DINÂMICOS ---
        st.sidebar.markdown("---")
        
        # Filtro de UF
        lista_ufs = sorted(df['U.F'].unique().astype(str))
        ufs_selecionadas = st.sidebar.multiselect("2. Filtrar por Estado (UF)", lista_ufs, default=lista_ufs)

        # Filtro de Datas
        data_min = df['Faturamento'].min().date()
        data_max = df['Faturamento'].max().date()
        periodo = st.sidebar.date_input("3. Período de Faturamento", [data_min, data_max])

        # Parâmetro de Auditoria
        aliquota = st.sidebar.number_input("4. Alíquota ICMS (%)", value=12.0) / 100

        # --- APLICAÇÃO DOS FILTROS ---
        mask = (df['U.F'].isin(ufs_selecionadas))
        if len(periodo) == 2:
            mask = mask & (df['Faturamento'].dt.date >= periodo[0]) & (df['Faturamento'].dt.date <= periodo[1])
        
        df_filtrado = df.loc[mask].copy()

        # --- CÁLCULOS DE EFICIÊNCIA E AUDITORIA ---
        # Eficiência Logística
        df_filtrado['Lead_Time'] = (df_filtrado['Entrega'] - df_filtrado['Faturamento']).dt.days
        df_filtrado['OTD'] = np.where(df_filtrado['Entrega'] <= df_filtrado['Data Agendamento'], 1, 0)
        
        # Auditoria Tributária
        df_filtrado['Status_Auditoria'] = np.where(df_filtrado['Vlr. Nota'] > 10000, "🚨 Revisar", "✅ OK")

        # --- DASHBOARD VISUAL ---
        st.title("🚀 Torre de Controle Semalo")
        
        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Pedidos", len(df_filtrado))
        m2.metric("OTD Médio", f"{(df_filtrado['OTD'].mean()*100):.1f}%")
        m3.metric("Lead Time Médio", f"{df_filtrado['Lead_Time'].mean():.1f} dias")
        m4.metric("Faturamento Filtrado", f"R$ {df_filtrado['Vlr. Nota'].sum():,.2f}")

        # Gráfico de Performance por OPL
        st.subheader("📊 Eficiência por Transportadora (OTD)")
        fig_opl = px.bar(df_filtrado.groupby('Logística Ent.')['OTD'].mean().reset_index(), 
                         x='Logística Ent.', y='OTD', text_auto='.1%', 
                         color='OTD', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_opl, use_container_width=True)

        # Tabela Detalhada
        st.subheader("🔍 Auditoria de Operações")
        st.dataframe(df_filtrado[['Ordem Carga', 'Logística Ent.', 'U.F', 'Vlr. Nota', 'Lead_Time', 'Status_Auditoria']], use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

else:
    st.info("💡 Por favor, faça o upload de um arquivo CSV ou XLSX exportado do Sankhya.")
