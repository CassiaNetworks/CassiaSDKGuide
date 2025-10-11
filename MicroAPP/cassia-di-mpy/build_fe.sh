#!/usr/bin/env bash

cd fe || exit

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm use 22
echo "use node 22 ok"

npm install
echo "npm install ok"

npm run build
echo "npm build ok"

cd - || exit

index_html_bytes=$(hexdump -v -e '"\\x" 1/1 "%02x"' fe/dist/index.html.gz | tr -d '\n')
echo "INDEX_HTML_BYTES = b\"${index_html_bytes}\"" > src/http_static.py
echo "write index html bytes to src/http_static.py ok"
