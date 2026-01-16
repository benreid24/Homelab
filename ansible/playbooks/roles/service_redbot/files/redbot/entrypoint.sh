#!/usr/bin/env sh
set -e

# Ensure data directory has correct ownership
# Container starts as root, so this will work
chown -R ${RED_USER}:${RED_USER} ${RED_HOME}/data

# Install pip packages and start Red as specified user
exec runuser -u $RED_USER -- ${RED_HOME}/start-red.sh $@
