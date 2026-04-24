import streamlit as st
import pandas as pd

# --- FUNÇÃO DE LIMPEZA (Reutilizando sua base) ---
def limpar_moeda(valor):
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return pd.to_numeric(valor, errors='coerce')
    return valor

st.title("⚖️ Auditoria de Compliance Logístico")

arquivo = st.sidebar.file_uploader("Suba o arquivo Sankhya", type=['csv'])

if arquivo:
    # 1. Leitura e Limpeza Inicial
    df = pd.read_csv(arquivo, sep=';', encoding='latin1')
    df.columns = [c.strip() for c in df.columns]
    df['Vlr. Nota'] = df['Vlr. Nota'].apply(limpar_moeda)

    # --- 2. LOGÍCA DE AUDITORIA TRIBUTÁRIA ---
    st.sidebar.subheader("Parâmetros de Auditoria")
    # O usuário escolhe a alíquota de acordo com o estado ou operação
    aliquota = st.sidebar.number_input("Alíquota Fixa de ICMS (%)", min_value=0.0, max_value=30.0, value=12.0) / 100

    # Simulando o cálculo do ICMS que deveria estar na nota
    df['ICMS_Calculado'] = df['Vlr. Nota'] * aliquota

    # Aqui criamos a coluna de STATUS
    # Se você tiver a coluna 'Vlr. ICMS' no arquivo, a comparação seria:
    # df['Status_Auditoria'] = np.where(df['Vlr. ICMS'] == df['ICMS_Calculado'], "✅ OK", "🚨 DIVERGENTE")
    
    # Como vamos criar para análise de processo jurídico/tributário:
    # Vamos marcar como '⚠️ REVISAR' notas com valores muito altos que precisam de atenção jurídica
    limite_alerta = st.sidebar.number_input("Limite para Alerta Jurídico (R$)", value=5000.0)
    
    def avaliar_status(row):
        if row['Vlr. Nota'] > limite_alerta:
            return "🔴 Alto Risco (Revisar)"
        return "🟢 Conformidade"

    df['Status_Auditoria'] = df.apply(avaliar_status, axis=1)

    # --- 3. EXIBIÇÃO DOS RESULTADOS ---
    st.subheader("📋 Painel de Conferência")
    
    # Colorindo a tabela no Streamlit para facilitar a visão da Torre de Controle
    def highlight_status(val):
        color = 'red' if '🔴' in val else 'green'
        return f'color: {color}'

    # Exibindo apenas colunas relevantes para a auditoria
    colunas_foco = ['Ordem Carga', 'Cliente', 'U.F', 'Vlr. Nota', 'ICMS_Calculado', 'Status_Auditoria']
    st.dataframe(df[colunas_foco].style.applymap(highlight_status, subset=['Status_Auditoria']), use_container_width=True)

    # Métrica de Compliance
    qtd_alerta = len(df[df['Status_Auditoria'] == "🔴 Alto Risco (Revisar)"])
    st.metric("Notas em Alerta Jurídico", qtd_alerta, delta="Atenção necessária", delta_color="inverse")
