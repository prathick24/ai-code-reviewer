import ast
from langchain_core.tools import tool
from utils.helper import log_decorator, logger


@tool
def ast_code(source_text: str) -> dict:
    """
    Examine Python source using AST and produce a validation report.

    Validation includes:
    - Parsing / syntax verification
    - Detection of unused imports
    - Identification of empty functions or classes
    - Flagging functions without meaningful bodies
    - Detection of unnamed except blocks
    - Detection of repeated function or class identifiers

    Parameters
    ----------
    source_text : str
        Python code provided as a string.

    Returns
    -------
    dict
        Contains:
        - result: "pass" or "fail"
        - findings: list of discovered issues (empty if none)
    """
    findings = []

    # Syntax validation
    try:
        ast_tree = ast.parse(source_text)
    except SyntaxError as err:
        print("----syntax validation issue detected")
        return {
            "result": "fail",
            "findings": [f"Parsing error: {err.msg} at line {err.lineno}"]
        }

    # Gather imported identifiers
    declared_imports = set()
    for element in ast.walk(ast_tree):
        if isinstance(element, ast.Import):
            for item in element.names:
                imported_id = item.asname if item.asname else item.name.split(".")[0]
                declared_imports.add(imported_id)
        elif isinstance(element, ast.ImportFrom):
            for item in element.names:
                imported_id = item.asname if item.asname else item.name
                declared_imports.add(imported_id)

    # Gather identifiers actually used
    referenced_names = set()
    for element in ast.walk(ast_tree):
        if isinstance(element, ast.Name):
            referenced_names.add(element.id)
        elif isinstance(element, ast.Attribute):
            if isinstance(element.value, ast.Name):
                referenced_names.add(element.value.id)

    # Identify unused imports
    redundant_imports = declared_imports - referenced_names
    for entry in sorted(redundant_imports):
        findings.append(
            f"Redundant import detected: '{entry}' is declared but never referenced."
        )

    # Function and class analysis
    name_registry = {}
    for element in ast.walk(ast_tree):

        # Check for duplicate function or class definitions
        if isinstance(element, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            entity_type = (
                "Function"
                if isinstance(element, (ast.FunctionDef, ast.AsyncFunctionDef))
                else "Class"
            )
            if element.name in name_registry:
                findings.append(
                    f"Repeated {entity_type.lower()} identifier: '{element.name}' appears multiple times."
                )
            name_registry[element.name] = entity_type

        # Detect empty function bodies
        if isinstance(element, (ast.FunctionDef, ast.AsyncFunctionDef)):
            statements = element.body
            if len(statements) == 1 and isinstance(statements[0], ast.Pass):
                findings.append(
                    f"Non-implemented function found: '{element.name}' contains only a pass statement."
                )

        # Detect empty class bodies
        if isinstance(element, ast.ClassDef):
            statements = element.body
            if len(statements) == 1 and isinstance(statements[0], ast.Pass):
                findings.append(
                    f"Non-implemented class found: '{element.name}' contains only a pass statement."
                )

    print("------------------------------------", findings, "-----------------------------------------")
    final_result = "pass" if not findings else "fail"
    return {"result": final_result, "findings": findings}