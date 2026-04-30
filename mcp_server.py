import os
import re
import sqlite3
from jinja2 import Environment, FileSystemLoader
from mcp.server.fastmcp import FastMCP

# ================================
# PATHS (sempre absoluto)
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_STORAGE = os.path.join(BASE_DIR, "template_storage")

os.makedirs(TEMPLATE_STORAGE, exist_ok=True)

# ================================
# MCP INIT
# ================================
mcp = FastMCP("template-generator")

# ================================
# HELPERS (copiados do seu app)
# ================================

def filter_out_pk(columns):
    return [c for c in columns if c["pk"] == 0]


ACCENT_FIX = {
    "acao": "ação",
    "acoes": "ações",
    "descricao": "descrição",
    "situacao": "situação",
    "informacao": "informação",
    "informacoes": "informações",
    "numero": "número",
    "usuario": "usuário",
    "usuarios": "usuários",
    "endereco": "endereço",
    "observacao": "observação",
    "observacoes": "observações"
}


def ptbr_accent(word: str) -> str:
    w = word.lower()

    if w in ACCENT_FIX:
        return ACCENT_FIX[w]

    if w.endswith("cao"):
        return w[:-3] + "ção"

    if w.endswith("coes"):
        return w[:-4] + "ções"

    return w


def snake_to_title(value: str) -> str:
    words = []
    for w in value.split("_"):
        if not w:
            continue
        w = ptbr_accent(w)
        words.append(w.capitalize())

    return " ".join(words)


def map_type(sqlite_type):
    t = sqlite_type.upper()

    if "INT" in t:
        return "number"

    if "REAL" in t or "DECIMAL" in t or "FLOAT" in t:
        return "number"

    if "DATE" in t:
        return "date"

    return "text"


def get_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def extract_table_name(sql: str) -> str:
    match = re.search(r"create table\s+(\w+)", sql, re.IGNORECASE)
    if not match:
        raise Exception("Não foi possível identificar o nome da tabela")
    return match.group(1)


def introspect(sql):
    conn = get_conn()
    conn.executescript(sql)

    table = extract_table_name(sql)

    columns = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    conn.close()

    return table, columns


# ================================
# JINJA ENV (isolado)
# ================================
generator_env = Environment(
    loader=FileSystemLoader(TEMPLATE_STORAGE),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)

# ================================
# TOOLS
# ================================

@mcp.tool(
    name="list_available_templates",
    description="List all available code templates"
)
def list_templates():
    files = os.listdir(TEMPLATE_STORAGE)

    return {
        "templates": files,
        "total": len(files)
    }


@mcp.tool(
    name="generate_template_from_sql",
    description="Generate code template from CREATE TABLE SQL and a selected template"
)
def gen_template_from_create_sql(sql: str, template_name: str):
    try:
        table, columns = introspect(sql)

        template = generator_env.get_template(template_name)

        result = template.render(
            table=table,
            columns=columns,
            columns_no_pk=filter_out_pk(columns),
            gen_label=snake_to_title,
            map_type=map_type
        )

        return {
            "table": table,
            "generated": result
        }

    except Exception as e:
        return {
            "error": str(e)
        }


@mcp.tool(
    name="create_new_template",
    description="Create a new code template with given name and content"
)
def criar_template(nome: str, conteudo: str):
    try:
        if not nome.endswith(".jinja"):
            nome += ".jinja"

        path = os.path.join(TEMPLATE_STORAGE, nome)

        if os.path.exists(path):
            return {"error": "template já existe"}

        with open(path, "w", encoding="utf-8") as f:
            f.write(conteudo)

        return {"status": "ok", "template": nome}

    except Exception as e:
        return {"error": str(e)}


# ================================
# RUN
# ================================
if __name__ == "__main__":
    mcp.run()