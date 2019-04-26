#!/bin/bash
NAME=test
if [ -e $NAME.zip  ];then
  rm $NAME.zip
fi
zip -r9 $NAME.zip *
pip install -r requirements.txt --target .
aws lambda update-function-code \
 --function-name test \
 --region us-west-2 \
 --zip-file fileb://test.zip \
 --profile developer ;
echo $?
