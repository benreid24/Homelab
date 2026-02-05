#!/bin/bash

systemctl stop satisfactory.service
sleep 60
systemctl start satisfactory.service
