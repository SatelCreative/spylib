#!/usr/bin/env bash


reportvalidation() {
  if [ -z "$1" ]
  then
    echo "OK"
  else
    echo -e "\e[1m\e[91mFAILED\e[21m\e[39m"
    echo "$1"
  fi
}


python -m pytest -vv --durations=3 --cov=spylib --cov-report term-missing

echo -ne "\n######### CHECK TYPING: "
MYPYOUT=`mypy --no-error-summary .`
reportvalidation "$MYPYOUT"

echo -ne "\n######### CHECK LINTING: "
FLAKE8OUT=`flake8`
reportvalidation "$FLAKE8OUT"

echo -ne "\n######### CHECK FORMATTING: "
BLACKOUT=`black spylib tests --check 2>&1`
if [[ $BLACKOUT == "All done!"* ]]
then
  echo "OK"
else
  echo -e "\e[1m\e[91mFAILED\e[21m\e[39m"
  echo "$BLACKOUT"
fi

echo
