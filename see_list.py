import sqlite3
import requests
import json
pipefy_api_token = ''

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
          table_records(table_id: "", first: 50, after: {after_cursor_value}) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            edges {{
              node {{
                id
                title
                record_fields {{
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
            
            if 'data' in data and 'table_records' in data['data'] and 'edges' in data['data']['table_records']:
                users = data['data']['table_records']['edges']
                all_users.extend(users)
                
                page_info = data['data']['table_records']['pageInfo']
                has_next_page = page_info['hasNextPage']
                after_cursor = page_info['endCursor'] if has_next_page else None
            else:
                print("Unexpected response structure:", data)  # Debugging: Print unexpected structure
                has_next_page = False
        else:
            raise Exception(f"Failed to fetch users from Pipefy: {response.status_code}, Response: {response.text}")
    
    
    cc_dict = {user['node']['title']: user for user in all_users}
    return cc_dict

pipefy_api_token = ''
dict = get_pipefy_users(pipefy_api_token)
for key, value in dict.items():
    print(key)
    print(value["node"]["id"])
