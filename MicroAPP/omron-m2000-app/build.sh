#!/bin/bash

# Read package metadata.
NAME=$(python3 -c "import json; print(json.load(open('meta.json'))['name'])")
VERSION=$(python3 -c "import json; print(json.load(open('meta.json'))['version'])")

# Build the package name.
PACKAGE_NAME="${NAME}.${VERSION}.tar.gz"

# Ensure required package files exist.
if [[ ! -f main.py || ! -f meta.json ]]; then
    echo "main.py or meta.json does not exist"
    exit 1
fi

# Remove old package files.
echo "Removing old package files..."
rm -f ${NAME}.*.tar.gz

# Package main.py and meta.json.
tar -czvf "$PACKAGE_NAME" main.py meta.json

echo "Package created: $PACKAGE_NAME"
