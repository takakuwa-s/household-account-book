#!/bin/sh

# Check number of arguments
# if test $# -ne 1 ; then
#   echo "number of arguments is not correct"
#   exit 1
# fi

rm code.zip
zip -r code.zip src/ resource/ .env main.py -x ".pytest_cache/*"  -x "*__pycache__/*" -x ".pytest_cache/*"

# lambda関数のアップデート
aws lambda update-function-code --function-name submit_reciepts --zip-file fileb://code.zip
aws lambda update-function-code --function-name analyze_receipt --zip-file fileb://code.zip
# aws lambda update-function-code --function-name $1 --zip-file fileb://lambda.zip
