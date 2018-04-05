import boto3
from config import ips

client_online=boto3.client('ec2',region_name="eu-west-1",aws_access_key_id='***************',aws_secret_access_key='***************************')
region_list=[i['RegionName']  for i in client_online.describe_regions()['Regions']]
clients=[]
for i in region_list:
    client_online=boto3.client('ec2',region_name="%s"%i,aws_access_key_id='***************************',aws_secret_access_key='**************************')
    clients.append(client_online)
instances_list=[]
[instances_list.append(i.describe_instances()) for i in clients]
id_ip_dict={}
for k in instances_list:
    for i in k['Reservations']:
        if i['Instances'][0]['State']['Name'] == 'running':
            ip=i['Instances'][0]['PublicIpAddress']
            instance_id=i['Instances'][0]['InstanceId']
            id_ip_dict[ip]=instance_id

for i in ips.keys():
    for j in ips[i]:
        for k in clients:
            try:
                k.create_tags(Resources=[id_ip_dict[j]],Tags=[{'Key': 'User','Value': i}])
                break
            except Exception as e:
                pass
