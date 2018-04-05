import boto3
from botocore.client import Config
from configobj import ConfigObj
import os

config_details=ConfigObj('config_details.py')
ansible_inventory_path=config_details['ansible_inventory_path']
ssh_config_path=config_details['ssh_config_path']

#getting all regions
print 'Getting region list'
client_classifieds=boto3.client('ec2',region_name='eu-west-1',aws_access_key_id='AKIAIVH6LMPKQY735VKQ',aws_secret_access_key='******************************')
region_list=[i['RegionName']  for i in client_classifieds.describe_regions()['Regions']]

#Setting read and default timeout
config = Config(connect_timeout=50, read_timeout=100)

#getting connection objects for all regions all accounts
print 'Getting EC2 connection objects'
clients=[]
for i in region_list:
    client_classifieds=boto3.client('ec2',region_name="%s"%i,aws_access_key_id='AKIAIVH6LMPKQY735VKQ',aws_secret_access_key='*************************',config=config)
    clients.append(client_classifieds)
    client_online=boto3.client('ec2',region_name="%s"%i,aws_access_key_id='AKIAJHB24ETUOOZ7FJQA',aws_secret_access_key='***************************',config=config)
    clients.append(client_online)
    client_psupport=boto3.client('ec2',region_name="%s"%i,aws_access_key_id='AKIAJRRLHJCSR7NPVODA',aws_secret_access_key='**************************',config=config)
    clients.append(client_psupport)
    client_mmsupport=boto3.client('ec2',region_name="%s"%i,aws_access_key_id='AKIAINEQFZEB57OGGLSA',aws_secret_access_key='**************************',config=config)
    clients.append(client_mmsupport)
    client_classifieds_test=boto3.client('ec2',region_name="%s"%i,aws_access_key_id='AKIAI3C6LACZSTTKMRZQ',aws_secret_access_key='************************',config=config)
    clients.append(client_classifieds_test)

#getting instance description
print 'Collecting instance description'
instances_list=[]
[instances_list.append(i.describe_instances()) for i in clients]

#getting data
print 'Sorting out data from the instance description'
main={}
for k in instances_list:
    for i in k['Reservations']:
        if i['Instances'][0]['State']['Name'] == 'running':
            tag=i['Instances'][0]['Tags']
            if 'Platform' in i['Instances'][0].keys():
                project='Windows'
                if project not in main.keys():
                    main[project]=[]
                for j in tag:
                    if j['Key']=='Name':
                        name_key=j['Value']
                        name=name_key.replace(" ","")
                    if j['Key']=='User':
                        user=j['Value']
            else:
                for j in tag:
                    if j['Key']=='PROJECT':
                        project_key=j['Value']
                        project=project_key.replace(" ","")
                        if project not in main.keys():
                            main[project]=[]
                    if j['Key']=='Name':
                        name_key=j['Value']
                        name=name_key.replace(" ","")
                    if j['Key']=='User':
                        user=j['Value']
            if project == 'PROD-TABLET':
                ip=i['Instances'][0]['PublicIpAddress']
            elif project == 'STAG-TABLET':
                ip=i['Instances'][0]['PublicIpAddress']
            elif project == 'PROD-MINISITES':
                ip=i['Instances'][0]['PublicIpAddress']
            elif project == 'Contest':
                ip=i['Instances'][0]['PublicIpAddress']
            else:
                ip=i['Instances'][0]['PrivateIpAddress']
            key_key=i['Instances'][0]['KeyName']
            key="~/.ssh/%s.pem"%key_key
            values=[name,ip,user,key]
            main[project].append(values)


print 'Writing the inventory and SSH config file'
if os.path.isfile(ansible_inventory_path):
    os.rename(ansible_inventory_path, "%s_back"%ansible_inventory_path)
if os.path.isfile(ssh_config_path):
    os.rename(ssh_config_path, "%s_back"%ssh_config_path)

for i in main.keys():
    append_inventory_text="\n\n[%s]\n"%i
    append_ssh_text="\n\n###%s###\n"%i
    with open(ansible_inventory_path, "a") as file:
        file.write(append_inventory_text)
    with open(ssh_config_path, "a") as file:
        file.write(append_ssh_text)
    for j in main[i]:
        append_inventory_text1="%s    ansible_ssh_host=%s     ansible_ssh_user=%s     ansible_ssh_private_key_file=%s\n"%(j[0],j[1],j[2],j[3])
        append_ssh_text1="Host %s\n    HostName %s\n    Port 22\n    User %s\n    IdentityFile %s\n\n"%(j[0],j[1],j[2],j[3])
        with open(ansible_inventory_path, "a") as file:
            file.write(append_inventory_text1)
        with open(ssh_config_path, "a") as file:
            file.write(append_ssh_text1)
