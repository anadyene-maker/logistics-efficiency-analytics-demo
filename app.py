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
            # Carregamento automático do CSV local do repositório
            df = pd.read_csv(file_or_path, sep=';', encoding='utf-8')
        else:
            # Carregamento via Upload pelo usuário
            if file_or_path.name.endswith('.csv'):
                df = pd.read_csv(file_or_path, sep=None, engine='python', encoding='latin1')
            else:
                df = pd.read_excel(file_or_path)
                
        df.columns = [c.strip() for c in df.columns]
        for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao ler os dados: {e}")
        return None

def definir_regiao(cidade):
    cidade = str(cidade).upper()
    if cidade in ['CUIABA', 'VARZEA GRANDE']: return 'Baixada Cuiabana'
    elif cidade in ['SINOP', 'SORRISO', 'LUCAS DO RIO VERDE', 'NOVA MUTUM']: return 'Norte (Eixo 163)'
    elif cidade in ['RONDONOPOLIS', 'PRIMAVERA DO LESTE', 'JACIARA']: return 'Sul/Sudeste'
    elif cidade in ['TANGARA DA SERRA', 'CAMPO NOVO DO PARECIS']: return 'Médio-Norte'
    return 'Outras Regiões MT'

# --- 3. BARRA LATERAL (CARREGAMENTO AUTOMÁTICO + FILTROS) ---
st.sidebar.header("🕹️ Painel de Operações")
st.sidebar.info("💡 **Portfólio:** Base de dados sintética/fictícia carregada automaticamente em conformidade com a LGPD.")

arquivo = st.sidebar.file_uploader("Suba outro relatório (Opcional)", type=['csv', 'xlsx'])

# Lógica inteligente: se a pessoa subir um arquivo novo, usa o novo. Caso contrário, usa o 'dados_eficiencia.csv'
if arquivo:
    df_raw = carregar_dados(arquivo)
else:
    df_raw = carregar_dados('dados_eficiencia.csv')

if df_raw is not None:
    # Caso a coluna de UF exista ou não no CSV sintético
    if 'U.F' in df_raw.columns:
        df_mt = df_raw[df_raw['U.F'] == 'MT'].copy()
    else:
        df_mt = df_raw.copy()

    if not df_mt.empty:
        df_mt['Regiao'] = df_mt['Cidade.'].apply(definir_regiao)
        regioes_disponiveis = sorted(df_mt['Regiao'].unique())
        regioes_sel = st.sidebar.multiselect("Regiões", regioes_disponiveis, default=regioes_disponiveis)
        
        # Ajuste de Datas
        faturamento_valido = df_mt['Faturamento'].dropna()
        if not faturamento_valido.empty:
            data_min, data_max = faturamento_valido.min().date(), faturamento_valido.max().date()
            periodo = st.sidebar.date_input("Período", [data_min, data_max])
        else:
            periodo = []

        df_final = df_mt[df_mt['Regiao'].isin(regioes_sel)].copy()
        if len(periodo) == 2:
            df_final = df_final[(df_final['Faturamento'].dt.date >= periodo[0]) & (df_final['Faturamento'].dt.date <= periodo[1])]

        # --- 4. CÁLCULOS ---
        df_final['OTD'] = np.where(df_final['Entrega'] <= df_final['Data Agendamento'], 1, 0)
        df_final['Lead_Time'] = (df_final['Entrega'] - df_final['Faturamento']).dt.days
        otd_geral = df_final['OTD'].mean() * 100

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
        cols_exibicao = [c for c in ['Ordem Carga', 'Cidade.', 'Regiao', 'Lead_Time', 'OTD'] if c in df_final.columns]
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

        pior_regiao = df_grafico.loc[df_grafico['OTD'].idxmin(), 'Regiao']
        pior_valor = df_grafico['OTD'].min() * 100

        relatorio = f"""
        **Data do Relatório:** {pd.Timestamp.now().strftime('%d/%m/%Y')}  
        **Classificação da Operação:** {status_texto}

        1. **Análise de Eficiência:** O índice de OTD geral está em **{otd_geral:.1f}%**.
        2. **Gargalo Regional:** A região **{pior_regiao}** tem o menor nível (**{pior_valor:.1f}%**).
        3. **Parecer:** Operação classificada como **{status_texto}**. Recomenda-se auditoria/ação de acompanhamento.
        """
        if cor_alerta == "success": st.success(relatorio)
        elif cor_alerta == "warning": st.warning(relatorio)
        else: st.error(relatorio)

        # --- 7. NOTA DE SEGURANÇA ---
        st.markdown("---")
        st.caption("🔒 **Nota de Segurança de Dados & LGPD:**")
        st.info("Este dashboard foi desenvolvido para demonstração técnica de Legal Ops & Process Analytics. A base de dados principal utiliza registros anonimizados/sintéticos.")
    else:
        st.warning("⚠️ Não foram encontrados dados para exibir.")
