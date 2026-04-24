import streamlit as st
import pandas as pd
import numpy as np

# --- 1. FUNÇÃO DE CONVERSÃO ROBUSTA ---
def converter_para_numero(valor):
    """
    Transforma 'R$ 1.234,50' em 1234.50.
    Trata também se o valor já for número ou estiver vazio.
    """
    if isinstance(valor, str):
        # Remove R$, espaços e o ponto do milhar
        valor = valor.replace('R$', '').replace('.', '').replace(' ', '').replace('\xa0', '')
        # Troca a vírgula decimal por ponto
        valor = valor.replace(',', '.')
        try:
            return float(valor)
        except:
            return 0.0
    return float(valor) if pd.notna(valor) else 0.0

# --- 2. LÓGICA DE AUDITORIA ---
st.title("⚖️ Auditoria de ICMS - Torre de Controle")

arquivo = st.sidebar.file_uploader("Upload do CSV", type=['csv'])

if arquivo:
    # Lendo o arquivo (ajustado para o padrão do print: sep=';' e latin1)
    df = pd.read_csv(arquivo, sep=';', encoding='latin1')
    
    # Limpando nomes das colunas (Sankhya costuma colocar espaços)
    df.columns = [c.strip() for c in df.columns]

    # CONVERSÃO CRUCIAL: Transformando a coluna Vlr. Nota em número real
    if 'Vlr. Nota' in df.columns:
        df['Vlr. Nota'] = df['Vlr. Nota'].apply(converter_para_numero)
    
    # Parâmetros na Sidebar
    aliquota = st.sidebar.slider("Alíquota ICMS (%)", 0.0, 25.0, 12.0) / 100
    margem_erro = 0.05 # Tolerância de 5 centavos

    # --- CÁLCULO DA AUDITORIA ---
    # 1. Calculamos o que deveria ser o ICMS
    df['ICMS_Calculado'] = df['Vlr. Nota'] * aliquota
    
    # NOTA: Se o seu CSV tiver a coluna real do ICMS do Sankhya, 
    # use o converter_para_numero nela também e compare as duas!
    
    # 2. Criando o Status de Conformidade
    # Regra: Se o valor da nota for maior que 0, aplicamos a lógica
    df['Status_Auditoria'] = np.where(
        df['Vlr. Nota'] > 0, 
        "✅ CONFORME", 
        "⚪ SEM VALOR"
    )

    # Exemplo de verificação de divergência (Simulando que notas acima de R$ 10k precisam de revisão jurídica)
    df['Status_Auditoria'] = np.where(
        df['Vlr. Nota'] > 10000, 
        "🚨 REVISÃO JURÍDICA", 
        df['Status_Auditoria']
    )

    # --- EXIBIÇÃO ---
    st.subheader("📋 Painel de Auditoria")
    
    # Formatando para exibição (colocando a vírgula de volta apenas na visualização)
    df_visualizacao = df.copy()
    df_visualizacao['Vlr. Nota'] = df_visualizacao['Vlr. Nota'].map('R$ {:,.2f}'.format)
    df_visualizacao['ICMS_Calculado'] = df_visualizacao['ICMS_Calculado'].map('R$ {:,.2f}'.format)

    st.dataframe(
        df_visualizacao[['Ordem Carga', 'U.F', 'Vlr. Nota', 'ICMS_Calculado', 'Status_Auditoria']],
        use_container_width=True
    )

    # Métricas de Resumo
    col1, col2 = st.columns(2)
    col1.metric("Total de Notas", len(df))
    col2.metric("Notas para Revisão", len(df[df['Status_Auditoria'] == "🚨 REVISÃO JURÍDICA"]))
