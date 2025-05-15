#!/usr/bin/env bash
# exit on error
set -o errexit

# Cài đặt psycopg2
pip install psycopg2-binary

# Chạy script tạo schema
python run_sql.py 