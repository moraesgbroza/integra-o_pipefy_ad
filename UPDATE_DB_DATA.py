import sqlite3
import json

def load_existing_data(cursor):
    cursor.execute("SELECT mail, telephone, cc, name, cc_name, fullcc FROM users")
    existing_data = {}  
    for row in cursor.fetchall():
        existing_data[row[0]] = {
            'telephone': row[1],
            'cc': row[2],
            'name': row[3],
            'cc_name': row[4],
            'fullcc' : row[5]
        }
    return existing_data

def update_or_insert_data(cursor, json_data, existing_data):
    for row in json_data:
        mail_value = row['mail']
        telephone_value = row['telefone']
        cc_value = row['cc']
        name_value = row['name']
        ccname_value = row['ccname']
        fullcc_value = row['fullcc']

        if mail_value in existing_data:
            # Update the record if there's any difference
            if (telephone_value != existing_data[mail_value]['telephone'] or
                cc_value != existing_data[mail_value]['cc'] or
                name_value != existing_data[mail_value]['name'] or
                ccname_value != existing_data[mail_value]['cc_name'] or
                fullcc_value != existing_data[mail_value]['fullcc']):
                sql_update = '''UPDATE users SET telephone = ?, cc = ?, name = ?, cc_name = ?, fullcc = ? WHERE mail = ?'''
                cursor.execute(sql_update, (telephone_value, cc_value, name_value, ccname_value, fullcc_value, mail_value))
        else:
            # Insert new record
            sql_insert = '''INSERT INTO users (mail, telephone, cc, name, cc_name, fullcc) VALUES (?, ?, ?, ?, ?, ?)'''
            cursor.execute(sql_insert, (mail_value, telephone_value, cc_value, name_value, ccname_value, fullcc_value))

def main():
    # Load JSON data
    with open('filtered_users.json', 'r') as f:
        json_data = json.load(f)

    # Specify the path to the SQLite database file
    db_path = r'D:\pipefy\pipefy_database'

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load existing data from the database
    existing_data = load_existing_data(cursor)

    # Update or insert data
    update_or_insert_data(cursor, json_data, existing_data)

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
