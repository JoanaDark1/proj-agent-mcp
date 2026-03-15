import asyncio
import json
import streamlit as st
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from utils.database import get_categorias, load_full_data
from utils.gemini import run_agent

load_dotenv()

st.set_page_config(page_title="Base de Dados Olist", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title(":material/dashboard: Dashboard Olist: Vendas & Satisfação")


with st.sidebar:
    st.header("Filtros")
    anos_sel = st.pills("Anos", options=[2016, 2017, 2018],
                        default=[2016, 2017, 2018], selection_mode="multi")
    todas_categorias = get_categorias()
    categorias_sel = st.multiselect("Categorias", options=todas_categorias,
                                    default=todas_categorias[:5])

if not anos_sel or not categorias_sel:
    st.warning("Selecione pelo menos um ano e uma categoria.")
    st.stop()


st.subheader(":material/smart_toy: Assistente de Dados Olist")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg.get("text"):
            st.write(msg["text"])
        if msg.get("chart"):
            st.vega_lite_chart(msg["chart"], use_container_width=True)

if prompt := st.chat_input("Pergunte algo (ex: gráfico de pizza das categorias)"):
    st.session_state.chat_history.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            result = asyncio.run(run_agent(prompt))

        msg_data = {"role": "assistant"}

        if result["type"] == "chart":
            st.vega_lite_chart(result["content"], use_container_width=True)
            msg_data["chart"] = result["content"]
            msg_data["text"] = "Aqui está o gráfico:"
            st.write("Aqui está o gráfico:")
        else:
            st.write(result["content"])
            msg_data["text"] = result["content"]

        st.session_state.chat_history.append(msg_data)

st.divider()


df = load_full_data(tuple(anos_sel), tuple(categorias_sel))


if df.empty:
    st.info("Nenhum dado encontrado.")
    st.stop()


faturamento_grupo = df["payment_value"].sum()
pedidos = df["order_id"].nunique()
review_medio = df["review_score"].mean()

m1, m2, m3 = st.columns(3)
with m1.container(border=True):
    st.metric("Faturamento Somado das categorias selecionadas", f"R$ {faturamento_grupo:,.2f}")
with m2.container(border=True):
    st.metric("Total Pedidos", f"{pedidos:,}")
with m3.container(border=True):
    st.metric("Satisfação Média", f"{review_medio:.2f} / 5")

st.divider()

col1, col2 = st.columns(2)

with col1.container(border=True):
    st.subheader("Faturamento por Estado")
    vendas_estado = df.groupby("customer_state")["payment_value"].sum().reset_index()
    st.altair_chart(
        alt.Chart(vendas_estado).mark_bar().encode(
            x=alt.X("payment_value:Q", title="Faturamento (R$)"),
            y=alt.Y("customer_state:N", sort="-x", title="UF"),
            color=alt.Color("payment_value:Q", scale=alt.Scale(scheme="blues"), legend=None)
        ).properties(height=300),
        use_container_width=True
    )

with col2.container(border=True):
    st.subheader("Participação por Categoria")
    vendas_cat = df.groupby("product_category_name")["payment_value"].sum().reset_index()
    st.altair_chart(
        alt.Chart(vendas_cat).mark_arc(innerRadius=50).encode(
            theta="payment_value:Q",
            color="product_category_name:N"
        ).properties(height=300),
        use_container_width=True
    )

st.subheader("Satisfação por Categoria")
with st.container(border=True):
    review_cat = df.groupby("product_category_name")["review_score"].mean().reset_index()
    meta_line = alt.Chart(pd.DataFrame({"x": [4]})).mark_rule(
        color="white", strokeDash=[5, 5]
    ).encode(x="x:Q")
    st.altair_chart(
        alt.Chart(review_cat).mark_bar().encode(
            x=alt.X("review_score:Q", scale=alt.Scale(domain=[0, 5]), title="Nota Média"),
            y=alt.Y("product_category_name:N", sort="-x", title=None),
            color=alt.Color("review_score:Q", scale=alt.Scale(scheme="redyellowgreen"))
        ).properties(height=350) + meta_line,
        use_container_width=True
    )

with st.container(border=True):
    st.subheader("Evolução de Vendas por Ano")
    chart_data_ano = df.groupby(["ano", "product_category_name"])["payment_value"].sum().reset_index()
    st.altair_chart(
        alt.Chart(chart_data_ano).mark_bar().encode(
            x=alt.X("ano:O", title="Ano"),
            y=alt.Y("payment_value:Q", title="R$"),
            color="product_category_name:N",
            xOffset="product_category_name:N"
        ).properties(height=300),
        use_container_width=True
    )

with st.expander("Dados Brutos"):
    st.dataframe(df.head(100), use_container_width=True)