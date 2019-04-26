#!/bin/bash
NAME=open-pr-commands
if [ -e $NAME.zip  ];then
  rm $NAME.zip
fi
zip -r9 $NAME.zip *
pip install -r requirements-lambda.txt --target .
aws lambda update-function-code \
 --function-name $NAME \
 --region us-west-2 \
 --zip-file fileb://$NAME.zip \
 --profile developer ;
echo $?
