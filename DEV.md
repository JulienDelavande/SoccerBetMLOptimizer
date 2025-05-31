# Installation for local development

# 1. Clone the repository
```
git clone
cd SoccerBetMLOptimizer
```

# 2. Get the db
You will need psql (PostgreSQL client) and preferably pgAdmin to see the database (can manage as well but we use migrations with a custom script to apply changes).
```
kubectl port-forward -n optimsportbets pod/postgresql-global-0 5432:5432
cd db
pg_dump -h localhost -U kube -d optimsportbets-db -F c -b -v -f optimsportbets-db.dump

# if you already created the database skip next line
createdb -U postgres optimsportbets-db
pg_restore -h localhost -U postgres -d optimsportbets-db -v optimsportbets-db.dump

# to access the database with command line
psql -U postgres -d optimsportbets-db
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