#!/usr/bin/env python3
from common import ContractPackageError, check_compatibility

def main() -> int:
    try:
        result = check_compatibility()
    except ContractPackageError as error:
        print(f"FAIL: {error}")
        return 1
    print(f"{result['status']}: generated={result['generated']} pending={result['pending']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
