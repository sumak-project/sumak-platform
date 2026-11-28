#!/usr/bin/env python3
from common import PACKAGE_ROOT

REQUIRED = (
    "README.md", "catalogo/package-policy.json", "catalogo/schemas-baseline.json",
    "generated/contract-catalog.json", "tools/common.py", "tools/generar.py",
    "tools/integraciones.py", "tools/trazabilidad.py", "tools/compatibilidad.py",
    "tools/revisar_estructura.py", "tools/validar.cjs",
)

def main() -> int:
    missing = [item for item in REQUIRED if not (PACKAGE_ROOT / item).is_file()]
    schemas = [
        str(path.relative_to(PACKAGE_ROOT)) for path in PACKAGE_ROOT.rglob("*")
        if path.is_file() and path.suffix in {".graphqls", ".proto", ".yaml", ".yml"}
    ]
    if missing or schemas:
        print(f"FAIL: missing={missing} unexpectedPendingSchemas={schemas}")
        return 1
    print(f"PASS: package structure contains {len(REQUIRED)} required files")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
