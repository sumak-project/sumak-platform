#!/usr/bin/env python3
from common import ContractPackageError, POLICY_PATH, load_json, validate_policy

def main() -> int:
    try:
        validate_policy(load_json(POLICY_PATH))
    except ContractPackageError as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: approved GraphQL/gRPC/Kafka/RabbitMQ/WSS/technical-HTTP policy")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
