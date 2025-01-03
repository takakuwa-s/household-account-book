#!/bin/sh

# Check number of arguments
# if test $# -ne 1 ; then
#   echo "number of arguments is not correct"
#   exit 1
# fi

rm submit_reciepts.zip
zip -r submit_reciepts.zip src/ resource/ .env main.py -x ".pytest_cache/*"  -x "*__pycache__/*" -x ".pytest_cache/*"

# lambda関数のアップデート
aws lambda update-function-code --function-name submit_reciepts --zip-file fileb://submit_reciepts.zip
# aws lambda update-function-code --function-name $1 --zip-file fileb://lambda.zip
