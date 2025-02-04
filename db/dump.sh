#!/bin/bash

HOST="localhost"
PORT="8110"
USER="kube"
DB="optimsportbets-db"

TABLES=("soccer_odds")

for TABLE in "${TABLES[@]}"; do
  OUTPUT_FILE="${TABLE}.csv"
  psql -h $HOST -p $PORT -U $USER -d $DB -c "\COPY $TABLE TO '$OUTPUT_FILE' CSV HEADER"
  echo "Exported $TABLE to $OUTPUT_FILE"
done
