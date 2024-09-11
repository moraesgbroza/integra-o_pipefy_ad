import sqlite3
import requests
import json
import re


# Check if email exists in the dictionary
def email_exists(data, target_email):
    for person, info in data.items():
        fields = info.get('node', {}).get('fields', [])
        for field in fields:
            if field['name'] == 'email' and field['value'] == target_email:
                return person
    return None

# SQLite database connection
def get_sqlite_users(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, mail, telephone, cc FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# Fetch users from Pipefy
def get_pipefy_users(pipefy_api_token):
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {pipefy_api_token}",
        "Content-Type": "application/json"
    }
    has_next_page = True
    after_cursor = None  # Start with None for the first request
    all_users = []
    
    while has_next_page:
        after_cursor_value = f'"{after_cursor}"' if after_cursor else "null"
        query = f"""
        {{
          cards(pipe_id: "", first: 50, after: {after_cursor_value}) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            edges {{
              node {{
                id
                title
                fields {{
                  name
                  value
                }}
              }}
            }}
          }}
        }}
        """
        response = requests.post(url, headers=headers, json={"query": query})
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'cards' in data['data'] and 'edges' in data['data']['cards']:
                users = data['data']['cards']['edges']
                all_users.extend(users)
                
                page_info = data['data']['cards']['pageInfo']##['edges']
                has_next_page = page_info['hasNextPage']
                after_cursor = page_info['endCursor'] if has_next_page else None
            else:
                print("Unexpected response structure:", data)  # Debugging: Print unexpected structure
                has_next_page = False
        else:
            raise Exception(f"Failed to fetch users from Pipefy: {response.status_code}, Response: {response.text}")
        
    users_dict = {user['node']['title']: user for user in all_users}
    with open('email_dont.json', 'w') as json_file:
        json.dump(users_dict, json_file, indent=4)
    return users_dict
# Compare users and update/create as needed
def sync_users(sqlite_users, pipefy_users, pipefy_api_token, json_data):
    pipefy_user_dict = pipefy_users

    for user in sqlite_users:
        name, email, phone, fullcc = user

        if phone == None:
          phone = ""
        record_fields = {}
        user_key = email_exists(pipefy_users, email)
        if user_key:
            pipefy_user = pipefy_user_dict[user_key]
            record_fields = {field['name']: field['value'] for field in pipefy_user['node']['fields']}
            cc_comparation = ""
            cc = None
            existe = False
            if record_fields.get("centro_de_custo") != None:
              # Extract the string from the list
              input_string = record_fields.get("centro_de_custo")
              cc_comparation = ''.join([char for char in input_string if char.isdigit()])
              
              for key, value in json_data.items():
                existe = False
                cc_1 = value["node"]["record_fields"]
                
                cc_test = cc_1[0]["value"]
                legacy_cc = cc_1[1]["value"]
                
                if cc_test == str(fullcc) + ".0" or legacy_cc == str(fullcc) + ".0":
                    existe = True
                    if cc_test == str(fullcc) + ".0":
                        cc = cc_test
                        cc_legacy = legacy_cc
                    else:
                        cc_legacy = legacy_cc
                        cc = cc_test
                    break
            elif record_fields.get("centro_de_custo") == None:
              cc_comparation = ""
              for key, value in json_data.items():
                existe = False
                cc_1 = value["node"]["record_fields"]
                
                cc_test = cc_1[0]["value"]
                legacy_cc = cc_1[1]["value"]
                
                if cc_test == str(fullcc) + ".0" or legacy_cc == str(fullcc) + ".0":
                    existe = True
                    if cc_test == str(fullcc) + ".0":
                        cc = cc_test
                        cc_legacy = legacy_cc
                    else:
                        cc_legacy = legacy_cc
                        cc = cc_test
                    break
              
            if email != record_fields.get("email") or name != record_fields.get("nome_completo") or (cc_comparation + ".0" != cc and cc_comparation + ".0" != cc_legacy):
                update_pipefy_user(pipefy_user['node']['id'], name, email, phone, fullcc, pipefy_api_token, json_data)
        elif email != None and '@sysmex' in email.lower():
            create_pipefy_user(name, email, phone, fullcc, pipefy_api_token, json_data)
            
            

def update_pipefy_user(user_id, name, email, phone, fullcc, pipefy_api_token, json_data):
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {pipefy_api_token}",
        "Content-Type": "application/json"
    }

    for key, value in json_data.items():
        existe = False
        cc_1 = value["node"]["record_fields"]
        
        cc = cc_1[0]["value"]
        legacy_cc = cc_1[1]["value"]
        
        if repr(cc) == repr(fullcc + ".0") or repr(legacy_cc) == repr(fullcc + ".0"):
            existe = True
            record_id = value["node"]["id"]
            break
    if existe == False:
      with open('email_dont.json', 'w') as json_file:
        json.dump(fullcc, json_file, indent=4)
      print("centro de custos não está no pipefy - update user ", email)
      return
    query2 = """

    mutation{
    
        updateFieldsValues(input:{
            nodeId:"USER_ID"
            values:[
                {fieldId: "email", value:"USER_EMAIL"},
                {fieldId: "nome_completo", value: "USER_NAME"},
                ]}) 
            {
            clientMutationId
            success
        }
      setTableRecordFieldValue(input: {
        table_record_id: "USER_ID"
        field_id: "centro_de_custo"
        value: "RECORD_ID"
      }) {
        clientMutationId
      }
    }
    
    """
    query1 = """

    """
    query = query2.replace("USER_ID", user_id or "").replace("USER_NAME", name or "").replace("USER_EMAIL", email or "").replace("USER_PHONE", phone or "").replace("USER_CC", cc or "").replace("RECORD_ID", record_id or "")
    
    response = requests.post(url, headers=headers, json={"query": query})
    print("response: ", response.json())
    if response.status_code != 200:
        raise Exception(f"Failed to update user in Pipefy: {response.status_code}")
    
def create_pipefy_user(name, email, phone, fullcc, pipefy_api_token, json_data):
    url = "https://api.pipefy.com/graphql"
    headers = {
        "Authorization": f"Bearer {pipefy_api_token}",
        "Content-Type": "application/json"
    }

    for key, value in json_data.items():
        existe = False
        cc_1 = value["node"]["record_fields"]
        
        cc = cc_1[0]["value"]
        legacy_cc = cc_1[1]["value"]
        if repr(cc) == repr(fullcc + ".0") or repr(legacy_cc) == repr(fullcc + ".0"):
            existe = True
            record_id = value["node"]["id"]
            break
        
    if existe == False:
      with open('email_dont.json', 'w') as json_file:
        json.dump(fullcc, json_file, indent=4)

        print("centro de custos não está no pipefy - create user ", email)
      return

    query = """
    mutation {
        createCard(
            input: {
            pipe_id: "",
            title: "USER_EMAIL",
            fields_attributes: [
                {field_id: "nome_completo", field_value: "USER_NAME"},
                {field_id: "email", field_value: "USER_EMAIL"},
                {field_id: "centro_de_custo", field_value: "RECORD_ID"}
            ],
            phase_id: ""
            }
        ) {
            card {
            id
            }
        }
        }
    """
    query = query.replace("USER_NAME", name or "")
    query = query.replace("USER_EMAIL", email or "")
    query = query.replace("USER_PHONE", phone or "")
    query = query.replace("USER_CC", fullcc or "")
    query = query.replace("RECORD_ID", record_id or "")
    response = requests.post(url, headers=headers, json={"query": query})
    print("response- create: ", response.json())

    if response.status_code != 200:
        raise Exception(f"Failed to create user in Pipefy: {response.status_code}")

with open('list_cc.json', 'r') as f:
    json_data = json.load(f)
db_path = r'D:\pipefy\pipefy_database'
pipefy_api_token = ''
pipefy_api_token1 = ''
sqlite_users = get_sqlite_users(db_path)
pipefy_users = get_pipefy_users(pipefy_api_token)

sync_users(sqlite_users, pipefy_users, pipefy_api_token, json_data)
