import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página - Deve ser a primeira linha de comando Streamlit
st.set_page_config(page_title="Control Tower - Logística & Direito", layout="wide")

st.title("🚀 Torre de Controle Logística 4.0")
st.markdown("---")

# --- 1. UPLOAD DE ARQUIVOS (MÉTODO MANUAL) ---
# O file_uploader retorna um objeto de arquivo que o Pandas consegue ler diretamente.
arquivo_postado = st.sidebar.file_uploader("Arraste sua planilha (CSV ou Excel) aqui", type=['csv', 'xlsx'])

if arquivo_postado is not None:
    # Lógica para identificar se é CSV ou Excel (comum em processos jurídicos e fretes)
    try:
        if arquivo_postado.name.endswith('.csv'):
            df = pd.read_csv(arquivo_postado, sep=';', encoding='latin1')
        else:
            df = pd.read_excel(arquivo_postado)
        st.sidebar.success("Arquivo carregado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    # --- 2. LIMPEZA E TRATAMENTO (A MÁGICA DO PANDAS) ---
    # Convertemos colunas para datetime. O 'errors=coerce' transforma datas inválidas em NaT (Not a Time)
    df['Faturamento'] = pd.to_datetime(df['Faturamento'], dayfirst=True, errors='coerce')
    df['Entrega'] = pd.to_datetime(df['Entrega'], dayfirst=True, errors='coerce')
    df['Data Agendamento'] = pd.to_datetime(df['Data Agendamento'], dayfirst=True, errors='coerce')

    # Dropamos linhas onde o Faturamento é nulo para não quebrar os cálculos de tempo
    df = df.dropna(subset=['Faturamento'])

    # Cálculo do Lead Time e OTD (On-Time Delivery)
    df['Lead_Time'] = (df['Entrega'] - df['Faturamento']).dt.days
    df['OTD'] = (df['Entrega'] <= df['Data Agendamento']).astype(int)

    # --- 3. FILTROS NA SIDEBAR ---
    st.sidebar.header("Filtros de Análise")
    
    # Filtro de Datas: Pegamos a menor e maior data do faturamento
    min_date = df['Faturamento'].min().date()
    max_date = df['Faturamento'].max().date()
    
    periodo = st.sidebar.date_input("Selecione o Período", [min_date, max_date])

    # Filtro de UF
    ufs = sorted(df['U.F'].unique().astype(str))
    uf_selecionada = st.sidebar.multiselect("Filtrar por Estado", ufs, default=ufs)

    # Aplicando os filtros no DataFrame original
    # Checamos se o usuário selecionou o range de datas completo (início e fim)
    if len(periodo) == 2:
        mask = (df['Faturamento'].dt.date >= periodo[0]) & (df['Faturamento'].dt.date <= periodo[1]) & (df['U.F'].isin(uf_selecionada))
        df_filtrado = df.loc[mask]
    else:
        df_filtrado = df[df['U.F'].isin(uf_selecionada)]

    # --- 4. DASHBOARD E VISUALIZAÇÕES ---
    if not df_filtrado.empty:
        # Métricas Principais
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Pedidos", len(df_filtrado))
        m2.metric("Lead Time Médio", f"{df_filtrado['Lead_Time'].mean():.1f} dias")
        m3.metric("Eficiência OTD", f"{(df_filtrado['OTD'].mean()*100):.1f}%")

        # Gráfico Minucioso: OTD por Cidade (Análise de Gargalos Regionais)
        st.subheader("📍 Performance por Cidade")
        otd_cidade = df_filtrado.groupby('Cidade.').agg({'OTD': 'mean', 'Ordem Carga': 'count'}).reset_index()
        otd_cidade.columns = ['Cidade', 'Eficiencia_OTD', 'Volume']
        otd_cidade = otd_cidade.sort_values(by='Volume', ascending=False).head(15)

        fig_city = px.bar(otd_cidade, x='Cidade', y='Volume', color='Eficiencia_OTD',
                          title="Top 15 Cidades por Volume e Eficiência (Cores)",
                          color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_city, use_container_width=True)
        
        st.write("Dica: Cidades em **vermelho** têm alto volume mas baixa eficiência de entrega.")

    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

else:
    st.info("Aguardando upload da planilha para iniciar a análise... 📁")
