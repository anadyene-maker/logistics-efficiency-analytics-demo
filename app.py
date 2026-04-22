import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página para ficar com cara de sistema
st.set_page_config(page_title="Torre de Controle Semalo", layout="wide")

st.title("📊 Dashboard de Eficiência Logística - Semalo")
st.markdown("---")

# Barra lateral para upload
st.sidebar.header("Configurações")
uploaded_file = st.sidebar.file_uploader("Suba o arquivo CSV da operação", type="csv")

if uploaded_file is not None:
    # Lendo o arquivo com o padrão que descobrimos no Colab
    df = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
    
    # Tratamento de Datas
    df['Faturamento'] = pd.to_datetime(df['Faturamento'], dayfirst=True, errors='coerce')
    df['Entrega'] = pd.to_datetime(df['Entrega'], dayfirst=True, errors='coerce')
    df['Data Agendamento'] = pd.to_datetime(df['Data Agendamento'], dayfirst=True, errors='coerce')
    
    # Cálculo do Lead Time e OTD
    df['Lead_Time'] = (df['Entrega'] - df['Faturamento']).dt.days
    df['OTD'] = (df['Entrega'] <= df['Data Agendamento']).astype(int)
    
    # Criar OPLs fictícios se a coluna não existir (para teste)
    if 'OPL' not in df.columns:
        import numpy as np
        df['OPL'] = np.random.choice(['Logística Ágil', 'TransRápido', 'Expresso Semalo'], size=len(df))

    # Criando o Ranking
    ranking = df.groupby('OPL').agg(
        Qtd_Entregas=('Vlr. Nota', 'count'),
        Lead_Time_Medio=('Lead_Time', 'mean'),
        Eficiencia_OTD=('OTD', 'mean')
    ).reset_index()
    
    ranking['Eficiencia_OTD'] = (ranking['Eficiencia_OTD'] * 100).round(1)
    ranking['Lead_Time_Medio'] = ranking['Lead_Time_Medio'].round(1)

    # Exibindo os Cards principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Entregas", int(ranking['Qtd_Entregas'].sum()))
    col2.metric("Lead Time Médio", f"{ranking['Lead_Time_Medio'].mean():.1f} dias")
    col3.metric("Eficiência Geral (OTD)", f"{ranking['Eficiencia_OTD'].mean():.1f}%")

    # Gráfico de Barras
    st.subheader("Performance por Operador")
    fig = px.bar(ranking, x='OPL', y='Eficiencia_OTD', text='Eficiencia_OTD',
                 color='Lead_Time_Medio', title="Eficiência OTD% vs Lead Time (Cor)",
                 color_continuous_scale='RdYlGn_r', labels={'Eficiencia_OTD':'Eficiência %'})
    st.plotly_chart(fig, use_container_width=True)

    # Tabela de dados detalhada
    st.write("### Detalhamento por Operador", ranking)
else:
    st.warning("⚠️ Por favor, suba o arquivo CSV na barra lateral para gerar o Dashboard.") 
