from flask import g
from werkzeug.security import generate_password_hash, check_password_hash

def do_query(query, params, commit=False):
    cursor = g.mysql.connection.cursor()
    cursor.execute(query, params)
    if commit:
        g.mysql.connection.commit()
    result = cursor.fetchall()
    insertObject = []
    try:
        columnNames = [column[0] for column in cursor.description]
        for record in result:
            insertObject.append( dict( zip( columnNames , record ) ) )
    except TypeError:
        return None
    finally:
        cursor.close()
    return insertObject

def user_exists(username):
    query = 'SELECT * FROM users WHERE username = %s'
    result = do_query(query, [username])
    if len(result) == 0:
        return False
    return True

def do_login(username, password):
    query = 'SELECT userid, password FROM users WHERE username = %s'
    result = do_query(query, [username])
    if len(result) != 1:
        return False

    password_hash = result[0]['password']
    if not check_password_hash(password_hash, password):
        return False
    return username, result[0]['userid']

def do_register(username, password):
    if user_exists(username):
        return [400,'username already registered']
    query = 'INSERT INTO users (username, password) VALUES (%s, %s)'
    password_hash = generate_password_hash(password)
    do_query(query, [username, password_hash], commit=True)
    return [201, "registered"]