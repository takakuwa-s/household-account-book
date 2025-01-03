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

echo "\n----- pip install 完了 -----\n"

# zipファイルの作成
rm python.zip
zip -r python.zip ./python

echo "\n----- python.zip作成完了 -----\n"

# layerのアップロード
aws lambda publish-layer-version \
  --layer-name pip-package-layer \
  --zip-file fileb://python.zip \
  --compatible-runtimes python3.12 \
  --compatible-architectures "arm64"

echo "\n----- layerの新バージョンアップロード完了 -----\n"

# layerの削除
aws lambda delete-layer-version --layer-name pip-package-layer --version-number 14

echo "\n----- layerの旧バージョン削除完了 -----\n"

# layerの指定
aws lambda update-function-configuration \
  --function-name submit_reciepts \
  --layers \
    "arn:aws:lambda:ap-northeast-1:101037559230:layer:pip-package-layer:15"

echo "\n----- 使用layerの切り替え完了 -----\n"

# 仮想環境の有効化解除
deactivate