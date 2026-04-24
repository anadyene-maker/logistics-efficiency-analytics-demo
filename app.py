import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Torre de Controle Semalo", layout="wide")

# Função para limpar moeda (essencial para não dar erro em cálculos)
def limpar_valor(valor):
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', '').strip()
        try: return float(valor)
        except: return 0.0
    return float(valor) if pd.notna(valor) else 0.0

st.sidebar.header("🕹️ Painel de Controle")
arquivo = st.sidebar.file_uploader("Suba o arquivo (CSV ou XLSX)", type=['csv', 'xlsx'])

if arquivo:
    try:
        # --- LEITURA INTELIGENTE ---
        if arquivo.name.endswith('.csv'):
            # O segredo: sep=None + engine='python' detecta o separador automaticamente
            # encoding='latin1' trata os acentos do Sankhya sem dar erro
            df = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        else:
            # Para Excel (xlsx), não precisa de sep ou encoding
            df = pd.read_excel(arquivo)

        # Limpeza de nomes de colunas (remove espaços que o Sankhya gera)
        df.columns = [c.strip() for c in df.columns]

        # --- PROCESSAMENTO ---
        # Conversão de Valores
        if 'Vlr. Nota' in df.columns:
            df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_valor)

        # Conversão de Datas
        for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        # --- FILTROS NA SIDEBAR ---
        st.sidebar.markdown("---")
        
        # Filtro de UF
        ufs = sorted([str(x) for x in df['U.F'].unique() if pd.notna(x)])
        ufs_sel = st.sidebar.multiselect("Filtrar Estados", ufs, default=ufs)

        # Filtro de Data
        data_min = df['Faturamento'].min().date() if not df['Faturamento'].dropna().empty else None
        data_max = df['Faturamento'].max().date() if not df['Faturamento'].dropna().empty else None
        
        if data_min and data_max:
            periodo = st.sidebar.date_input("Período de Faturamento", [data_min, data_max])
        
        # Parâmetro Auditoria
        aliquota = st.sidebar.number_input("Alíquota ICMS (%)", value=12.0) / 100

        # --- APLICAÇÃO DOS FILTROS ---
        df_filtrado = df[df['U.F'].isin(ufs_sel)].copy()
        if 'periodo' in locals() and len(periodo) == 2:
            df_filtrado = df_filtrado[(df_filtrado['Faturamento'].dt.date >= periodo[0]) & 
                                      (df_filtrado['Faturamento'].dt.date <= periodo[1])]

        # --- CÁLCULOS LOGÍSTICOS (O que você pediu!) ---
        df_filtrado['Lead_Time'] = (df_filtrado['Entrega'] - df_filtrado['Faturamento']).dt.days
        df_filtrado['OTD'] = np.where(df_filtrado['Entrega'] <= df_filtrado['Data Agendamento'], 1, 0)
        df_filtrado['Status_Auditoria'] = np.where(df_filtrado['Vlr. Nota'] > 10000, "🚨 Revisar", "✅ OK")

        # --- EXIBIÇÃO ---
        st.title("🚀 Torre de Controle Semalo")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pedidos", len(df_filtrado))
        col2.metric("Eficiência OTD", f"{(df_filtrado['OTD'].mean()*100):.1f}%")
        col3.metric("Lead Time Médio", f"{df_filtrado['Lead_Time'].mean():.1f} dias")

        st.dataframe(df_filtrado[['Ordem Carga', 'Logística Ent.', 'U.F', 'Vlr. Nota', 'Lead_Time', 'Status_Auditoria']], use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
else:
    st.info("Aguardando upload...")
