import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import streamlit as st
import logging
load_dotenv()

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

def conexao_db():
    host = os.getenv('HOST')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    database = os.getenv('DATABASE')
    return create_engine(f'mysql+pymysql://{user}:{password}@{host}/{database}')

engine = conexao_db()

def get_categorias():
    query = text("SELECT DISTINCT product_category_name FROM olist_products WHERE product_category_name IS NOT NULL")
    return pd.read_sql_query(query, engine)['product_category_name'].tolist()

@st.cache_data

def load_full_data(anos, categorias):
    query = text("""
        SELECT
            YEAR(o.order_purchase_timestamp) as ano,
            o.order_id, p.payment_value, pr.product_category_name,
            r.review_score, c.customer_state
        FROM olist_orders o
        JOIN olist_order_payments p ON o.order_id = p.order_id
        JOIN olist_order_items i ON o.order_id = i.order_id
        LEFT JOIN olist_products pr ON i.product_id = pr.product_id
        JOIN olist_customers c ON o.customer_id = c.customer_id
        LEFT JOIN olist_order_reviews r ON o.order_id = r.order_id
        WHERE YEAR(o.order_purchase_timestamp) IN :anos
        AND pr.product_category_name IN :categorias

    """)

    return pd.read_sql_query(query, engine, params={"anos": anos, "categorias": categorias})