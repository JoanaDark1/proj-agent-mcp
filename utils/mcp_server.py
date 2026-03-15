import pandas as pd
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from utils.database import engine

mcp = FastMCP("Olist")


@mcp.tool()
def query_database(sql_query: str) -> str:
    """
    Executa uma query SQL no banco Olist e retorna os resultados.
    Use para perguntas factuais: totais, contagens, médias, rankings.
    O banco é MySQL com as tabelas:
      olist_orders, olist_order_payments, olist_order_items,
      olist_order_reviews, olist_products, olist_customers, olist_sellers.
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(sql_query), conn)
        if df.empty:
            return "Nenhum dado encontrado."
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Erro SQL: {str(e)}"


@mcp.tool()
def generate_chart(sql_query: str, x_field: str, y_field: str,
                   chart_type: str = "bar", title: str = "") -> str:
    """
    Gera um gráfico Vega-Lite com dados do banco Olist.
    Parâmetros:
      - sql_query : query SQL que retorna os dados do gráfico
      - x_field   : nome da coluna para eixo X (ou fatias no pie)
      - y_field   : nome da coluna para eixo Y (ou tamanho das fatias)
      - chart_type: "bar" | "line" | "point" | "pie"
      - title     : título do gráfico
    Retorna o spec Vega-Lite como JSON string.
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(sql_query), conn)
        if df.empty:
            return "Sem dados para gerar gráfico."

        records = df.to_dict(orient="records")

        if chart_type == "pie":
            spec = {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": title,
                "mark": {"type": "arc", "innerRadius": 50},
                "data": {"values": records},
                "encoding": {
                    "theta": {"field": y_field, "type": "quantitative"},
                    "color": {"field": x_field, "type": "nominal"}
                }
            }
        else:
            spec = {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": title,
                "mark": chart_type,
                "data": {"values": records},
                "encoding": {
                    "x": {"field": x_field, "type": "nominal", "sort": "-y"},
                    "y": {"field": y_field, "type": "quantitative"},
                    "tooltip": [
                        {"field": x_field, "type": "nominal"},
                        {"field": y_field, "type": "quantitative"}
                    ]
                }
            }

        import json
        return json.dumps(spec)

    except Exception as e:
        return f"Erro ao gerar gráfico: {str(e)}"


if __name__ == "__main__":
    mcp.run()