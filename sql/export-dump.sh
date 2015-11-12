#!/bin/bash

mysqldump --add-drop-table -u root -p -h farmserver irrigation > database.sql
