#!/bin/bash

until python3 get_doc_scraper.py; do
    exit_code=$?
    
    # Check for specific error code (replace 1 with your target error code)
    if [ $exit_code -eq 35 ]; then
        echo "Script failed with error code $exit_code"
        continue
    else
        echo "Script exited with code $exit_code. Not restarting."
        break
    fi
done

# for i in docs/*.json; do
#     echo $(basename $i .json)00 >> existing_docs.txt
# done