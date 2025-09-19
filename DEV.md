# Installation for local development

# 1. Clone the repository
```
git clone
cd SoccerBetMLOptimizer
```

# 2. Get the db
You will need psql (PostgreSQL client) and preferably pgAdmin to see the database (can manage as well but we use migrations with a custom script to apply changes).
```
set -a
source prod.env
set +a
kubectl port-forward -n optimsportbets pod/postgresql-global-0 $DB_PORT:5432
cd db
pg_dump -h localhost -U $DB_USER -p $DB_PORT -d optimsportbets-db -F c -b -v -f optimsportbets-db.dump
pg_dump --schema-only --no-owner --no-privileges -h localhost -U $DB_USER -p $DB_PORT -d optimsportbets-db > schema_before.sql
pg_dump --schema-only --no-owner --no-privileges -h localhost -U postgres -p $DB_PORT > schema_before.sql

# if you already created the database skip next line
cd ..
set -a
source dev.env
set +a
createdb -U $DB_USER -p $DB_PORT optimsportbets-db
cd db
pg_restore -h localhost -U $DB_USER -p $DB_PORT -d optimsportbets-db -v optimsportbets-db.dump

# to access the database with command line
psql -U $DB_USER -p $DB_PORT -d optimsportbets-db
psql -U postgres -p 5432 -d optimsportbets-db
```

# 3. Install dependencies
```
# use python 3.10
python -m venv venv
source venv/bin/activate

echo "DB_PASSWORD=<your password>" > secrets.env
echo "THE_ODDS_API_KEY=<your api key>" >> secrets.env
# get environment variables (only available in the local terminal)
set -a
source .env
source secrets.env
set +a