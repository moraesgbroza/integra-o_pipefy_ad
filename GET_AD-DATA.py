import sqlite3
import os
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import json
import re
import requests
from pyad import *
import unicodedata



def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

# ============================================================================================

server = Server('', get_info=ALL)
conn = Connection(server, user="", password="", auto_bind=True)
search_base = 'ou=LatAm,ou=user,ou=company,dc=sysmexamerica,dc=com'
search_base2 = 'ou=user,ou=company,dc=sysmexamerica,dc=com'
search_filter = '(objectClass=user)' 
search_attributes = ['canonicalName', 'sAMAccountName', 'distinguishedName', 'mail', 'cn', 'department', 'telephoneNumber', 'memberOf']  # Adjust attributes as needed
search_attributes_2 = ['mail', 'userAccountControl', 'cn']
search_filter2 = '(objectClass=*)'
search_base3 = 'ou=Term,ou=Disabled,dc=sysmexamerica,dc=com'

conn.search(search_base, search_filter, search_scope=SUBTREE, attributes=search_attributes)

specific_part = 'Disabled'

filtered_users = []

# ===================================================

for entry in conn.entries:
    canonical_name = entry.canonicalName.value if 'canonicalName' in entry else None
    if 'Review' not in canonical_name and 'Test' not in canonical_name and 'mail' in entry and entry.mail.value:
        if entry.department.value:
            department_numeric = re.sub(r'\D', '', entry.department.value)
            department_chars = re.sub(r'\d', '', entry.department.value)

        else:
            department_numeric = None
            department_chars = None
    is_disabled = 0
    if specific_part in canonical_name:
        is_disabled = 1
    is_latam_user = False
    is_topdesk_member = False
    if 'distinguishedName' in entry.entry_attributes_as_dict:
        for dn in entry.entry_attributes_as_dict['distinguishedName']:
            if 'OU=LatAm' in dn:
                is_latam_user = True
                break
    
    if 'memberOf' in entry.entry_attributes_as_dict:
        for group in entry.entry_attributes_as_dict['memberOf']:
            if 'SBR-TopDesk-Access' in group:  
                is_topdesk_member = True
                break
    
    if is_latam_user or is_topdesk_member:
        user_details = {
            'mail': entry.mail.value,
            'name': remove_accents(entry.cn.value),
            'cc': department_numeric,
            'telefone': entry.telephoneNumber.value,
            'ccname' : department_chars.rstrip(),
            'fullcc' : entry.department.value.rstrip(),
            'is_disabled' : is_disabled
        }
        filtered_users.append(user_details)
# =====================================================================================

conn.search(search_base2, search_filter, search_scope=SUBTREE, attributes=search_attributes)       
for entry in conn.entries:
    
    email_found = any(item["mail"] == entry.mail.value for item in filtered_users)
    
    canonical_name = entry.canonicalName.value if 'canonicalName' in entry else None
    if 'Review' not in canonical_name and 'Test' not in canonical_name and 'mail' in entry and entry.mail.value:
        if entry.department.value:
            department_numeric = re.sub(r'\D', '', entry.department.value)
            department_chars = re.sub(r'\d', '', entry.department.value)

        else:
            department_numeric = None
            department_chars = None

    is_disabled = 0
    if specific_part in canonical_name:
        is_disabled = 1
        
    is_latam_user = False
    is_topdesk_member = False
    if 'sAMAccountName' in entry.entry_attributes_as_dict:
        for account_name in entry.entry_attributes_as_dict['sAMAccountName']:
            if 'moraesg' in account_name:
                print('found it')

    if 'distinguishedName' in entry.entry_attributes_as_dict:
        for dn in entry.entry_attributes_as_dict['distinguishedName']:
            if 'OU=LatAm' in dn:
                is_latam_user = True
                break
    
    if 'memberOf' in entry.entry_attributes_as_dict:
        for group in entry.entry_attributes_as_dict['memberOf']:
            if 'SBR-TopDesk-Access' in group:  
                is_topdesk_member = True
                break
    
    if (is_latam_user or is_topdesk_member) and not email_found:
        user_details2 = {
            'mail': entry.mail.value,
            'name': remove_accents(entry.cn.value),
            'cc': department_numeric,
            'telefone': entry.telephoneNumber.value,
            'ccname' : department_chars.rstrip(),
            'fullcc' : entry.department.value.rstrip(),
            'is_disabled' : is_disabled
        }
        filtered_users.append(user_details2)    
    
        
conn.unbind()
with open('filtered_users.json', 'w') as json_file:
    json.dump(filtered_users, json_file, indent=4)

# ===================================================


server = Server('DC901.sysmexamerica.com', get_info=ALL)
conn = Connection(server, user="", password="", auto_bind=True)
user_details3 = []
cookie = None
try:
    while True:

        conn.search(search_base3, search_filter2, search_scope=SUBTREE, attributes=search_attributes_2, paged_size=1000, paged_cookie=cookie) 
        for entry in conn.entries:
            if entry.mail.value != None:
                mail = entry.mail.value
                user_details3.append(mail.lower())

        cookie = conn.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
        
        if not cookie:
            break  # No more pages to retrieve

except LDAPCursorError as e:
    print(f"ladp cursor error: {e}")

with open('disabled_users.json', 'w') as json_file:
    json.dump(user_details3, json_file, indent=4)

conn.unbind()
