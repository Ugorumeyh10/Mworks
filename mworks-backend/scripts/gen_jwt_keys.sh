#!/bin/sh
set -eu
DIR="${1:-./secrets}"
mkdir -p "$DIR"
PRIV="$DIR/jwt_private.pem"
PUB="$DIR/jwt_public.pem"
if [ ! -f "$PRIV" ]; then
  openssl genrsa -out "$PRIV" 2048 >/dev/null 2>&1
  openssl rsa -in "$PRIV" -pubout -out "$PUB" >/dev/null 2>&1
  chmod 600 "$PRIV"
  echo "generated RS256 keypair in $DIR"
fi
