import requests
import boto3
import sys

dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
r = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
publisher_instance_id = r.text
print (publisher_instance_id)



instance_creation_type = sys.argv[0]
dispatcher_internal_ip = sys.argv[1]




'''
function tp map publisher instance id and dispatcher internal ip in dynamodb table
'''
def add_to_ddb(instance_Id,internal_Ip):
    response = dynamodb.put_item(
        TableName='aem-mlic-autoscaling-mapping',
        Item={
            'instance-id':{'S':instance_Id},
            'application-type':{'S':'publisher'},
            'dependent-ip':{'S':internal_Ip}
            }
        )






'''
create replication agent in author server
'''
def create_replication_agent():

    pass



'''
update current dynamodb table with new dispatcher ip
'''
def update_ddb(instance_Id,internal_Ip):
    response = dynamodb.update_item(
    TableName='aem-mlic-autoscaling-mapping',
    Key={
                    'instance-id':{'S':instance_Id}
        },
        AttributeUpdates={'dependent-ip':{
                        'Value':{'S':internal_Ip}}}
                        )




def main():
    if (instance_creation_type.lower() == 'unhealthy'):
        '''funtions to run when call is from a disptcher created due to an unhealthy instance'''
        update_ddb(publisher_instance_id,dispatcher_internal_ip)
        create_replication_agent()

    elif (instance_creation_type.lower() == 'load'):
        '''funtions to run when call is from a disptcher created due to the load in asg'''
        add_to_ddb(publisher_instance_id,dispatcher_internal_ip)
        create_replication_agent()

