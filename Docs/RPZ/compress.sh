#!/bin/bash

SOURCE_DIR="$1"

[ ! -d "$SOURCE_DIR" ] && exit 1

find "$SOURCE_DIR" -type f -iname "*.pdf" -print0 | while IFS= read -r -d '' pdf_file; do
  tmp_file=$(mktemp --suffix=.pdf)

  gs -sDEVICE=pdfwrite \
    -dCompatibilityLevel=1.4 \
    -dNOPAUSE \
    -dOptimize=true \
    -dQUIET \
    -dBATCH \
    -dRemoveUnusedFonts=true \
    -dRemoveUnusedImages=true \
    -dOptimizeResources=true \
    -dDetectDuplicateImages \
    -dCompressFonts=true \
    -dEmbedAllFonts=true \
    -dSubsetFonts=true \
    -dPreserveAnnots=true \
    -dPreserveMarkedContent=true \
    -dPreserveOverprintSettings=true \
    -dPreserveHalftoneInfo=true \
    -dPreserveOPIComments=true \
    -dPreserveDeviceN=true \
    -dMaxInlineImageSize=0 \
    -sOutputFile="$tmp_file" \
    "$pdf_file" >/dev/null 2>&1

  if [ -f "$tmp_file" ] && [ -s "$tmp_file" ]; then
    mv "$tmp_file" "$pdf_file"
  else
    rm -f "$tmp_file"
  fi
done
