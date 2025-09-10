#!/bin/bash

# shellcheck disable=SC1091
source version.sh

MERGE_PY=$NAME_VER.py
MIN_PY=$NAME_VER.min.py
MPY=$NAME_VER.mpy

micropython merge_app.py "$MERGE_PY"
echo ""
echo "merge src ok -> $MERGE_PY"

python -m python_minifier --remove-literal-statements "$MERGE_PY" > "$MIN_PY"
echo "minifier src ok -> $MIN_PY"

mpy-cross -o "$MPY" "$MIN_PY"
echo "build mpy ok -> $MPY"

echo ""
ls -lh "$NAME_VER".*
mv "$NAME_VER".* build