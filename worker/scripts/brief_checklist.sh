#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8787}"

echo "GET /datasets"
curl -sS -D- "$BASE/datasets"
echo
echo "POST Trade Confirmations"
curl -sS -D- "$BASE/datasets" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Trade Confirmations","owner":"Middle Office","description":"Daily export of confirmed trades including instrument type, counterparty, notional value, and settlement date."}'
echo
echo "DELETE /datasets/1"
curl -sS -D- -X DELETE "$BASE/datasets/1"
echo
echo "GET after delete"
curl -sS "$BASE/datasets"
echo
echo "POST missing fields"
curl -sS -D- "$BASE/datasets" \
  -H 'Content-Type: application/json' \
  -d '{}'
echo
