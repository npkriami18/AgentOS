import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    user="postgres",
    password="postgres",
    dbname="myapp"
)

print("PostgreSQL connected!")

conn.close()