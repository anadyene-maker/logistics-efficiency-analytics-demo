import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Torre de Controle - Eficiência Logística", layout="wide")

# --- 2. FUNÇÕES DE SUPORTE ---
def carregar_dados(file_or_path):
    try:
        if isinstance(file_or_path, str):
            df = pd.read_csv(file_or_path, sep=';', encoding='utf-8')
        else:
            if file_or_path.name.endswith('.csv'):
                df = pd.read_csv(file_or_path, sep=None, engine='python', encoding='latin1')
            else:
                df = pd.read_excel(file_or_path)
                
        df.columns = [c.strip() for c in df.columns]
        
        # Converte colunas de data
        for col in ['Faturamento', 'Entrega', 'Data Agendamento', 'Data Agendamento;Obs. Logística;Entrega']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao ler os dados: {e}")
        return None

def definir_regiao(cidade):
    cidade = str(cidade).upper().strip()
    if cidade in ['CUIABA', 'VARZEA GRANDE']: return 'Baixada Cuiabana'
    elif cidade in ['SINOP', 'SORRISO', 'LUCAS DO RIO VERDE', 'NOVA MUTUM']: return 'Norte (Eixo 163)'
    elif cidade in ['RONDONOPOLIS', 'PRIMAVERA DO LESTE', 'JACIARA']: return 'Sul/Sudeste'
    elif cidade in ['TANGARA DA SERRA', 'CAMPO NOVO DO PARECIS']: return 'Médio-Norte'
    elif cidade in ['GUARAPUAVA', 'MARINGA', 'LONDRINA', 'CURITIBA', 'PONTA GROSSA', 'FOZ DO IGUACU', 'COLOMBO', 'APUCARANA', 'ARAPONGAS', 'RONDON']: return 'Operação Sul / PR'
    return 'Demais Regiões'

# --- 3. BARRA LATERAL (CARREGAMENTO AUTOMÁTICO + FILTROS) ---
st.sidebar.header("🕹️ Painel de Operações")
st.sidebar.info("💡 **Portfólio:** Base de dados sintética/fictícia carregada automaticamente em conformidade com a LGPD.")

arquivo = st.sidebar.file_uploader("Suba outro relatório (Opcional)", type=['csv', 'xlsx'])

if arquivo:
    df_raw = carregar_dados(arquivo)
else:
    df_raw = carregar_dados('dados_eficiencia.csv')

if df_raw is not None and not df_raw.empty:
    df_final = df_raw.copy()

    # Identificação da coluna de cidade
    col_cidade = 'Cidade.' if 'Cidade.' in df_final.columns else ('Cidade' if 'Cidade' in df_final.columns else None)
    
    if col_cidade:
        df_final['Regiao'] = df_final[col_cidade].apply(definir_regiao)
        regioes_disponiveis = sorted(df_final['Regiao'].unique())
        regioes_sel = st.sidebar.multiselect("Regiões", regioes_disponiveis, default=regioes_disponiveis)
        df_final = df_final[df_final['Regiao'].isin(regioes_sel)].copy()
    else:
        df_final['Regiao'] = 'Geral'

    # Ajuste de Datas e Período
    if 'Faturamento' in df_final.columns:
        faturamento_valido = df_final['Faturamento'].dropna()
        if not faturamento_valido.empty:
            data_min, data_max = faturamento_valido.min().date(), faturamento_valido.max().date()
            periodo = st.sidebar.date_input("Período", [data_min, data_max])
            if len(periodo) == 2:
                df_final = df_final[(df_final['Faturamento'].dt.date >= periodo[0]) & (df_final['Faturamento'].dt.date <= periodo[1])]

    # --- 4. CÁLCULOS ---
    if 'Entrega' in df_final.columns and 'Data Agendamento' in df_final.columns:
        df_final['OTD'] = np.where(df_final['Entrega'] <= df_final['Data Agendamento'], 1, 0)
    else:
        df_final['OTD'] = 1  # Valor padrão caso não haja datas de agendamento no upload

    if 'Entrega' in df_final.columns and 'Faturamento' in df_final.columns:
        df_final['Lead_Time'] = (df_final['Entrega'] - df_final['Faturamento']).dt.days
    else:
        df_final['Lead_Time'] = 0

    otd_geral = df_final['OTD'].mean() * 100 if len(df_final) > 0 else 0

    # --- 5. DASHBOARD VISUAL ---
    st.title("📈 Performance Logística - Analytics Demo")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Pedidos", len(df_final))
    c2.metric("OTD Médio (Eficiência)", f"{otd_geral:.1f}%")
    c3.metric("Lead Time Médio", f"{df_final['Lead_Time'].mean():.1f} dias")

    st.subheader("📊 Eficiência por Região (OTD%)")
    df_grafico = df_final.groupby('Regiao')['OTD'].mean().reset_index()
    fig = px.bar(df_grafico, x='Regiao', y='OTD', text_auto='.1%',
                 color='OTD', color_continuous_scale='RdYlGn', range_color=[0, 1])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔍 Detalhamento das Entregas")
    cols_possiveis = ['Ordem Carga', col_cidade, 'Regiao', 'Lead_Time', 'OTD']
    cols_exibicao = [c for c in cols_possiveis if c in df_final.columns]
    st.dataframe(df_final[cols_exibicao], use_container_width=True)

    # --- 6. RELATÓRIO COM RÉGUA DE PERFORMANCE ---
    st.markdown("---")
    st.subheader("📝 Parecer Técnico e Régua de Performance")
    
    if otd_geral >= 95: status_texto, cor_alerta = "💎 EXCELÊNCIA", "success"
    elif otd_geral >= 90: status_texto, cor_alerta = "✅ BOM / ACEITÁVEL", "success"
    elif otd_geral >= 80: status_texto, cor_alerta = "⚠️ REGULAR (ALERTA)", "warning"
    else: status_texto, cor_alerta = "🚨 CRÍTICO / DEFICIENTE", "error"

    with st.expander("📊 Veja a Régua de Referência de Mercado (Benchmark)"):
        st.write("""
        | Taxa de OTD | Classificação | Ação Recomendada |
        | :--- | :--- | :--- |
        | **95% a 100%** | **Excelência** | Manter processos e bonificar. |
        | **90% a 94%** | **Bom** | Ajustes finos em rotas específicas. |
        | **80% a 89%** | **Regular** | Notificar operador / Plano de ação. |
        | **Abaixo de 80%** | **Crítico** | Revisão Contratual / Aplicação de Multas. |
        """)

    if not df_grafico.empty:
        pior_regiao = df_grafico.loc[df_grafico['OTD'].idxmin(), 'Regiao']
        pior_valor = df_grafico['OTD'].min() * 100
    else:
        pior_regiao, pior_valor = "N/A", 0

    relatorio = f"""
    **Data do Relatório:** {pd.Timestamp.now().strftime('%d/%m/%Y')}  
    **Classificação da Operação:** {status_texto}

    1. **Análise de Eficiência:** O índice de OTD geral está em **{otd_geral:.1f}%**.
    2. **Gargalo Regional:** A região **{pior_regiao}** apresenta o menor nível (**{pior_valor:.1f}%**).
    3. **Parecer:** Operação classificada como **{status_texto}**. Recomenda-se acompanhamento e alinhamento de SLA.
    """
    if cor_alerta == "success": st.success(relatorio)
    elif cor_alerta == "warning": st.warning(relatorio)
    else: st.error(relatorio)

    # --- 7. NOTA DE SEGURANÇA ---
    st.markdown("---")
    st.caption("🔒 **Nota de Segurança de Dados & LGPD:**")
    st.info("Este dashboard foi desenvolvido para demonstração técnica de Legal Ops & Process Analytics. A base principal utiliza registros anonimizados/sintéticos.")
else:
    st.warning("⚠️ Nenhum dado encontrado. Certifique-se de que o arquivo no repositório ou o upload contenha registros válidos.")
