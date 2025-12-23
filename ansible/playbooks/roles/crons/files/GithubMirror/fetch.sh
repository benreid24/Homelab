#!/bin/bash

# Directory containing the repositories
base_dir="$1"

# Check if directory was provided
if [ -z "$base_dir" ]; then
  echo "Usage: $0 /path/to/repositories"
  exit 1
fi

# Find all top-level directories that contain a .git directory and update them
for repo_dir in "$base_dir"/*; do
  if [ -d "$repo_dir/.git" ]; then
    echo "Updating repository: $repo_dir"
    (cd "$repo_dir" && git fetch && git pull)
  fi
done
