import os
import json
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage

SYSTEM_PROMPT = """Você é um assistente de dados da Olist. Responda sempre em Português.

Você tem duas ferramentas:
- query_database: para perguntas factuais (totais, médias, rankings)
- generate_chart: para gráficos

REGRA CRÍTICA PARA GRÁFICOS:
Quando o usuário pedir qualquer gráfico:
1. Chame a ferramenta generate_chart
2. Pegue o JSON retornado pela ferramenta
3. Retorne APENAS o JSON cru, sem nenhum texto antes ou depois
4. NUNCA resuma ou descreva o gráfico — retorne só o JSON

Tipos de gráfico:
  bar   → comparar categorias/estados
  line  → evolução temporal
  pie   → participação percentual
  point → correlação entre variáveis
"""


async def get_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        #model="gpt-4o-mini",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        #api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    )

    client = MultiServerMCPClient({
        "olist": {
            "command": "python",
            "args": ["-m", "utils.mcp_server"],
            "transport": "stdio",
        }
    })

    tools = await client.get_tools()
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    return agent


async def run_agent(prompt: str) -> dict:
    agent = await get_agent()
    result = await agent.ainvoke({"messages": [("user", prompt)]})


    all_messages = result["messages"]
    for msg in reversed(all_messages):
        content = msg.content if hasattr(msg, "content") else ""


        if isinstance(content, list):
            for block in content:
                text = block.get("text", "") if isinstance(block, dict) else str(block)
                spec = _try_parse_chart(text)
                if spec:
                    return {"type": "chart", "content": spec}

        if isinstance(content, str):
            spec = _try_parse_chart(content)
            if spec:
                return {"type": "chart", "content": spec}


    resposta = result["messages"][-1].content
    if isinstance(resposta, list):
        resposta = " ".join(b.get("text", "") for b in resposta if isinstance(b, dict))
    return {"type": "text", "content": resposta}


def _try_parse_chart(text: str):
    """Tenta extrair um spec Vega-Lite válido de uma string."""
    if not isinstance(text, str):
        return None
    if '"$schema"' not in text and '"mark"' not in text:
        return None
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        spec = json.loads(text[start:end])

        if "mark" in spec and "encoding" in spec:
            return spec
    except Exception:
        pass
    return None