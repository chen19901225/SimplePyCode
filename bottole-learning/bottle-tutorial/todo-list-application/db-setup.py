__author__ = 'Administrator'
import sqlite3

con=sqlite3.connect('todo.db')
con.execute('CREATE TABLE todo (id INTEGER primary  key,task char(100) not null, status bool not null )')
con.execute('INSERT INTO todo (task,status) VALUES("Read A-byte-of-python to get a good introduction ",0)')
con.execute('INSERT INTO todo (task,status) VALUES("Visit the Python websit ",1)')
con.execute('INSERT INTO todo(task,status) VALUES("Test various editors for and check the syntax",0)')
con.commit()