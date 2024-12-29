#!/bin/sh

# Check number of arguments
# if test $# -ne 1 ; then
#   echo "number of arguments is not correct"
#   exit 1
# fi

rm submit_reciepts.zip
zip -r submit_reciepts.zip . -x "*.git*" -x "*.sh" -x "*.zip" -x "*.txt" -x "*.md"  -x ".pytest_cache/*"  -x "*__pycache__/*" -x "layer/*"  -x ".pytest_cache/*" -x ".ruff_cache/*"

# lambda関数のアップデート
aws lambda update-function-code --function-name submit_reciepts --zip-file fileb://submit_reciepts.zip
# aws lambda update-function-code --function-name $1 --zip-file fileb://lambda.zip
