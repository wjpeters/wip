"""Export canonical FastAPI/Pydantic wire schemas and generate consumer types."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
from app.main import app  # noqa: E402 - local package path is initialized above

schema = app.openapi()
folder = ROOT / "packages/contracts"
(folder / "openapi.json").write_text(
    json.dumps(schema, indent=2, sort_keys=True) + "\n"
)
models = schema["components"]["schemas"]


def ref(s):
    return s["$ref"].split("/")[-1]


def ts(s):
    if "$ref" in s:
        return ref(s)
    if "const" in s:
        return json.dumps(s["const"])
    if "enum" in s:
        return " | ".join(map(json.dumps, s["enum"]))
    if "anyOf" in s:
        return "(" + " | ".join(map(ts, s["anyOf"])) + ")"
    t = s.get("type")
    if t == "array":
        return "Array<" + ts(s.get("items", {})) + ">"
    if t == "object":
        return (
            "Record<string," + ts(s.get("additionalProperties", {})) + ">"
            if isinstance(s.get("additionalProperties", {}), dict)
            else "Record<string,unknown>"
        )
    return {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "null": "null",
    }.get(t, "unknown")


def py(s):
    if "$ref" in s:
        return ref(s)
    if "const" in s:
        return "Literal[" + repr(s["const"]) + "]"
    if "enum" in s:
        return "Literal[" + ", ".join(map(repr, s["enum"])) + "]"
    if "anyOf" in s:
        return " | ".join(map(py, s["anyOf"]))
    t = s.get("type")
    if t == "array":
        return "list[" + py(s.get("items", {})) + "]"
    if t == "object":
        return (
            "dict[str," + py(s.get("additionalProperties", {})) + "]"
            if isinstance(s.get("additionalProperties", {}), dict)
            else "dict[str,Any]"
        )
    return {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "null": "None",
    }.get(t, "Any")


def rust(s):
    if "$ref" in s:
        return ref(s)
    t = s.get("type")
    if "anyOf" in s:
        members = [v for v in s["anyOf"] if v.get("type") != "null"]
        if len(members) == 1:
            return "Option<" + rust(members[0]) + ">"
        return "serde_json::Value"
    if t == "array":
        return "Vec<" + rust(s.get("items", {})) + ">"
    if t == "object":
        return (
            "std::collections::BTreeMap<String,"
            + rust(s.get("additionalProperties", {}))
            + ">"
            if isinstance(s.get("additionalProperties", {}), dict)
            else "serde_json::Value"
        )
    return {
        "string": "String",
        "integer": "i64",
        "number": "f64",
        "boolean": "bool",
    }.get(t, "serde_json::Value")


types = ["// GENERATED from canonical API/Pydantic definitions. Do not edit."]
python = [
    "# GENERATED. Runtime authority remains the canonical Pydantic request model.",
    "from __future__ import annotations",
    "from typing import Any,Literal",
    "from pydantic import BaseModel,ConfigDict",
    "class WireModel(BaseModel):",
    '    model_config=ConfigDict(extra="forbid")',
]
rs = [
    "// GENERATED API types. Validate incoming JSON against openapi.json before use.",
    "use serde::{Serialize,Deserialize};",
]
for name, s in models.items():
    if s.get("type") != "object":
        continue
    types.append("export type " + name + " = {")
    python.append("class " + name + "(WireModel):")
    rs.extend(
        [
            "#[derive(Debug,Clone,Serialize,Deserialize)]",
            "#[serde(deny_unknown_fields)]",
            "pub struct " + name + " {",
        ]
    )
    if not s.get("properties"):
        python.append("    pass")
    for key, value in s.get("properties", {}).items():
        optional = key not in s.get("required", [])
        types.append(
            "  " + json.dumps(key) + ("?" if optional else "") + ": " + ts(value) + ";"
        )
        python.append(
            "    "
            + key
            + ": "
            + py(value)
            + (" = " + repr(value.get("default")) if optional else "")
        )
        rt = rust(value)
        if optional and not rt.startswith("Option<"):
            rt = "Option<" + rt + ">"
        rs.append(
            "    pub "
            + ("r#" + key if key in ["type", "ref", "match"] else key)
            + ": "
            + rt
            + ","
        )
    types.append("};")
    rs.append("}")
    python.append("")
python.append(
    "for _model in list(globals().values()):\n    if isinstance(_model,type) and issubclass(_model,WireModel):_model.model_rebuild()"
)
(folder / "api.generated.ts").write_text("\n".join(types) + "\n")
(ROOT / "apps/web/src/api.generated.ts").write_text("\n".join(types) + "\n")
(folder / "api.generated.py").write_text("\n".join(python) + "\n")
(folder / "rust/src/api.rs").write_text("\n".join(rs) + "\n")
print(f"Exported {len(models)} API schemas and Python/TypeScript/Rust types.")
