
import re
import csv
from pathlib import Path

CSV_PATH = Path(r"C:/Users/128669/Downloads/sct/aws-sct-assessment.csv")
SQL_PATH = Path(r"C:/Users/128669/Downloads/sct/oracle_objects.sql")
OUTPUT_DIR = Path(r"C:/Users/128669/Downloads/sct/prompts")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def normalize_name(name: str) -> str:
    name = name.strip()
    if name.startswith('"') and name.endswith('"'):
        return name
    return name.upper()

def build_definition_index(sql_text: str):
    pattern = re.compile(
        r"""(?imxs)
        ^\s*
        create\s+(?:or\s+replace\s+)?
        (?P<type>table|view|function|procedure|package(?:\s+body)?|trigger|sequence)
        \s+
        (?P<name>
            (?:"[^"]+"|\w+)(?:\.\w+|(?:\."[^"]+"))?
        )
        (?P<body>.*?)
        (?=
            ^\s*/\s*$
            | ^\s*create
            | \Z
        )
        """,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )

    index = {}
    for m in pattern.finditer(sql_text):
        raw_name = m.group("name").strip()
        body = m.group(0).rstrip()
        # Unqualified name for key
        if "." in raw_name and not raw_name.startswith('"'):
            key_name = raw_name.split(".")[-1]
        elif raw_name.startswith('"') and "." in raw_name:
            parts = re.findall(r'"[^"]+"|\w+', raw_name)
            key_name = parts[-1]
        else:
            key_name = raw_name
        key = normalize_name(key_name)
        index.setdefault(key, []).append(body)
    return index

def make_prompt(obj_name:str, obj_type:str=None, issue:str=None, severity:str=None, notes:str=None, definitions:list=None):
    # Construct a markdown prompt for LLMs / engineers
    lines = []
    lines.append(f"# Migration Prompt: {obj_name}")
    # if obj_type or issue or severity or notes:
    #     lines.append("\n## Assessment (from AWS SCT)")
    #     if obj_type:
    #         lines.append(f"- **Object Type:** {obj_type}")
    #     if issue:
    #         lines.append(f"- **Issue:** {issue}")
    #     if severity:
    #         lines.append(f"- **Severity:** {severity}")
    #     if notes:
    #         lines.append(f"- **Notes:** {notes}")
    
    if definitions:
        #lines.append("\n## Oracle Definition(s)")
        for i, d in enumerate(definitions, start=1):
            #lines.append(f"\n### Definition {i}\n")
            lines.append("```sql")
            lines.append(d)
            lines.append("```")
    else:
        lines.append("\n> No Oracle definition found in `oracle_objects.sql` for this object.")

    # Task instructions
    lines.append("\n## Task")
    lines.append(
        "Convert the given Oracle object(s) into PostgreSQL-compatible DDL/DML."
        "Output only the converted SQL. "
        "Do not include explanations, comments, best practices, or indentation."

#        "Explain the differences, propose equivalents (e.g., partitions, triggers, packages), and provide final PostgreSQL code. "
#        "Highlight any manual steps required and validation strategies."
    )

    # # Acceptance criteria
    # lines.append("\n## Acceptance Criteria")
    # lines.append("- Provide complete PostgreSQL code blocks.")
    # lines.append("- Note any unsupported Oracle features and recommended redesigns.")
    # lines.append("- Include test queries or steps to validate the migration.")

    return "\n".join(lines)

def main():
    sql_text = load_sql(SQL_PATH)
    index = build_definition_index(sql_text)

    created = []
    with CSV_PATH.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        # Map header columns
        col_map = {}
        if header:
            for i, h in enumerate(header):
                key = h.strip().lower()
                col_map[key] = i
        # Defaults
        obj_idx = col_map.get("object name", 0)
        type_idx = col_map.get("object type", None)
        issue_idx = col_map.get("issue", None)
        severity_idx = col_map.get("severity", None)
        notes_idx = col_map.get("notes", None)

        for row_num, row in enumerate(reader, start=2):
            if not row or len(row) <= obj_idx:
                continue
            obj_name = row[obj_idx].strip()
            obj_type = row[type_idx].strip() if (type_idx is not None and len(row) > type_idx) else None
            issue = row[issue_idx].strip() if (issue_idx is not None and len(row) > issue_idx) else None
            severity = row[severity_idx].strip() if (severity_idx is not None and len(row) > severity_idx) else None
            notes = row[notes_idx].strip() if (notes_idx is not None and len(row) > notes_idx) else None

            defs = index.get(normalize_name(obj_name), [])
            prompt_text = make_prompt(obj_name, obj_type, issue, severity, notes, defs)
            # Safe filename
            safe_name = re.sub(r"[^A-Za-z0-9_\\-]", "_", obj_name)
            out_path = OUTPUT_DIR / f"prompt_{safe_name}_{row_num:02d}.txt"
            out_path.write_text(prompt_text, encoding="utf-8")
            created.append(str(out_path))

    print({"created_files": created})

if __name__ == "__main__":
    main()
