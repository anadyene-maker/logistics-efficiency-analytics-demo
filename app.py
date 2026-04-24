import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Semalo - Control Tower", layout="wide")

# --- FUNÇÕES DE SUPORTE (DIdática: Tratando a "sujeira" dos dados) ---
def tratar_moeda(valor):
    if isinstance(valor, str):
        # O Sankhya usa R$, pontos para milhar e vírgula para decimal.
        # Precisamos limpar tudo para virar um número (float).
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return pd.to_numeric(valor, errors='coerce')
    return valor

# --- SIDEBAR: O CÉREBRO DO DASHBOARD ---
st.sidebar.header("🕹️ Painel de Controle")

arquivo = st.sidebar.file_uploader("1. Importar Planilha Sankhya", type=['csv'])

if arquivo:
    # O segredo para não dar erro: sep=None faz o pandas detectar se é ; ou ,
    # encoding='latin1' evita erros de acentuação (comum no Windows/Sankhya)
    df = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin1')
    
    # Limpeza de nomes de colunas (tira espaços extras)
    df.columns = [c.strip() for c in df.columns]

    # --- PROCESSAMENTO ---
    # Convertendo Valores
    if 'Vlr. Nota' in df.columns:
        df['Vlr. Nota'] = df['Vlr. Nota'].apply(tratar_moeda)

    # Convertendo Datas
    for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
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

    # --- APLICANDO OS FILTROS ---
    mask = (df['U.F'].isin(ufs_selecionadas))
    if len(periodo) == 2:
        mask = mask & (df['Faturamento'].dt.date >= periodo[0]) & (df['Faturamento'].dt.date <= periodo[1])
    
    df_filtrado = df.loc[mask].copy()

    # --- CÁLCULOS DE EFICIÊNCIA ---
    # Lead Time (Logística)
    df_filtrado['Lead_Time'] = (df_filtrado['Entrega'] - df_filtrado['Faturamento']).dt.days
    
    # OTD (Eficiência)
    df_filtrado['OTD'] = np.where(df_filtrado['Entrega'] <= df_filtrado['Data Agendamento'], 1, 0)
    
    # Auditoria (Direito/Compliance)
    df_filtrado['Status_Auditoria'] = np.where(df_filtrado['Vlr. Nota'] > 10000, "🚨 Revisar", "✅ OK")

    # --- VISUALIZAÇÃO ---
    st.title("🚀 Torre de Controle & Compliance")
    
    # Métricas de Resumo
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pedidos", len(df_filtrado))
    c2.metric("OTD Médio", f"{(df_filtrado['OTD'].mean()*100):.1f}%")
    c3.metric("Lead Time Médio", f"{df_filtrado['Lead_Time'].mean():.1f} dias")
    c4.metric("Valor Total", f"R$ {df_filtrado['Vlr. Nota'].sum():,.2f}")

    # Gráfico de Eficiência Logística
    st.subheader("📊 Eficiência Logística por UF")
    fig_perf = px.bar(df_filtrado.groupby('U.F')['OTD'].mean().reset_index(), 
                      x='U.F', y='OTD', text_auto='.1%', color='OTD',
                      color_continuous_scale='RdYlGn')
    st.plotly_chart(fig_perf, use_container_width=True)

    # Tabela de Auditoria
    st.subheader("🔍 Auditoria de Notas e Prazos")
    st.dataframe(
        df_filtrado[['Ordem Carga', 'Logística Ent.', 'U.F', 'Vlr. Nota', 'Lead_Time', 'Status_Auditoria']],
        use_container_width=True
    )

else:
    st.warning("Aguardando upload do arquivo na barra lateral...")
