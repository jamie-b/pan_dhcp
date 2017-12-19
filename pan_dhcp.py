#!/usr/bin/env python
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import xml.etree.ElementTree as ET

#fwhost can be either an IP address or a DNS record - enter it below between the quotation marks
#for an IP address, it would look like: fwhost = "192.168.1.1"
#for a DNS object, it would look like: fwhost = "fwmanagement.yourdomain.com"
fwhost = ""

#fwkey is the API key that is generated by the firewall for the account that the API will impersonate
#You can generate the key using the following URL to the firewall:
#https://<firewall>/api?type=keygen&user=<username>&password=<password>
#The response will be in XML and the key will be between the <key> and </key> tags
#Copy that entire key into the variable below between the quotation marks
fwkey = ""

#Make call to firewall to get XML DHCP lease information
values = {'type': 'op', 'cmd': '<show><dhcp><server><lease>all</lease></server></dhcp></show>', 'key': fwkey}
palocall = 'https://%s/api/' % (fwhost)
r = requests.post(palocall, data=values, verify=False)

#Convert the response from the firewall to an ElementTree to parse as XML
tree = ET.fromstring(r.text)

#Create an XML string to hold the firewall UserID update information
fwxml = '<uid-message>\n'
fwxml = fwxml + '\t<version>1.0</version>\n'
fwxml = fwxml + '\t<type>update</type>\n'
fwxml = fwxml + '\t<payload>\n'
fwxml = fwxml + '\t\t<login>\n'

#Parse the IP and Hostname information from the DHCP lease data and add it to the firewall XML update string

for interface in tree.find('result').findall('interface'):
  for lease in interface.findall('entry'):

    #We really want a hostname if possible, so we're going to look for that in the DHCP lease information first.
    if lease.find('hostname') is not None:
      ip = lease.find('ip').text
      mac = lease.find('mac').text
      host = lease.find('hostname').text
      fwxml = fwxml + '\t\t\t<entry name="' + host + '-' + mac + '" ip="' + ip + '" timeout="0"></entry>\n'

    #If the hostname is not available, we want to use the MAC address instead
    else:
      ip = lease.find('ip').text
      mac = lease.find('mac').text
      fwxml = fwxml + '\t\t\t<entry name="' + mac + '" ip="' + ip + '" timeout="0"></entry>\n'

#Close out the firewall XML update sring
fwxml = fwxml + '\t\t</login>\n'
fwxml = fwxml + '\t</payload>\n'
fwxml = fwxml + '</uid-message>\n'

#Convert the XML update to a memory file so we can upload it to the firewall as a file post (this avoids the 2048-bit limit imposed by a GET)
fwfile = open('fwupdate.xml', 'w')
fwfile.write(fwxml)
fwfile.close()

#Upload the update to the firewall
files = {'fwupdate.xml': open('fwupdate.xml','rb')}
values = {'type': 'user-id', 'key': fwkey}
palocall = 'https://' + fwhost + '/api'
r = requests.post(palocall, data=values, files=files, verify=False)
