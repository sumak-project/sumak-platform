#!/usr/bin/env python3
import argparse
from common import ContractPackageError, generate

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        catalog = generate(check=args.check)
    except ContractPackageError as error:
        print(f"FAIL: {error}")
        return 1
    print(f"{catalog['status']}: rows={catalog['rowCount']} generated={catalog['generatedCount']} pending={catalog['pendingCount']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
