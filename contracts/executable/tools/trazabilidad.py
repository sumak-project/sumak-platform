#!/usr/bin/env python3
from common import ContractPackageError, MATRIX_PATH, load_json, validate_matrix

def main() -> int:
    try:
        validate_matrix(load_json(MATRIX_PATH))
    except ContractPackageError as error:
        print(f"FAIL: {error}")
        return 1
    print("PENDING: 162 routes are traceable; executable equivalence is not certified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
