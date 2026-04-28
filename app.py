import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Semalo - Torre de Controle MT", layout="wide")

# --- 2. FUNÇÕES DE SUPORTE ---
def carregar_dados(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python', encoding='latin1')
        else:
            df = pd.read_excel(file)
        
        # Limpeza de nomes e conversão de datas
        df.columns = [c.strip() for c in df.columns]
        for col in ['Faturamento', 'Entrega', 'Data Agendamento']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None

def definir_regiao(cidade):
    cidade = str(cidade).upper()
    if cidade in ['CUIABA', 'VARZEA GRANDE']: return 'Baixada Cuiabana'
    elif cidade in ['SINOP', 'SORRISO', 'LUCAS DO RIO VERDE', 'NOVA MUTUM']: return 'Norte (Eixo 163)'
    elif cidade in ['RONDONOPOLIS', 'PRIMAVERA DO LESTE', 'JACIARA']: return 'Sul/Sudeste'
    elif cidade in ['TANGARA DA SERRA', 'CAMPO NOVO DO PARECIS']: return 'Médio-Norte'
    return 'Outras Regiões MT'

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("🕹️ Painel de Operações")
arquivo = st.sidebar.file_uploader("Suba o relatório do Sankhya", type=['csv', 'xlsx'])

if arquivo:
    df_raw = carregar_dados(arquivo)
    
    if df_raw is not None:
        # Filtro para Mato Grosso
        df_mt = df_raw[df_raw['U.F'] == 'MT'].copy()
        
        if not df_mt.empty:
            df_mt['Regiao'] = df_mt['Cidade.'].apply(definir_regiao)

            # Filtros de Seleção
            regioes_disponiveis = sorted(df_mt['Regiao'].unique())
            regioes_sel = st.sidebar.multiselect("Regiões", regioes_disponiveis, default=regioes_disponiveis)
            
            data_min = df_mt['Faturamento'].min().date()
            data_max = df_mt['Faturamento'].max().date()
            periodo = st.sidebar.date_input("Período de Faturamento", [data_min, data_max])

            # Aplicando filtros
            df_final = df_mt[df_mt['Regiao'].isin(regioes_sel)].copy()
            if len(periodo) == 2:
                df_final = df_final[(df_final['Faturamento'].dt.date >= periodo[0]) & (df_final['Faturamento'].dt.date <= periodo[1])]

            # --- 4. CÁLCULOS ---
            # OTD: 1 se entregou no prazo, 0 se atrasou
            df_final['OTD'] = np.where(df_final['Entrega'] <= df_final['Data Agendamento'], 1, 0)
            df_final['Lead_Time'] = (df_final['Entrega'] - df_final['Faturamento']).dt.days

            # --- 5. DASHBOARD VISUAL ---
            st.title("📈 Performance Logística - Mato Grosso")
            
            c1, c2, c3 = st.columns(3)
            otd_geral = df_final['OTD'].mean() * 100
            c1.metric("Total de Pedidos", len(df_final))
            c2.metric("OTD Médio (Eficiência)", f"{otd_geral:.1f}%")
            c3.metric("Lead Time Médio", f"{df_final['Lead_Time'].mean():.1f} dias")

            # Gráfico de Cores (Farol)
            st.subheader("📊 Eficiência por Região (OTD%)")
            df_grafico = df_final.groupby('Regiao')['OTD'].mean().reset_index()
            
            fig = px.bar(df_grafico, x='Regiao', y='OTD', text_auto='.1%',
                         color='OTD', color_continuous_scale='RdYlGn', range_color=[0, 1],
                         title="Percentual de Entregas no Prazo")
            st.plotly_chart(fig, use_container_width=True)

            # Tabela
            st.subheader("🔍 Detalhamento das Entregas")
            st.dataframe(df_final[['Ordem Carga', 'Cidade.', 'Regiao', 'Lead_Time', 'OTD']], use_container_width=True)

            # --- 6. RELATÓRIO ESCRITO AUTOMÁTICO ---
            st.markdown("---")
            st.subheader("📝 Parecer Técnico Operacional")
            
            pior_regiao = df_grafico.loc[df_grafico['OTD'].idxmin(), 'Regiao']
            pior_valor = df_grafico['OTD'].min() * 100

            status_operacao = "CRÍTICA" if otd_geral < 70 else "ESTÁVEL"

            relatorio = f"""
            **Data do Relatório:** {pd.Timestamp.now().strftime('%d/%m/%Y')}  
            **Status da Operação:** {status_operacao}

            1. **Análise de Eficiência:** O índice de OTD (On-Time Delivery) geral está em **{otd_geral:.1f}%**.
            2. **Gargalo Identificado:** A região **{pior_regiao}** apresenta o menor nível de serviço, com **{pior_valor:.1f}%** de sucesso nas entregas.
            3. **Recomendação:** Priorizar a revisão logística na região de {pior_regiao} e auditar as datas de agendamento do operador para reduzir o Lead Time médio.
            """
            st.info(relatorio)
            
            # --- 7. NOTA DE SEGURANÇA E PRIVACIDADE ---
            st.markdown("---")
            st.caption("🔒 **Nota de Segurança de Dados:**")
            st.warning("Este sistema processa dados em memória temporária. Nenhuma informação do Sankhya é armazenada no GitHub ou em servidores externos, garantindo o sigilo empresarial e o compliance com a LGPD.")

        else:
            st.warning("⚠️ Não foram encontrados dados para o estado de Mato Grosso (MT) neste arquivo.")
        else:
            st.warning("⚠️ Não foram encontrados dados para o estado de Mato Grosso (MT) neste arquivo.")
else:
    st.info("💡 Por favor, faça o upload do arquivo Excel ou CSV do Sankhya para iniciar a análise.")
