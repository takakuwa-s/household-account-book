#!/bin/sh

# 仮想環境の有効化
source .venv/bin/activate.fish

# layerの作成
pip install \
  --platform manylinux2014_aarch64 \
  --target=./python/ \
  --implementation cp \
  --python-version 3.12 \
  -r requirements.txt \
  --only-binary=:all: --upgrade

# zipファイルの作成
rm python.zip
zip -r python.zip ./python

# layerのアップロード
aws lambda publish-layer-version \
  --layer-name pip-package-layer \
  --zip-file fileb://python.zip \
  --compatible-runtimes python3.12 \
  --compatible-architectures "arm64"

# layerの削除
aws lambda delete-layer-version --layer-name pip-package-layer --version-number 14

# layerの指定
aws lambda update-function-configuration \
  --function-name submit_reciepts \
  --layers \
    "arn:aws:lambda:ap-northeast-1:101037559230:layer:pip-package-layer:14"

# 仮想環境の有効化解除
deactivate