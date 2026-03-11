"""
Code Parser Tool — Tree-sitter based multi-language code structure extractor.

Supports Python, JavaScript, and Java.
Deterministic output for the same input.
"""

import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser


# ── Language Setup ──────────────────────────────────────────────────────────

LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
    "java": Language(tsjava.language()),
}


def _get_parser(language: str) -> Parser:
    """Create a parser for the given language."""
    lang_key = language.lower()
    if lang_key not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(LANGUAGES.keys())}")
    parser = Parser(LANGUAGES[lang_key])
    return parser


# ── Node text helper ────────────────────────────────────────────────────────

def _node_text(node, source_bytes: bytes) -> str:
    """Extract text content of a tree-sitter node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8").replace("\r", "")


# ── Python extractor ───────────────────────────────────────────────────────

def _extract_python(root_node, source_bytes: bytes) -> dict:
    """Extract functions and classes from Python source."""
    functions = []
    classes = []

    for child in root_node.children:
        if child.type == "function_definition":
            functions.append(_extract_python_function(child, source_bytes))
        elif child.type == "decorated_definition":
            # Handle decorated functions/classes
            for sub in child.children:
                if sub.type == "function_definition":
                    func = _extract_python_function(sub, source_bytes)
                    # Get decorators
                    decorators = [
                        _node_text(d, source_bytes)
                        for d in child.children if d.type == "decorator"
                    ]
                    func["decorators"] = decorators
                    functions.append(func)
                elif sub.type == "class_definition":
                    cls = _extract_python_class(sub, source_bytes)
                    decorators = [
                        _node_text(d, source_bytes)
                        for d in child.children if d.type == "decorator"
                    ]
                    cls["decorators"] = decorators
                    classes.append(cls)
        elif child.type == "class_definition":
            classes.append(_extract_python_class(child, source_bytes))

    return {"functions": functions, "classes": classes}


def _extract_python_function(node, source_bytes: bytes) -> dict:
    """Extract a single Python function's structure."""
    name = ""
    parameters = []
    return_type = None
    docstring = None

    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type == "parameters":
            for param in child.children:
                if param.type in ("identifier", "typed_parameter", "default_parameter",
                                  "typed_default_parameter", "list_splat_pattern",
                                  "dictionary_splat_pattern"):
                    param_text = _node_text(param, source_bytes)
                    if param_text not in ("(", ")", ",", "self", "cls"):
                        parameters.append(param_text)
        elif child.type == "type":
            return_type = _node_text(child, source_bytes)
        elif child.type == "block":
            # Check for docstring
            if child.children and child.children[0].type == "expression_statement":
                expr = child.children[0]
                if expr.children and expr.children[0].type == "string":
                    docstring = _node_text(expr.children[0], source_bytes).strip("\"'")

    result = {"name": name, "parameters": parameters}
    if return_type:
        result["return_type"] = return_type
    if docstring:
        result["docstring"] = docstring
    return result


def _extract_python_class(node, source_bytes: bytes) -> dict:
    """Extract a single Python class's structure."""
    name = ""
    bases = []
    methods = []
    docstring = None

    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type == "argument_list":
            for arg in child.children:
                if arg.type == "identifier":
                    bases.append(_node_text(arg, source_bytes))
        elif child.type == "block":
            # Check for class docstring
            if child.children and child.children[0].type == "expression_statement":
                expr = child.children[0]
                if expr.children and expr.children[0].type == "string":
                    docstring = _node_text(expr.children[0], source_bytes).strip("\"'")
            # Extract methods
            for block_child in child.children:
                if block_child.type == "function_definition":
                    methods.append(_extract_python_function(block_child, source_bytes))
                elif block_child.type == "decorated_definition":
                    for sub in block_child.children:
                        if sub.type == "function_definition":
                            method = _extract_python_function(sub, source_bytes)
                            decorators = [
                                _node_text(d, source_bytes)
                                for d in block_child.children if d.type == "decorator"
                            ]
                            method["decorators"] = decorators
                            methods.append(method)

    result = {"name": name, "methods": methods}
    if bases:
        result["bases"] = bases
    if docstring:
        result["docstring"] = docstring
    return result


# ── JavaScript extractor ───────────────────────────────────────────────────

def _extract_javascript(root_node, source_bytes: bytes) -> dict:
    """Extract functions and classes from JavaScript source."""
    functions = []
    classes = []

    for child in root_node.children:
        if child.type == "function_declaration":
            functions.append(_extract_js_function(child, source_bytes))
        elif child.type == "class_declaration":
            classes.append(_extract_js_class(child, source_bytes))
        elif child.type in ("lexical_declaration", "variable_declaration"):
            # Handle arrow functions and function expressions: const foo = () => {}
            for decl in child.children:
                if decl.type == "variable_declarator":
                    _extract_js_variable_declarator(decl, source_bytes, functions)
        elif child.type == "export_statement":
            for sub in child.children:
                if sub.type == "function_declaration":
                    functions.append(_extract_js_function(sub, source_bytes))
                elif sub.type == "class_declaration":
                    classes.append(_extract_js_class(sub, source_bytes))

    return {"functions": functions, "classes": classes}


def _extract_js_variable_declarator(node, source_bytes: bytes, functions: list):
    """Extract arrow/function-expression from a variable declarator."""
    name = ""
    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type in ("arrow_function", "function"):
            params = []
            for sub in child.children:
                if sub.type == "formal_parameters":
                    for p in sub.children:
                        if p.type == "identifier":
                            params.append(_node_text(p, source_bytes))
            functions.append({"name": name, "parameters": params})


def _extract_js_function(node, source_bytes: bytes) -> dict:
    """Extract a single JavaScript function."""
    name = ""
    parameters = []
    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            for param in child.children:
                if param.type == "identifier":
                    parameters.append(_node_text(param, source_bytes))
    return {"name": name, "parameters": parameters}


def _extract_js_class(node, source_bytes: bytes) -> dict:
    """Extract a JavaScript class."""
    name = ""
    methods = []
    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type == "class_body":
            for member in child.children:
                if member.type == "method_definition":
                    methods.append(_extract_js_function(member, source_bytes))
    return {"name": name, "methods": methods}


# ── Java extractor ─────────────────────────────────────────────────────────

def _extract_java(root_node, source_bytes: bytes) -> dict:
    """Extract classes (with methods) from Java source."""
    classes = []
    functions = []

    for child in root_node.children:
        if child.type == "class_declaration":
            classes.append(_extract_java_class(child, source_bytes))

    return {"functions": functions, "classes": classes}


def _extract_java_class(node, source_bytes: bytes) -> dict:
    """Extract a Java class."""
    name = ""
    methods = []
    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type == "class_body":
            for member in child.children:
                if member.type == "method_declaration":
                    methods.append(_extract_java_method(member, source_bytes))
                elif member.type == "constructor_declaration":
                    methods.append(_extract_java_method(member, source_bytes))
    return {"name": name, "methods": methods}


def _extract_java_method(node, source_bytes: bytes) -> dict:
    """Extract a Java method."""
    name = ""
    parameters = []
    return_type = None
    for child in node.children:
        if child.type == "identifier":
            name = _node_text(child, source_bytes)
        elif child.type in ("void_type", "type_identifier", "integral_type",
                            "floating_point_type", "boolean_type", "generic_type",
                            "array_type"):
            return_type = _node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            for param in child.children:
                if param.type == "formal_parameter":
                    param_name = ""
                    for p in param.children:
                        if p.type == "identifier":
                            param_name = _node_text(p, source_bytes)
                    if param_name:
                        parameters.append(param_name)
    result = {"name": name, "parameters": parameters}
    if return_type:
        result["return_type"] = return_type
    return result


# ── Main parse_code function ──────────────────────────────────────────────

EXTRACTORS = {
    "python": _extract_python,
    "javascript": _extract_javascript,
    "java": _extract_java,
}


def parse_code(source_code: str, language: str) -> dict:
    """
    Parse source code and extract its structure.
    
    This is a deterministic tool: same input always produces the same output.
    
    Args:
        source_code: The source code string to parse.
        language: Programming language ('python', 'javascript', 'java').
        
    Returns:
        Dictionary with 'language', 'functions', and 'classes' keys.
    """
    lang_key = language.lower()
    parser = _get_parser(lang_key)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    # Check for syntax errors
    has_errors = _has_errors(root_node)

    extractor = EXTRACTORS[lang_key]
    structure = extractor(root_node, source_bytes)

    result = {
        "language": lang_key,
        "functions": structure.get("functions", []),
        "classes": structure.get("classes", []),
        "has_errors": has_errors,
    }
    return result


def _has_errors(node) -> bool:
    """Recursively check if the parse tree contains any ERROR nodes."""
    if node.type == "ERROR":
        return True
    for child in node.children:
        if _has_errors(child):
            return True
    return False
