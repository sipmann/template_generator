import re
import sqlite3
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_STORAGE = BASE_DIR / "template_storage"
DEFAULT_TEMPLATE_CONTENT = """<h2>{{ table }}</h2>

{% for col in columns %}
{{ col.name }}
{% endfor %}
"""

ACCENT_FIX = {
    "acao": "a\u00e7\u00e3o",
    "acoes": "a\u00e7\u00f5es",
    "descricao": "descri\u00e7\u00e3o",
    "situacao": "situa\u00e7\u00e3o",
    "informacao": "informa\u00e7\u00e3o",
    "informacoes": "informa\u00e7\u00f5es",
    "numero": "n\u00famero",
    "usuario": "usu\u00e1rio",
    "usuarios": "usu\u00e1rios",
    "endereco": "endere\u00e7o",
    "observacao": "observa\u00e7\u00e3o",
    "observacoes": "observa\u00e7\u00f5es",
}


def ensure_storage() -> None:
    TEMPLATE_STORAGE.mkdir(exist_ok=True)


def filter_out_pk(columns):
    return [column for column in columns if column["pk"] == 0]


def ptbr_accent(word: str) -> str:
    value = word.lower()

    if value in ACCENT_FIX:
        return ACCENT_FIX[value]

    if value.endswith("cao"):
        return value[:-3] + "\u00e7\u00e3o"

    if value.endswith("coes"):
        return value[:-4] + "\u00e7\u00f5es"

    return value


def snake_to_title(value: str) -> str:
    words = []

    for word in value.split("_"):
        if not word:
            continue

        words.append(ptbr_accent(word).capitalize())

    return " ".join(words)


def get_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def extract_table_name(sql: str) -> str:
    match = re.search(r"create table\s+(\w+)", sql, re.IGNORECASE)
    if not match:
        raise ValueError("Nao foi possivel identificar o nome da tabela")
    return match.group(1)


def introspect(sql: str):
    conn = get_conn()

    try:
        conn.executescript(sql)
        table = extract_table_name(sql)
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return table, columns
    finally:
        conn.close()


def map_type(sqlite_type: str) -> str:
    value = sqlite_type.upper()

    if "INT" in value:
        return "number"

    if "REAL" in value or "DECIMAL" in value or "FLOAT" in value:
        return "number"

    if "DATE" in value:
        return "date"

    return "text"


def create_generator_env() -> Environment:
    ensure_storage()
    return Environment(
        loader=FileSystemLoader(TEMPLATE_STORAGE),
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=["jinja2.ext.loopcontrols"],
    )


def list_template_names():
    ensure_storage()
    return sorted(
        path.relative_to(TEMPLATE_STORAGE).as_posix()
        for path in TEMPLATE_STORAGE.rglob("*")
        if path.is_file()
    )


def normalize_template_name(name: str) -> str:
    normalized = name.strip()

    if not normalized:
        raise ValueError("Nome do template e obrigatorio")

    if not normalized.endswith(".jinja"):
        normalized += ".jinja"

    return normalized


def template_path(name: str) -> Path:
    normalized = normalize_template_name(name)
    path = (TEMPLATE_STORAGE / normalized).resolve()
    storage = TEMPLATE_STORAGE.resolve()

    if storage != path and storage not in path.parents:
        raise ValueError("Nome de template invalido")

    return path


def read_template(name: str) -> str:
    return template_path(name).read_text(encoding="utf-8")


def write_template(name: str, content: str, overwrite: bool = True) -> str:
    ensure_storage()
    path = template_path(name)

    if path.exists() and not overwrite:
        raise FileExistsError("Template ja existe")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path.relative_to(TEMPLATE_STORAGE).as_posix()


def generate_from_sql(sql: str, template_name: str) -> tuple[str, str]:
    table, columns = introspect(sql)
    template = create_generator_env().get_template(template_name)
    generated = template.render(
        table=table,
        columns=columns,
        columns_no_pk=filter_out_pk(columns),
        gen_label=snake_to_title,
        map_type=map_type,
    )

    return table, generated
