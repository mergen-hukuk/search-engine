#!/bin/bash

# Check if directory is provided as argument
if [ $# -eq 0 ]; then
    DIR="."  # Use current directory if no argument
else
    DIR="$1"
fi

# Initialize previous count
prev_count=$(find "$DIR" -maxdepth 1 -type f | wc -l)
echo "Initial count: $prev_count"

while true; do
    # Get current count of files
    current_count=$(find "$DIR" -maxdepth 1 -type f | wc -l)
    
    # Calculate change
    change=$((current_count - prev_count))
    
    # Create change message with sign
    if [ $change -gt 0 ]; then
        change_msg="+$change"
    else
        change_msg="$change"
    fi
    
    # Print current time, file count and change
    echo "$(date +"%H:%M:%S") - Files: $current_count (Change: $change_msg)"
    
    # Update previous count
    prev_count=$current_count
    
    # Wait for 10 seconds
    sleep 10
done