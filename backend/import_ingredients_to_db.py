import psycopg2
import os

conn = psycopg2.connect(
    database=os.getenv('POSTGRES_DB', 'foodgram'),
    user=os.getenv('POSTGRES_USER', 'foodgram_user'),
    password=os.getenv('POSTGRES_PASSWORD', 'foodgram_password'),
    host=os.getenv('DB_HOST', ''),
    port=os.getenv('DB_PORT', 5432))

conn.autocommit = True
cursor = conn.cursor()

sql = '''COPY reviews_ingredient(name,measurement_unit)
FROM './app/data/ingredients.csv'
DELIMITER ','
CSV HEADER;'''

cursor.execute(sql)

conn.commit()
conn.close()
