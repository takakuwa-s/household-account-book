#!/bin/sh

# layerの作成
pip install -r requirements.txt --target ./python/

# zipファイルの作成
rm python.zip
zip -r python.zip ./python

# layerのアップロード
aws lambda publish-layer-version \
  --layer-name pip-package-layer \
  --zip-file fileb://python.zip \
  --compatible-runtimes python3.13

# layerの指定
aws lambda update-function-configuration \
  --function-name submit_reciepts \
  --layers \
    "arn:aws:lambda:ap-northeast-1:101037559230:layer:pip-package-layer:5"