#
# Audit tool functions module
#

from collections import OrderedDict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import glob
import grp
import json
from pg import DB
import os
import sys
import argparse
import collections
import csv
import ldap
import ldif
import logging
from pprint import pprint
import pwd
import requests
import requests_kerberos
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import socket
import subprocess
import time
import xml.etree.ElementTree as ET

# disable requests http cert warning here, verified with Dan Markle (only used internally)
# Requests doesn't use the pem bundle right, and the warning just dirties the output 
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

divider = str('-' * 110 + "\n")
subdivider = str('-' * 55 + "\n")

#
# Global vars
#

def audit_ambari_users(ad_ldap_groupmap, ambari_uri,
					   ambari_port, ambari_username, ambari_password,
					   user_master_dict):
	"""Audits returned list of Ambari users"""

	# Note this requires the requesting user:
	#	1. Is a Ambari user
	#	2. Has Ambari admin rights (to get all response content)
	#	3. Not using a version of python-requests too high
	#	   See: https://github.com/kennethreitz/requests/issues/3608

	# Initiate vars
	invalid_users = []
	valid_users = []
	connection_tries = 1
	max_attempts = 3

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ambari_uri + ":" + ambari_port + "/api/v1/users"
		logging.info("Making API connection to: " + url)
		logging.info("Making request for Ambari user listing...")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ambari_username, ambari_password), verify=False )
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			userlist = []
			# Load JSON data into a dict object
			json_data = json.loads(r.text)
			# Interate through list
			list_count = len(json_data["items"])
			for index in range(list_count):
				# Add user to map
				# return values are already sorted by user
				user = json_data["items"][index]["Users"]["user_name"]

				# Make a seperate request for the group details.
				# Anything that is NOT LDAP 'true', should have it's members reported
				audit_ambari_user\
					(ambari_uri, ambari_port, \
					ambari_username, ambari_password, user)

				# Check here against AD/LDAP usermap
				# ensure the group mape is fully parsable, dict types are not meant to be searchable
				if user in str(ad_ldap_groupmap):
					logging.info("Ambari audit: '" + user + "'" + " exists in AD/LDAP usermap")
					user_master_dict[user] = user
					valid_users.append(user)
				elif user not in (str(ad_ldap_groupmap) or sysaccounts):
					logging.info("Ambari audit '" + user + "'" + " does not exist in AD/LDAP usermap")
					# Add user to invalid list list if they do not exist on the OS level
					# Can't rely only on built ad/ldap group map, as users
					# can exist invidually in Ambari User + Group Management
					valid_os_user = validate_os_user(user)
					if not valid_os_user:
						invalid_users.append(user)

			break
							
		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			elif r.reason == "Connection Aborted":
				logging.error("Connection error")
				sys.exit(1)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				sys.exit(1)
			
	# Kill function if we hit or exceeded max attempts
	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ambari user audit failed due to: " + r.reason)
		sys.exit(1)


	return user_master_dict, invalid_users, valid_users

def audit_ambari_groups(ad_ldap_groupmap, ambari_uri,
						ambari_port, ambari_username, ambari_password,
						group_master_dict, user_master_dict):
	"""Audits returned list of Ambari groups"""

	# Note this requires the requesting user:
	#	1. Is a Ambari user
	#	2. Has Ambari admin rights (to get all response content)
	#	3. Not using a version of python-requests too high
	#	   See: https://github.com/kennethreitz/requests/issues/3608

	# Initiate vars
	invalid_users = []
	valid_users = []
	connection_tries = 1
	max_attempts = 3

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ambari_uri + ":" + ambari_port + "/api/v1/groups"
		logging.info("Making API connection to: " + url)
		logging.info("Making request for information...")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ambari_username, ambari_password), verify=False )
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			grouplist = []
			# Load JSON data into a dict object
			json_data = json.loads(r.text)
			# Interate through list
			list_count = len(json_data["items"])
			for index in range(list_count):
				# Add user to map
				# return values are already sorted by user
				group = json_data["items"][index]["Groups"]["group_name"]
				group_master_dict[group] = group

				# Make a seperate request for the group details.
				# Anything that is NOT LDAP 'true', should have it's members reported
				userlist, grouptype = get_ambari_group_info\
					(ambari_uri, ambari_port, \
					ambari_username, ambari_password, group)

				# Loop back over the returned users from groups to ensure we get all members for user in userlist:
				# Check here against AD/LDAP usermap
				# ensure the group mape is fully parsable, dict types are not meant to be searchable
				logging.info("\n\n====== Validating all Ambari users against groupmap ======")
				for user in userlist:
					if user in str(ad_ldap_groupmap):
						logging.info("Ambari audit: '" + user + "'" + " exists in AD/LDAP usermap")
						user_master_dict[user] = user
						valid_users.append(user)
					elif user not in (str(ad_ldap_groupmap) or sysaccounts):
						logging.info("Ambari audit '" + user + "'" + " does not exist in AD/LDAP usermap")
						# Add user to invalid list list if they do not exist in LDAP
						# Can't rely only on built ad/ldap group map, as users
						# can exist invidually in Ambari User + Group Management
						valid_os_user = validate_os_user(user)
						if not valid_os_user:
							invalid_users.append(user)

			break
							
		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			elif r.reason == "Connection Aborted":
				logging.error("Connection error")
				sys.exit(1)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				sys.exit(1)

	# Kill function if we hit or exceeded max attempts
	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ambari user audit failed due to: " + r.reason)
		sys.exit(1)

	return user_master_dict, group_master_dict

def audit_apache_groups(user_master_dict, group_master_dict):
	"""Audit apache users and groups from list of groups"""

	apache_group_map = {}

	# pull the current apache config from git and check against ad and LDAP usermap
	# TODO	
	logging.info("Apache audit function currently unused")

def audit_hdfs_user(user):
	"""Scans HDFS for singular user, returns UID/GID"""

	# Directory Status
	hdfsstatus = subprocess.call(['hadoop','fs','-ls','/user/' + user], stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
	if hdfsstatus is 0:
		print "HDFS Directory Status: OK"
	else:
		print "HDFS Directory Status: NOT OK"

	# Quota
	current_user_quota, current_user_quota_gb, hdfs_folder_size, \
		hdfs_folder_size_gb = check_user_hdfs_quota(user)	
	print "Current Quota (Bytes): " + str(current_user_quota)
	print "Current Quota (GB): " + str(current_user_quota_gb)
	print "Folder size (Bytes): " + str(hdfs_folder_size)
	print "Folder size (GB): " + str(hdfs_folder_size_gb)

def audit_hdfs_users(user_master_dict, ad_ldap_groupmap, sysaccounts):
	"""Scans HDFS for all users, returns UID/GID"""

	# initialize vars
	valid_users = []
	invalid_users = []
	skiplist = ['None']

	# List users
	# use dictionary to be able to retrieve values from key
	# Return format: permissions number_of_replicas userid groupid filesize 
	#				 modification_date modification_time filename
	hdfs_users_raw = subprocess.Popen(['sudo', '-n', '-u', 'hdfs', 'hadoop', 'fs', '-ls', '/user'], stdout=subprocess.PIPE)
	stdout, stderr = hdfs_users_raw.communicate()

	reader = csv.DictReader(stdout.decode('ascii').splitlines(),
							delimiter=' ', skipinitialspace=True,
							fieldnames=['permissions', 'replicas',
										'userid', 'groupid', 'filesize',
										'moddate', 'modtime', 'filename'])

	# process each user from build dictionary
	for row in reader:
		try:
			user = str(row['filename']).replace('/user/','')
			valid_users.append(user)
			if user not in skiplist:
				logging.info("Processing user: '" + user + "'")
				if user in ad_ldap_groupmap:
					logging.info("HDFS user: '" + user + "' exists in AD/LDAP " +
					"groupmap")
				elif user not in (ad_ldap_groupmap or sysaccounts):
					logging.info("HDFS user: '" + user + "' does not exist in " +
					"AD/LDAP groupmap")
					# Add user to invalid list list if they do not exist in LDAP
					# Can't rely only on built ad/ldap group map
					valid_os_user = validate_os_user(user)
					if not valid_os_user and user not in sysaccounts:
						invalid_users.append(user)

				# Add user into master dict
				user_master_dict[user] = user
						
		except TypeError:
			logging.info("Cannot process user: '" + str(hdfs_user) + "'")	

	# return just the list of users
	return valid_users, invalid_users

def audit_hdfs_groups(group_master_dict, ad_ldap_groupmap, sysaccounts):
	"""Scans HDFS for all groups, returns UID/GID"""

	valid_groups = []
	invalid_groups = []

	# List groups
	# use dictionary to be able to retrieve values from key
	# Return format: permissions number_of_replicas userid groupid filesize 
	#				 modification_date modification_time filename
	hdfs_groups_raw = subprocess.Popen(['sudo', '-n', '-u', 'hdfs', 'hadoop', 'fs', '-ls', '/group'], stdout=subprocess.PIPE)
	stdout, stderr = hdfs_groups_raw.communicate()

	reader = csv.DictReader(stdout.decode('ascii').splitlines(),
							delimiter=' ', skipinitialspace=True,
							fieldnames=['permissions', 'replicas',
										'userid', 'groupid', 'filesize',
										'moddate', 'modtime', 'filename'])

	# process each group from built dictionary
	for row in reader:
		try:
			group = str(row['filename']).replace('/group/','')
			# Use string conversion if None keyword is hit
			logging.info("Pressing group: '" + group + "'")
			# report this for now, but HDFS group names are almost always 
			# Than AD/LDAP group names
			if group in ad_ldap_groupmap:
				logging.info("HDFS group: '" + group + "' exists in AD/LDAP usermap")
				# If user valid in AD or LDAP and not in dict, add them
				if group not in group_master_dict:
					group_master_dict[group] = group
			else:
				logging.info("HDFS group: '" + group + "' does not exist in AD/LDAP usermap")
				# Add user to invalid list list if they do not exist in LDAP
				# Can't rely only on built ad/ldap group map, as users
				# can exist invidually in Ambari User + Group Management
				valid_os_group = validate_os_group(group)
				if not valid_os_group and group not in sysaccounts:
					invalid_groups.append(group)

		except TypeError:
			logging.info("Cannot process group: '" + group + "'")	

	# return just the list of groups
	return valid_groups, invalid_groups

def audit_ranger_user(ranger_password, ranger_port, ranger_uri, \
					  ranger_username, user):
	"""Retrieves deetails from Ranger API for a user"""

	# initalize vars
	connection_tries = 1
	max_attempts = 3
	create_date = "None"
	description = "None"
	group_list = "None"
	ranger_id = "None"
	ranger_user = "None"
	source = "None"
	updated_by = "None"
	user_enabled = "None"
	user_role = "None"

	logging.info("\n\n== Processing Ranger user '" + user + "' ==")

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ranger_uri + ":" + ranger_port + "/service/xusers/users/userName/" + user
		logging.info("Making API connection to: " + url)
		logging.info("Making request for Ranger user listing...")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ranger_username,ranger_password), verify=False)
		#print r.text
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			user_attribs = []
			# Get the xml root data
			xmlroot = ET.fromstring(r.text)

			#for element in xmlroot.iter('*'):
			#	print element	

			# Iterate the tag we want
			# TODO - see if there is a way you don't have to iterate
			# twice to get the text values
			for item in xmlroot.iter('vxUser'):
				for name in item.iter('name'):
					ranger_user = name.text
				for user_id in item.iter('id'):
					ranger_id = user_id.text
				for description in item.iter('description'):
					description = description.text
				for updatedBy in item.iter('updatedBy'):
					updated_by = str(updatedBy.text.split(' ')[0])
				for userSource in item.iter('userSource'):
					source = userSource.text
				for createDate in item.iter('createDate'):
					create_date = createDate.text
				for userRoleList in item.iter('userRoleList'):
					user_role = userRoleList.text
				for isVisible in item.iter('isVisible'):
					user_enabled = isVisible.text

				# DEBUG
				'''
				keyword = "rg"
				if keyword in str(ranger_user):
					print "Ranger User: '" + ranger_user + "'"
					print "User we gave: '" + user + "'"
				'''

				# Check for a local account
				if source != '1':
					logging.warning("This is not a user account, but a local account")

				# Set some more "human readable" text
				# Role
				if user_role == "ROLE_USER":
					user_role = "User"
				elif user_role == "ROLE_SYS_ADMIN":
					user_role = "Admin"
				# ID enabled
				if user_enabled == "1":
					user_enabled = "True"
				else:
					user_enabled = "False"

				logging.info("\n\n=== '" + user + "' attributes ===")
				logging.info('source: ' + source)
				logging.info('updated_by: ' + updated_by)
				logging.info('ranger_id: ' + ranger_id)
				logging.info('ranger_user: ' + ranger_user)
				logging.info('description: ' + description)
				logging.info('user_role: ' + user_role)
				logging.info('create_date: ' + create_date)
				logging.info('user_enabled: ' + user_enabled)

			# break loop
			break

		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason == "Bad Request":
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				ranger_id = "None"
				# Return out of function now, as there is no reason to make an API call
				# to find a non-existant user's groups
				return create_date, description, group_list, ranger_id, \
					   ranger_user, source, updated_by, user_enabled, user_role
			else:
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			if connection_tries >= max_attempts:
				logging.error("Connection tries exhausted, failing.")
				logging.error("Ambari user audit failed due to: " + r.reason)
				break

	# Reset connection try for new request
	connection_tries = 1
	max_attempts = 3

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ranger_uri + ":" + ranger_port + "/service/xusers/" + ranger_id + "/groups"
		logging.info("Making API connection to: " + url)
		logging.info("Making request for Ranger user listing...")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ranger_username,ranger_password), verify=False)
		#print r.text
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			group_list = []
			# Get the xml root data
			xmlroot = ET.fromstring(r.text)
			for resultSize in xmlroot.iter('resultSize'):
				logging.info("Got " + resultSize.text + " results, processing...")

			# DEBUG
			#for element in xmlroot.iter('*'):
			#	print element	

			# Iterate the tag we want
			for item in xmlroot.iter('vXGroups'):
				this_group=''
				for group_name in item.iter('name'):
					this_group = group_name.text

				# Build a list
				group_list.append(this_group)

			# log
			logging.info("group_list: " + ', '.join(group_list))

			# Break loop
			break

		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			elif r.reason == "Connection Aborted":
				logging.error("Connection error")
				sys.exit(1)
			else:
				logging.warning("Cannot fetch Ranger groups for '" + user + "' (Reason: not found)")
				break

	# Kill function if we hit or exceeded max attempts
	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ambari user audit failed due to: " + r.reason)
		sys.exit(1)
	
	return create_date, description, group_list, ranger_id, \
		   ranger_user, source, updated_by, user_enabled, user_role
	
def audit_ranger_users(ad_ldap_groupmap, adgroupmap,  
						group_master_dict, ranger_uri,
						ranger_password, ranger_port, ranger_username,
						sysaccounts, user_master_dict):
	"""Takes the user provided by a particular function and audits them"""
	"""Based on: hadoop-scripting/ranger/delete-remote-users.py"""

	# Initiate vars
	invalid_users = []
	valid_users = []
	connection_tries = 1
	max_attempts = 3

	# skip known sysem users who will not have ldap/ad accounts
	disabled_ad_ldap_ids = []
	# Some "users" pulled down are actually groups
	users_actually_groups = ['cdisadmin']
	skiplist = ['null']

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ranger_uri + ":" + ranger_port + "/service/xusers/users"
		logging.info("Making API connection to: " + url)
		logging.info("Making request for Ranger user listing...")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ranger_username,ranger_password), verify=False)
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			userlist = []
			xmluserlist = ET.fromstring(r.text)
			for resultSize in xmluserlist.iter('resultSize'):
				logging.info("Got " + resultSize.text + " results, processing...")
			for vXUsers in xmluserlist.iter('vXUsers'):
				this_id = ''
				for user_id in vXUsers.iter('id'):
					this_id = user_id.text
				this_name = ''
				for name in vXUsers.iter('name'): 
					this_name = name.text
				this_source = ''
				for userSource in vXUsers.iter('userSource'):
					this_source = userSource.text
				userlist.append({'id': this_id, 'name': this_name, 'source': this_source})
			# Sort the list of dictionaries with lambda
			userlist.sort(key=lambda x:x['name'])
			for x in userlist:
				# Get Ranger username
				for item in x.iteritems():
					username = x['name']
					source = x['source']
				if source != '1':
					logging.info("Ranger Audit: Skipping local user " + username)
				elif username in skiplist:
					logging.info("Ignoring user in skip list: '" + username + "'")
				else:
					# Get details via audit_ranger_user()
					try:
						create_date, description, group_list, ranger_id, \
							ranger_user, source, updated_by, user_enabled, user_role = \
							audit_ranger_user(ranger_password, ranger_port, \
							ranger_uri, ranger_username, username)
					except:
						logging.error("Could not retrieve details for '" + username + "'")

					# Check here against AD/LDAP usermap
					# ensure the group mape is fully parsable, dict types are not meant to be searchable
					if username in str(ad_ldap_groupmap):
						logging.info("Ranger Audit: '" + username + "'" + " exists in AD/LDAP usermap")
						user_master_dict[username] = username
						valid_users.append(username)
					elif (username not in str(ad_ldap_groupmap)) and (username not in sysaccounts):
						logging.info("Ranger Audit '" + username + "'" + " does not exist in AD/LDAP groupmap")
						# Add user to list if not in groupmap
						invalid_users.append(username)

			break
							
		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			elif r.reason == "Connection Aborted":
				logging.error("Connection error")
				sys.exit(1)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				sys.exit(1)

	# Kill function if we hit or exceeded max attempts
	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ambari user audit failed due to: " + r.reason)
		sys.exit(1)

	return user_master_dict, group_master_dict, invalid_users, valid_users

def audit_ranger_groups(ad_ldap_groupmap, adgroupmap, group_master_dict, 
						ranger_uri, ranger_password, ranger_port, 
						ranger_username, sysaccounts, user_master_dict):
	"""Audits the list of ranger users"""
	"""Based on: hadoop-scripting/ranger/delete-internal-groups.py"""

	# Initialize vars
	connection_tries = 1
	max_attempts = 3

	# Make API call
	url = ranger_uri + ":" + ranger_port + "/service/xusers/groups"
	r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ranger_username, ranger_password), verify=False )

	# Process valid response
	if r.status_code == 200:
		attrib_list = []
		xmlroot = ET.fromstring(r.text)

		# --------- DEBUG ---------#
		for element in xmlroot.iter('*'):
			logging.debug(element)
		#sys.exit("Review XML response")
		# --------- DEBUG ---------#

		for resultSize in xmlroot.iter('resultSize'):
			logging.info("Got " + resultSize.text + " results, processing...")
		for vXGroups in xmlroot.iter('vXGroups'):
			this_id = ''
			for group_id in vXGroups.iter('id'):
				this_id = group_id.text
			this_enabled=' '
			for isVisible in vXGroups.iter('isVisible'):
				this_enabled = isVisible.text
			this_name = ''
			for name in vXGroups.iter('name'):
				this_name = name.text
			this_source = ''
			for groupSource in vXGroups.iter('groupSource'):
				this_source = groupSource.text
			this_created_on=' '
			for createDate in vXGroups.iter('createDate'):
				this_create_date = createDate.text

			# Human reabled text assignments
			if this_enabled == "1":
				this_enabled = "True"
			elif this_enabled == "2":
				this_enabled = "False"

			# Add set to list/dict objects
			object_instance = {'group_id': this_id\
							  ,'group_name': this_name\
							  ,'group_enabled': this_enabled\
							  ,'group_source': this_source\
							  ,'create_date': this_create_date}
			# build list and log
			attrib_list.append(object_instance)
			logging.debug(object_instance)
						
		# Sort the list of dictionaries with lambda
		attrib_list.sort(key=lambda x:x['group_name'])
		for x in attrib_list:
			if x['group_source'] != '1' and x['group_source'] != '':
				if x['group_source'] == '':
					# There are no source numbers in the group lists right now, so check blank IDs by default
					logging.info("Ranger Audit: This group has no source ID.") 
					logging.info("Ranger Audit: Skipping local group " + x['group_name'])
			else:
				logging.info("\n\n==Processing Ranger Group '" + x['group_name'] + "'==")
				group_id = x['group_id']
				group_name = x['group_name']
				group_source = x['group_source']
				create_date = x['create_date']
				group_enabled = x['group_enabled']
				# Log
				logging.info("Group ID: " + group_id)
				logging.info("Group name: " + group_name)
				logging.info("Group source: " + group_source)
				logging.info("Group creation date: " + create_date)
				logging.info("Group status: " + group_enabled)
				# Check here against AD/LDAP usermap
				# ensure the group map is fully parsable, dict types are not meant to be searchable
				if group_name in str(ad_ldap_groupmap):
					logging.info("Ranger Audit: '" + group_name + "'" + " exists in AD/LDAP usermap")
					group_master_dict[group_name] = group_name
				elif group_name not in (str(ad_ldap_groupmap) or sysaccounts):
					logging.info("Ranger Audit: '" + group_name + "'" + " does not exist in AD/LDAP usermap")
					# Add group to list if not in groupmap
					group_master_dict[group_name] = group_name

	else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			elif r.reason == "Connection Aborted":
				logging.error("Connection error")
				sys.exit(1)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				sys.exit(1)

	# Kill function if we hit or exceeded max attempts
	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ambari user audit failed due to: " + r.reason)
		sys.exit(1)

	return user_master_dict, group_master_dict	

def check_user_hdfs_quota(user):

	# Log current user quota (outputs in Bytes)
	# Format: QUOTA, REMAINING_QUOTA, SPACE_QUOTA, REMAINING_SPACE_QUOTA, DIR_COUNT, FILE_COUNT, CONTENT_SIZE, PATHNAME
	quota_fetch = subprocess.Popen(['sudo', '-n', '-u', 'hdfs', 'hadoop', 'fs', '-count', '-q', '/user/' + user], stdout=subprocess.PIPE, stderr=open('/dev/null', 'w'))
	stdout, stderr = quota_fetch.communicate()
	current_user_quota_raw = stdout.split()
	# If a quota is not set, this will fail out, report as such
	try:
		current_user_quota =  int(current_user_quota_raw[2])
		current_user_quota_gb = round((float(current_user_quota) / 1073741824), 2)
	except (IndexError, ValueError):
		logging.info("No quota is currently set for '" + user + "'")
		current_user_quota = None
		current_user_quota_gb = None

	#Folder size 
	try:
		hdfs_folder_size =	int(current_user_quota_raw[6])
		hdfs_folder_size_gb = round((float(hdfs_folder_size) / 1073741824), 2)
	except:
		raise

	return current_user_quota, current_user_quota_gb, hdfs_folder_size, hdfs_folder_size_gb

def get_ambari_group_info(ambari_uri, ambari_port, ambari_username, \
						  ambari_password, group):
	"""Audits given group info using API request to Ambari"""

	# Note this requires the requesting user:
	#	1. Is a Ambari user
	#	2. Has Ambari admin rights (to get all response content)
	#	3. Not using a version of python-requests too high
	#	   See: https://github.com/kennethreitz/requests/issues/3608

	# Initialize vars
	connection_tries = 1
	max_attempts = 3

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ambari_uri + ":" + ambari_port + "/api/v1/groups/" + group
		logging.info("Making API connection to: " + url)
		logging.info("Making request for information on group: '" + group + "'")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ambari_username, ambari_password), verify=False )
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			userlist = []
			# Load JSON data into a dict object
			json_data = json.loads(r.text)
			# DEBUG - get json back out of dict created above for use in vim
			#print json.dumps(json_data)
			#print "========= data test ========= "
			group_name = json_data["Groups"]["group_name"]
			ldap_group = json_data["Groups"]["ldap_group"]
			# Interate through member list
			list_count = len(json_data["members"])
			if ldap_group:
				grouptype = "ldap"
			else:
				grouptype = "local"
	
			# There is nothing of large value in the ambari.group postgres
			# table (e.g. creation date )
			logging.info("\n\n====== Processing " + grouptype + " group: " + group + " ======")
			for index in range(list_count):
				user = json_data["members"][index]["MemberInfo"]["user_name"]
				logging.info("Processing user: '" + user + "'")
				userlist.append(user)

			break

		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			elif r.reason == "Connection Aborted":
				logging.error("Connection error")
				sys.exit(1)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				sys.exit(1)

	# Kill function if we hit or exceeded max attempts
	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ambari user audit failed due to: " + r.reason)
		sys.exit(1)


	if r.reason == "Connection Aborted":
		logging.error("Connection error")

	return userlist, grouptype

def audit_ambari_user(ambari_uri, ambari_port, ambari_username, \
						 ambari_password, user):
	"""Audits given user info using API request to Ambari"""

	# Note this requires the requesting user:
	#	1. Is a Ambari user
	#	2. Has Ambari admin rights (to get all response content)
	#	3. Not using a version of python-requests too high
	#	   See: https://github.com/kennethreitz/requests/issues/3608

	# Initialize vars
	connection_tries = 1
	max_attempts = 3
	ambari_user_attribs = {}
	ambari_user = "None"
	user_type = "None"
	openldap_user = "None"
	active_account = "None"
	groups = "None"

	logging.info("\n\n==Processing Ambari user '" + user + "'===")

	# There are times when the dev team is hammering postgres, so allow retries
	start = time.time()
	while connection_tries <= max_attempts:
		url = ambari_uri + ":" + ambari_port + "/api/v1/users/" + user
		logging.info("Making API connection to: " + url)
		logging.info("Making request for '" + user + "' details...")
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ambari_username, ambari_password), verify=False )
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			userlist = []
			# Load JSON data into a dict object
			logging.debug(r.text)
			json_data = json.loads(r.text)
			# -------------- DEBUG -------------- # 
			'''
			# Write to file for review
			# in vim: '%!python -m json.tool'
			file = '/home/cdis_sys_prod/result.json'
			with open('/home/cdis_sys_prod/result.json', 'w') as fp:
				json.dump(json_data, fp)
			sys.exit("Review json file: " + str(file))

			# Show all values
			for key, value in json_data['Users'].iteritems():
			for key, value in json_data.iteritems():
				logging.info(str(key) + ": " + str(value))
			'''
			# -------------- DEBUG -------------- # 

			ambari_user =	str(json_data['Users']['user_name'])
			user_type = str(json_data['Users']['user_type'])
			openldap_user = str(json_data['Users']['ldap_user'])
			active_account = str(json_data['Users']['active'])
			groups = ', '.join(json_data['Users']['groups'])

			logging.info("username: " + ambari_user)
			logging.info("user_type: " + user_type)
			logging.info("openldap_user: " + openldap_user)
			logging.info("active account: " + active_account)
			logging.info("groups: " + groups)

			break
							
		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				break
			if connection_tries >= max_attempts:
				logging.error("Connection tries exhausted, failing.")
				logging.error("Ambari user audit (details) failed due to: " + r.reason)
				sys.exit(1)

	if r.reason == "Connection Aborted":
		logging.warning("Connection error")
			
	return ambari_user, user_type, openldap_user, active_account, groups
	
def get_ranger_dbaccess(ranger_uri, ranger_password, ranger_port,
					  ranger_username, search_type, search_string):
	"""Searches policies for user or group"""
	"""See: https://cwiki.apache.org/confluence/display/RANGER/REST+APIs+for+Policy+Management """

	# Initialize vars
	connection_tries = 1
	max_attempts = 3
	database_name = ""

	if search_type == "groupName":
		search_obj = "groupList"
	if search_type == "userName":
		search_obj = "userList"

	# set vars up dynamically to reuse code
	hive_policies = {}
	hdfs_policies = {}
	hive_objects = {}
	hdfs_objects = {}

	# Some "users" pulled down are actually groups
	users_actually_groups = ['cdisadmin']
	skiplist = ['null']

	# Make API call
	start = time.time()
	while connection_tries <= max_attempts:
		logging.info("Connection try: " + str(connection_tries) + " of " + str(max_attempts))
		url = ranger_uri + ":" + ranger_port + "/service/public/api/policy?" + search_type + \
		'=' + search_string
		logging.info("Making API connection to: " + url)
		logging.info("Making request for Ranger policies on search string: " + search_string)
		logging.info("Making request for Ranger policies on steach type: " + search_type)
		r = requests.get(url, auth=requests.auth.HTTPBasicAuth(ranger_username,ranger_password), verify=False)
		# Note if request time was abnormally long (ultimate timeout seems to be 60 seconds)
		now = time.time()
		if int(now - start) > 10:
			logging.warning("Ranger API request took longer than usual: " + str(int(now - start)) + " seconds")
		if r.status_code == 200:
			logging.info("Request accepted")
			# Load JSON data into a dict object
			json_data = json.loads(r.text)
			policy_count = len(json_data["vXPolicies"])
			logging.info("Retrieved " + str(policy_count) + " policies")
			for index in range(policy_count):
				# Set top level objects
				policy_id = json_data["vXPolicies"][index]["id"]
				policy_type = json_data["vXPolicies"][index]["repositoryType"]
				policy_name = json_data["vXPolicies"][index]["policyName"]
				is_enabled = json_data["vXPolicies"][index]["isEnabled"]

				# Get hive policy items
				if policy_type == "hive":
					grouplist = []
					userlist = []
					# Default polcies do not have some columns, try/except them
					try:
						column_type = json_data["vXPolicies"][index]["columnType"]
					except KeyError:
						column_type = "No entry"
					try:
						columns = json_data["vXPolicies"][index]["columns"]
					except KeyError:
						column_type = "No entry"
					database_name = json_data["vXPolicies"][index]["databases"]
					database_string = ''.join(database_name)
					database_desc = json_data["vXPolicies"][index]["description"]
					is_audited = json_data["vXPolicies"][index]["isAuditEnabled"]
					is_recursive = json_data["vXPolicies"][index]["isEnabled"]
					# get length of perm list
					permmap_count = len(json_data["vXPolicies"][index]["permMapList"])
					logging.debug("Number of permission sets: " + str(permmap_count))
					for permindex in range(permmap_count):
						logging.debug("Checking index: " + str(permindex))
						# Get perm list for our search only
						perm_obj = json_data["vXPolicies"][index]["permMapList"][permindex][search_obj]
						if perm_obj:
							perm_set = json_data["vXPolicies"][index]["permMapList"][permindex]["permList"][:]
							# Nab just what we want for simple returns based on searches
							if search_string in str(perm_set):
								perm_string = str(perm_set)
								hive_policies[database_name] = perm_set

						# Save more details to full object dict so they can be used elsewhere
						# Convert unicde where necessary
						groups = json_data["vXPolicies"][index]["permMapList"][permindex]["groupList"]
						users = json_data["vXPolicies"][index]["permMapList"][permindex]["userList"]
						perm_set_all = json_data["vXPolicies"][index]["permMapList"][permindex]["permList"][:]
						perm_set_all = ','.join(perm_set_all).encode('ascii','replace')
						if groups:
							for thisgroup in groups:
								logging.debug("Got this group: " + str(thisgroup))
								thisgroup = thisgroup.encode('ascii','replace')
								grouplist.append(thisgroup + ": " + perm_set_all)
						if users:
							for thisuser in users:
								logging.debug("Got this user: " + str(thisuser))
								thisuser = thisuser.encode('ascii','replace')
								userlist.append(thisuser + ": " + perm_set_all)

					# build the complete object for use in other scripts
					hive_objects[database_string] = \
						{'policy_name': policy_name,
						'policy_type': policy_type,
						'database_name': database_name,
						'column_type': column_type,
						'columns': columns,
						'database_name': database_name,
						'database_desc': database_desc,
						'policy_id': policy_id,
						'is_enabled': is_enabled,
						'is_recursive': is_recursive,
						'users': userlist,
						'groups': grouplist}
													
					logging.debug("\n\n=== DEBUG: Showing details and raw object ===")
					for primarykey, values in hive_objects.iteritems():
						for subkey, value in values.iteritems():
							logging.debug(str(subkey) + ": " + str(value))
					logging.debug(json_data["vXPolicies"][index])

					sys.exit("pause")

				# Get hdfs policy items
				if policy_type == "hdfs":
					hdfs_path = json_data["vXPolicies"][index]["resourceName"]
					# get length of perm list
					permmap_count = len(json_data["vXPolicies"][index]["permMapList"])
					for permindex in range(permmap_count):
						# get obj list
						perm_list = json_data["vXPolicies"][index]["permMapList"][permindex][search_obj]
						if perm_list:
							perm_obj = json_data["vXPolicies"][index]["permMapList"][permindex]["permList"][:]
							perm_string = str(perm_obj)
							if search_string in str(perm_list):
								perm_sting = str(perm_list)
								hdfs_path = str(hdfs_path)
								# Nab just what we want for simple returns based on searches
								hdfs_policies[hdfs_path] = perm_obj

								# can't use slashes in key, convert
								hdfs_objects[hdfs_path] = []
								hdfs_objects[hdfs_path].append(hdfs_path)
								hdfs_objects[hdfs_path].append(perm_obj)

			# DEBUG Write to file for analysis
			'''
			filename = str(os.environ['HOME'] + '/result.json')
			with open(filename, 'w') as fp:
				json.dump(json_data, fp)
			logging.info("Wrote JSON to file: " + filename)
			'''
			break
							
		else:

			logging.debug("Request reason: " + r.reason)
			if r.reason != "Not Found":
				logging.warning("Issue establishing connection")
				connection_tries += 1
				logging.warning("Attempting another connection in 10 seconds")
				time.sleep(10)
			else:
				logging.warning("Cannot fetch account details for '" + user + "' (Reason: not found)")
				sys.exit(1)

	if connection_tries >= max_attempts:
		logging.error("Connection tries exhausted, failing.")
		logging.error("Ranger policy audit failed due to: " + r.reason)
		sys.exit(1)

	if r.reason == "Not Found":
		logging.error("Please check the initiating user is valid in Ranger")

	return hdfs_objects, hdfs_policies, hive_objects, hive_policies

def send_audit_email(ad_disabled_accounts, admemberof_list, 
					 ad_no_ldap, ambari_audit_actions, 
					 disabled_accts_ad_membership, disabled_principals,
					 disabled_accts_ldap_membership, email_override,
					 hdfs_audit_actions, imported_ad_groups,
					 imported_ldap_groups, invalid_ambari_users, 
					 invalid_hdfs_users, invalid_ranger_users, 
					 locked_ad_accounts, ldap_group_filter_list, 
					 log_filename, no_email, origin_host, 
					 processed_ad_groups, processed_ldap_groups, 
					 ranger_audit_actions, scanned_adgroups, 
					 scanned_ldapgroups):
	""" Sends an email out based on given information and type"""

	# elements always used outside of any statement
	date_stamp = str(time.strftime("%c"))

	# format any lists or objects here
	invalid_ranger_users.sort()
	ad_disabled_accounts = collections.OrderedDict(sorted(ad_disabled_accounts.items()))
	disabled_principals = collections.OrderedDict(sorted(disabled_principals.items()))
	scanned_adgroups = collections.OrderedDict(sorted(scanned_adgroups.items()))
	scanned_ldapgroups = collections.OrderedDict(sorted(scanned_ldapgroups.items()))
	disabled_accts_ldap_membership.sort()
	locked_ad_accounts.sort()
	imported_ad_groups.sort() 
	imported_ldap_groups.sort()

	# Set values to "None" or "No issues" if they are no set
	if not ad_disabled_accounts: 
		ad_disabled_accounts['None'] = "None"
	if not ad_no_ldap:
		ad_no_ldap = "None"
	if not ambari_audit_actions:
		ambari_audit_actions.append("None")
	if not disabled_accts_ldap_membership:
		disabled_accts_ldap_membership = "None"
	if not disabled_principals:
		disabled_principals['None'] = "None"
	if not invalid_ranger_users:
		invalid_ranger_users.append("None")
	if not hdfs_audit_actions:
		hdfs_audit_actions.append("None")
	if not locked_ad_accounts:
		locked_ad_accounts.append("None")
	if not ranger_audit_actions:
		ranger_audit_actions = "None"

	if no_email is False:
		# Send email out if list that holds invalid users exists
		if invalid_ranger_users or ad_disabled_accounts or locked_ad_accounts or ranger_audit_actions:	

			if not email_override:
				tofield = "udahadoopops@geisinger.edu"
			else:
				tofield = email_override

			logging.info("\n\n== Sending Hadoop user audit email ==\n")

			# Define the message headers for email
			msg = MIMEMultipart()
			msg["From"] = "audit-tool@geisinger.edu" 
			msg["To"] = tofield
			msg["Subject"] = "Hadoop environment audit for: " + date_stamp
			msg.attach(MIMEText(

			# Informational metrics
			divider + "Informational metrics: \n" + divider +
			"\n\nImported AD groups: \n" + subdivider + ', '.join(imported_ad_groups) +
			"\n\n" + "Imported LDAP Groups: \n" + subdivider + ', '.join(imported_ldap_groups) +
			"\n\nAD Groups scanned for memberships: \n" + subdivider + ', '.join(scanned_adgroups) +
			"\n\n" + "LDAP groups scanned for memberships: \n" + subdivider + ', '.join(scanned_ldapgroups) +

			# AD principal accounts
			"\n\n" + divider + "AD principal accounts audit: \n" + divider +
			"\n" + "Disabled principals: \n" + 
			subdivider + "* " + "\n* ".join(disabled_principals) +

			# Ambari audit 
			"\n\n" + divider + "Ambari audit: \n" + divider +
			"\n" + "Ambari users that are not in LDAP: \n" + 
			subdivider + ', '.join(invalid_ambari_users) + 

			# HDFS audit 
			"\n\n" + divider + "HDFS audit: \n" + divider +
			"\n" + "HDFS users that are not in LDAP: \n" + 
			subdivider + ', '.join(invalid_hdfs_users) + 

			# Ranger audit 
			# TODO - FIX ME. For invalid ranger users, two lists are returned here...
			"\n\n" + divider + "Ranger audit: \n" + divider +
			"\n" + "Ranger users that are not in LDAP/AD: \n" + 
			subdivider + ', '.join(invalid_ranger_users) + 

			# User account audit
			"\n\n" + divider + "Global user account audit: \n" + divider +
			"This section contains a rollup of all users processed in this audit." +
			"\n\nWe do passthrough to AD, so if useres are disabled in AD they're already" +
			"disabled in our environment too. HDFS directories should ONLY be removed if " +
			"the directory is empty. There could be Hive external tables in those and/or " +
			"other data we need to retain." +
			"\n\nThese accounts should be disabled/removed from applications, including, but not limted to:" +
			"\n\n* Ranger\n* Ambari\n* /user/<USERNAME> HDFS dir" +
			"\n\n" + "Accounts disabled in AD: " + 
			"\n" + subdivider + ', '.join(ad_disabled_accounts) +
			"\n\n" + "Valid AD accounts not in LDAP: " + 
			"\n" + subdivider + ', '.join(ad_no_ldap) +
			"\n\n" + "AD group memberships for disabled AD accounts: " + 
			"\n" + subdivider + "* " + "\n* ".join(disabled_accts_ad_membership) +
			"\n\n" + "LDAP group memberships for disabled AD accounts: " + 
			"\n" + subdivider + "* " + "\n* ".join(disabled_accts_ldap_membership) +
			"\n\n" + "Accounts locked out in AD: " +
			"\n" + subdivider + ', '.join(locked_ad_accounts) +

			# Append any suggested actions admins should take
			"\n\n" + divider + "Suggested audit actions to take: \n" + divider +
			"\n" + "Ambari: \n" + 
			subdivider + "* " + "\n* ".join(ambari_audit_actions) +
			"\n\n" + "Ranger: \n" + 
			subdivider + "* " + "\n* ".join(ranger_audit_actions) +
			"\n\n" + "HDFS: \n" + 
			subdivider +  
			"Note: It is suggested to only clean these directories if you are sure the " +
			"user is also cleared from the group that gave them this directory under " +
			"homedir-create.py. If you fail to do so, homedir-create.py will recreate " +
			"the directory, as it merely reads the group members from the Linux group " +
			"(.e.g. 'getent group udaphiidprod'). \n\n" + "If you choose to clean out " +
			"user from the group, make sure you check the 'Remedy Ticket Procedures' " +
			"page in Confluence.\n\n" +
			"* " + "\n* ".join(hdfs_audit_actions) +

			# add signature
			"\n\nA copy of the complete audit log is attached." + 
			"\n" + divider + "(Sent via Linux Sendmail on " + origin_host + " via audit-tool.py)"
			))

			# add attachment
			f = file(log_filename)
			attachment = MIMEText(f.read())
			filename_basename = os.path.basename(log_filename)
			attachment.add_header('Content-Disposition', 'attachment', filename=filename_basename)
			msg.attach(attachment)

			# Send email
			logging.info("Sending email via Sendmail to: " + str(tofield))
			p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
			p.communicate(msg.as_string())
			logging.info("Email sent to: " + str(tofield))


	else:
		logging.info("Email function is disabled this run")

def send_discrepancy_email(ad_discrepancies, email_override,
						   ldap_discrepancies, missing_ldap_members,
						   origin_host, scanned_adgroups):
	""" Sends an email out on AD -> LDAP discrepancies """

	# elements always used outside of any statement
	date_stamp = str(time.strftime("%c"))
	divider = str('-' * 110 + "\n")
	subdivider = str('-' * 55 + "\n")

	# Sort any lists
	if missing_ldap_members:
		missing_ldap_members.sort()

	# This should always exist
	scanned_adgroups = collections.OrderedDict(sorted(scanned_adgroups.items()))

	# Send email out if list that holds invalid users exists
	if ad_discrepancies or ldap_discrepancies:

		logging.info("\n\n== Sending list of AD and LDAP discrepancies ==\n")

		if not email_override:
			tofield = "udahadoopops@geisinger.edu"
		else:
			tofield = email_override

		# Define the message headers for email
		msg = MIMEMultipart()
		msg["From"] = "audit-tool@geisinger.edu"
		msg["To"] = tofield
		msg["Subject"] = "Hadoop AD and LDAP Discrepancies" + date_stamp
		msg.attach(MIMEText(

		# Note important reminders
		"\nPlease note: Results below are validated against ldap/adldap " +
		"only, as they should be. Do not rely on getent/id commands as " +
		"the sole source-of-truth. If you notice an issue between ldap/" +
		"adldap, getent, and id, investigate any cache issues on hosts." +

		# Informational metrics
		"\n\n" + divider + "List of AD -> LDAP discrepancies: \n" + divider +
		"\nAD Groups Scanned: \n" + subdivider + ', '.join(scanned_adgroups) +
		"\n\nAD -> LDAP Discrepancies (Active accounts only): \n" + subdivider +
		"* " + "\n* ".join(ad_discrepancies) +
		"\n\n" + divider + "List of LDAP -> AD discrepancies: \n" + divider +
		"\nDiscrepancies (Active accounts only): \n" + subdivider +
		"* " + "\n* ".join(ldap_discrepancies) +

		# Report missing openldap users
		"\n\n" + divider + "WARNING: These users do not have an OpenLDAP account!\n" + divider +
		"\nMember list (Accounts with disabled AD accounts are not included): \n" + subdivider + 
		"* " + "\n* ".join(missing_ldap_members) +

		"\n\n" + divider + "(Sent via Linux Sendmail on " + origin_host + 
		" via audit-ad-ldap-groups.py)"
		))

		# Send email
		logging.info("Sending email via Sendmail to: " + str(tofield))
		p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
		p.communicate(msg.as_string())
		logging.info("Email sent to: " + str(tofield))

	else:
		logging.info("No discrepancies to report")

def validate_os_group(group):
	"""Checks give group against OS password listing (.e.g. using getent)"""

	try:
		grp.getgrnam(group)
		status = True
	except KeyError:
		status = False

	return status

def validate_os_user(user):
	"""Checks give username against OS password listing (.e.g. using getent)"""

	try:
		pwd.getpwnam(user)
		status = True
	except KeyError:
		status = False

	return status
