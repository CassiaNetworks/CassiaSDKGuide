#!/bin/bash

# shellcheck disable=SC1091
source version.sh

BUILD_DIR=/tmp/build
SRC_DIR=$BUILD_DIR/$NAME_VER/src

rm -rf "$BUILD_DIR"
mkdir -p "$SRC_DIR"

cp -r ./src/* "$SRC_DIR"
rm -rf "$SRC_DIR"/__pycache__

cd "$BUILD_DIR" || exit
gtar -zcvf "$NAME_VER".tar.gz "$NAME_VER"

cd - || exit
mv $BUILD_DIR/"$NAME_VER".tar.gz ./build

echo ""
ls -lh ./build/"$NAME_VER".tar.gz