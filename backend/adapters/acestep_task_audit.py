"""Find literal tasks or a task CLI enum forwarded to the handler."""
import ast


def wrapper_tasks(tree: ast.AST) -> list[str]:
    tasks = set()
    forwards_task = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "task_type":
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                tasks.add(keyword.value.value)
            elif (isinstance(keyword.value, ast.Attribute) and keyword.value.attr == "task_type"
                  and isinstance(keyword.value.value, ast.Name) and keyword.value.value.id == "args"):
                forwards_task = True
    if forwards_task:
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_argument" and node.args
                    and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--task-type"):
                choices = next((kw.value for kw in node.keywords if kw.arg == "choices"), None)
                if isinstance(choices, (ast.Tuple, ast.List)):
                    tasks.update(item.value for item in choices.elts
                                 if isinstance(item, ast.Constant) and isinstance(item.value, str))
    return sorted(tasks)
