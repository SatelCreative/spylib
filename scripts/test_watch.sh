#!/usr/bin/env bash

echo -e "\n ----- Tests ready to run when the code changes -----\n"

watchmedo shell-command --patterns="*.py" --recursive --command="scripts/test_suite.sh" --drop .
