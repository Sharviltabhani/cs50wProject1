import os, csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

os.environ['DATABASE_URL'] = 'postgres://ghpbuuqthyjnlq:b09cbc9f5ea657890f4dd7d80811a6803b9e9d0cd4a59a31bc0772240149bd32@ec2-54-246-85-151.eu-west-1.compute.amazonaws.com:5432/dfo7tn78867kis'


engine = create_engine(os.getenv("DATABASE_URL"))

db = scoped_session(sessionmaker(bind=engine))

#file = ("books.csv")
##reader = csv.reader(file)

#for isbn, title, author, year in reader:
#    db.execute("INSERT INTO book (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",{"isbn": isbn, "title": title, "author": author, "year":year})

#    print(f"Added book{title} to database.")
#    db.commit()

with open('books.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            print(f'\t{row[0]}  {row[1]}  {row[2]}  {row[3]} ')

            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",{"isbn": row[0], "title": row[1], "author": row[2], "year":row[3]})
            print(f"Added book{row[1]} to database.")
            db.commit()
            line_count += 1
    print(f'Processed {line_count} lines.')
