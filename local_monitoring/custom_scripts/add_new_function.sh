#!/bin/bash

HOME=`pwd`
sample_html='sample_template.txt'
main_file='run.py'

# echo ${HOME}/../${main_file}

if [ $# -ne 1 ]
then
  echo "please provide function name as arg"
  echo "Usage :- $0 function_name"
  echo "Exiting.."
  exit 1
fi
fn_name=$1
file=${HOME}/../${main_file}
html_file=${HOME}/../templates/index.html


function check_fn(){
    echo "Checking function_name and route in in $file"
    # function name check
    grep -q "def $fn_name" $file
    if [ $? -eq 0 ]
    then
      echo "Found in $file"
    else
      echo "function is not in $file"
      echo "Exiting.."
      exit 1
    fi
    #route name check
    grep -q "\@app.route('/${fn_name}')" $file
    if [ $? -eq 0 ]
    then
      echo "Route found in $file"
    else
      echo "Route  is not in $file"
      echo "Exiting.."
      exit 1
    fi

}

check_fn

function add_to_html(){
  echo "Adding html for $fn_name"
  cp $sample_html tmp_html.txt
  NAME=`echo $fn_name | awk '{print toupper($0)}'`
  TABLE=`echo $fn_name`
  ROUTE=`echo $fn_name`
  sed -i "s@CHANGE_NAME@$NAME@g" tmp_html.txt
  sed  -i "s@CHANGE_TABLE@$TABLE@g" tmp_html.txt
  sed  -i "s@CHANGE_ROUTE@$ROUTE@g" tmp_html.txt

}
add_to_html

sed -i -e '/REPLACE/rtmp_html.txt' $html_file
