"""
Documentation Generator Tool.

Converts parsed code structure JSON into human-readable markdown documentation.
Can operate in two modes:
  1. Template-based (deterministic, no LLM) — default fallback
  2. LLM-enhanced (uses Groq LLM for descriptions) — when agent provides descriptions
"""


def generate_docs_from_parsed(parsed_structure: dict, descriptions: dict = None) -> str:
    """
    Generate markdown documentation from a parsed code structure.
    
    This is the deterministic documentation generator tool.
    
    Args:
        parsed_structure: Output from parse_code tool.
        descriptions: Optional dict mapping function/class names to LLM-generated
                      descriptions. Keys are names, values are description strings.
    
    Returns:
        Markdown-formatted documentation string.
    """
    if descriptions is None:
        descriptions = {}

    language = parsed_structure.get("language", "unknown")
    functions = parsed_structure.get("functions", [])
    classes = parsed_structure.get("classes", [])
    has_errors = parsed_structure.get("has_errors", False)

    lines = []
    lines.append(f"# Code Documentation")
    lines.append(f"")
    lines.append(f"**Language:** {language.capitalize()}")
    lines.append(f"")

    if has_errors:
        lines.append("> ⚠️ **Warning:** The source code contains syntax errors. "
                      "Documentation may be incomplete.")
        lines.append("")

    if not functions and not classes:
        lines.append("_No functions or classes found in the source code._")
        return "\n".join(lines)

    # ── Functions ───────────────────────────────────────────────────────
    if functions:
        lines.append("## Functions")
        lines.append("")
        for func in functions:
            name = func.get("name", "unnamed")
            params = func.get("parameters", [])
            return_type = func.get("return_type")
            docstring = func.get("docstring")
            decorators = func.get("decorators", [])

            # Heading
            lines.append(f"### `{name}`")
            lines.append("")

            # Decorators
            if decorators:
                for dec in decorators:
                    lines.append(f"- Decorator: `{dec}`")
                lines.append("")

            # Signature
            param_str = ", ".join(params) if params else ""
            ret_str = f" → {return_type}" if return_type else ""
            lines.append(f"```")
            lines.append(f"{name}({param_str}){ret_str}")
            lines.append(f"```")
            lines.append("")

            # Parameters table
            if params:
                lines.append("**Parameters:**")
                lines.append("")
                lines.append("| Name | Description |")
                lines.append("|------|-------------|")
                for p in params:
                    param_name = p.split(":")[0].split("=")[0].strip().lstrip("*")
                    desc = descriptions.get(f"{name}.{param_name}", "_No description_").replace("\r", "")
                    lines.append(f"| `{param_name}` | {desc} |")
                lines.append("")

            # Description (from docstring or LLM)
            description = descriptions.get(name)
            if description:
                lines.append(f"**Description:** {description.replace(chr(13), '')}")
                lines.append("")
            elif docstring:
                lines.append(f"**Description:** {docstring}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # ── Classes ─────────────────────────────────────────────────────────
    if classes:
        lines.append("## Classes")
        lines.append("")
        for cls in classes:
            cls_name = cls.get("name", "unnamed")
            bases = cls.get("bases", [])
            methods = cls.get("methods", [])
            cls_docstring = cls.get("docstring")
            cls_decorators = cls.get("decorators", [])

            # Heading
            base_str = f"({', '.join(bases)})" if bases else ""
            lines.append(f"### `{cls_name}{base_str}`")
            lines.append("")

            # Decorators
            if cls_decorators:
                for dec in cls_decorators:
                    lines.append(f"- Decorator: `{dec}`")
                lines.append("")

            # Class description
            cls_desc = descriptions.get(cls_name)
            if cls_desc:
                lines.append(f"**Description:** {cls_desc.replace(chr(13), '')}")
                lines.append("")
            elif cls_docstring:
                lines.append(f"**Description:** {cls_docstring}")
                lines.append("")

            # Methods
            if methods:
                lines.append("#### Methods")
                lines.append("")
                for method in methods:
                    m_name = method.get("name", "unnamed")
                    m_params = method.get("parameters", [])
                    m_return = method.get("return_type")
                    m_docstring = method.get("docstring")
                    m_decorators = method.get("decorators", [])

                    if m_decorators:
                        for dec in m_decorators:
                            lines.append(f"- Decorator: `{dec}`")

                    m_param_str = ", ".join(m_params) if m_params else ""
                    m_ret_str = f" → {m_return}" if m_return else ""
                    lines.append(f"- **`{m_name}({m_param_str}){m_ret_str}`**")

                    m_desc = descriptions.get(f"{cls_name}.{m_name}")
                    if m_desc:
                        lines.append(f"  - {m_desc.replace(chr(13), '')}")
                    elif m_docstring:
                        lines.append(f"  - {m_docstring}")

                lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)
