import ast
from pathlib import Path

# The only file allowed to import litellm
ALLOWED_FILE = "litellm_client.py"


def imports_litellm(path: Path) -> bool:
    
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        # Case 1: "import litellm"
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "litellm":
                    return True
        # Case 2: "from litellm import ..."
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == "litellm":
                return True

    return False


def test_litellm_used_only_in_client():
    
    offenders = [
        str(file)
        for file in Path("app").rglob("*.py")
        if imports_litellm(file)
    ]

    # Only litellm_client.py may appear in the list
    others = [f for f in offenders if Path(f).name != ALLOWED_FILE]
    assert others == [], f"These files must not import litellm: {others}"
