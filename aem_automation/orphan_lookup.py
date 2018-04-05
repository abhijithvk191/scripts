import boto3
from config import config
import subprocess
dynamodb = boto3.client('dynamodb',region_name='ap-south-1')


response =  dynamodb.scan(
    TableName='aem-mlic-autoscaling-mapping',
    ScanFilter={'is-orphan':{
                'AttributeValueList':[{'S':'yes'}],
                'ComparisonOperator':'EQ'                                    }
                }
            )

tbl_name=config['dynamodb_table_name']
disp_list = []
pub_list = []
for item in response['Items']:
    if item['application-type']['S'] == 'orphan-publisher':
        pub_list.append(item)
    else:
        disp_list.append(item)
print (disp_list)
print (pub_list)

pub_len = len(pub_list)
disp_len = len(disp_list)
if pub_len >= 1 and disp_len >= 1 :
    pass
else:
    exit(0)


def delete_orphan(instance_id,tbl_name):

    try:
        response = dynamodb.delete_item(TableName=tbl_name,Key={'instance-id': {'S': 'orphan-'+instance_id}})
    except:
        print("No orphan entry to delete")


def update_dispatcher_conf(dispatcher_Ip):
    print dispatcher_Ip
    command = "ssh -o StrictHostKeyChecking=no root@" + dispatcher_Ip + " " + config['update_conf_script'] + " " + publisher_internal_ip
    print command
    try:
        subprocess.call(command,shell=True)
    except:
        message = "unable to connect to dispatcher for updating conf"
        print(message)

count = min(pub_len, disp_len)

for i in range(count):
    disp = disp_list[i]
    pub  = pub_list[i]
    dispatcher_instance_id = disp['instance-id']['S'].split('orphan-')[1]
    publisher_instance_id  = pub['instance-id']['S'].split('orphan-')[1]
    dispatcher_internal_ip = disp['own-ip']['S']
    global publisher_internal_ip
    publisher_internal_ip  = pub['own-ip']['S']
    dispatcher_response = dynamodb.update_item(
    TableName=config['dynamodb_table_name'],
    Key={
        'instance-id':{'S':dispatcher_instance_id}
        },
    AttributeUpdates={'dependent-ip':{
        'Value':{'S':publisher_internal_ip}}}
            )
    publisher_response = dynamodb.update_item(
    TableName=config['dynamodb_table_name'],
    Key={
        'instance-id':{'S':publisher_instance_id}
        },
    AttributeUpdates={'dependent-ip':{
        'Value':{'S':dispatcher_internal_ip}}}
            )
    delete_orphan(dispatcher_instance_id,tbl_name)
    delete_orphan(publisher_instance_id,tbl_name)
