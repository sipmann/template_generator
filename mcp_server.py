from mcp.server.fastmcp import FastMCP

from template_generator.core import generate_from_sql, list_template_names, write_template


mcp = FastMCP("template-generator")


@mcp.tool(
    name="list_available_templates",
    description="List all available code templates",
)
def list_templates():
    files = list_template_names()

    return {
        "templates": files,
        "total": len(files),
    }


@mcp.tool(
    name="generate_template_from_sql",
    description="Generate code template from CREATE TABLE SQL and a selected template",
)
def gen_template_from_create_sql(sql: str, template_name: str):
    try:
        table, result = generate_from_sql(sql, template_name)

        return {
            "table": table,
            "generated": result,
        }
    except Exception as error:
        return {
            "error": str(error),
        }


@mcp.tool(
    name="create_new_template",
    description="Create a new code template with given name and content",
)
def criar_template(nome: str, conteudo: str):
    try:
        template_name = write_template(nome, conteudo, overwrite=False)
        return {"status": "ok", "template": template_name}
    except FileExistsError:
        return {"error": "template ja existe"}
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    mcp.run()
