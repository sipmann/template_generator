# Template Generator

From time to time I have a simple CRUD to make, with small changes between them. This simple webapp enable me to just generate some code based in a template and a simples create table SQL.

## MCP

This project includes a **Model Context Protocol (MCP) Server** integration, allowing you to use Template Generator directly from MCP-compatible clients (like Claude Desktop, or integrated in other applications).

### Available MCP Tools

1. **list_available_templates**
   - Description: List all available code templates
   - Returns: Array of template names and total count

2. **generate_template_from_sql**
   - Description: Generate code from a CREATE TABLE SQL and a selected template
   - Parameters:
     - `sql`: CREATE TABLE SQL statement
     - `template_name`: Name of the template to use
   - Returns: Generated code based on the template

3. **create_new_template**
   - Description: Create a new code template with given name and content
   - Parameters:
     - `nome`: Template name
     - `conteudo`: Template content (Jinja2 format)
   - Returns: Status and template name

### Running the MCP Server

```bash
python mcp_server.py

# TODOs

- [X] Columns without PK (for less code in the template)
- [X] Snake_Case strings to proper Titles
- [X] Template Folder structure for better organization

# Structure

- `app.py`: Flask web interface.
- `mcp_server.py`: MCP tools interface.
- `template_generator/core.py`: shared SQL introspection, template storage, and rendering logic.
