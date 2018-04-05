import boto3
from sys import exit
import datetime
#from datetime import datetime, timedelta
import time
import requests
import subprocess
from config import config
ec2 = boto3.client('ec2',region_name='ap-south-1')

def sent_notification(message):
    """
    This will sent notifications to configured address with given message
    """
    # to_address = config['error_email']
    sns = boto3.client('sns', region_name='ap-south-1')
    sns.publish(TopicArn=config['sns_arn'], Message=message)

def get_trigger_type():
    """
    Finding the upscale action source ['load','pair_load/unhealthy']
    """
    result = {}
    p_asg = config['publisher_asg']
    d_asg = config['dispatcher_asg']

    client = boto3.client('autoscaling',region_name='ap-south-1')
    try:
        p_response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[p_asg])
        d_response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[d_asg])
    except:
        message = "un able to update describe autoscale gp"
        sent_notification(message)
        exit()

    if len(p_response['AutoScalingGroups']) > 0 and len(d_response['AutoScalingGroups']) > 0:
        #p_values = dict(k,p_response['AutoScalingGroups'][0][k] for k in ['MinSize','MaxSize','DesiredCapacity'])
        #d_values = dict(l,d_response['AutoScalingGroups'][0][l] for l in ['MinSize','MaxSize','DesiredCapacity'])
        p_values = p_response['AutoScalingGroups'][0]['DesiredCapacity']
        d_values = d_response['AutoScalingGroups'][0]['DesiredCapacity']
    else:
        message = "un able to describe one of the autoscale gp"
        sent_notification(message)
        exit()

    ### trigger logic
    if d_values > p_values:
        result['type'] = 'load'
        result['current_count'] = p_values
    else:
        result['type'] = 'pair_load'
        result['current_count'] = d_values

    return result


def update_asg(gp_name,current_count):
    """
    Increment autoscale desired count
    """
    client = boto3.client('autoscaling',region_name='ap-south-1')
    try:
        response = client.update_auto_scaling_group(AutoScalingGroupName=gp_name,DesiredCapacity=int(current_count)+1)
    except:
        message = "un able to update autoscale gp"
        sent_notification(message)
        exit()

def add_db():
    """
    updating the values to dynamoDB
    """
    try:

        dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
        response = dynamodb.put_item(
            TableName=config['table_name'],
            Item={
                'instance-id':{'S':dispatcher_instance_id},
                'application-type':{'S':'dispatcher'},
                'own-ip':{'S':dispatcher_internal_ip},
                'az':{'S':dispatcher_az}
                }
            )
    except:
        message = "un able to update dynamoDB new entry"
        sent_notification(message)
        exit()

def new_db_item(internal_Ip):
    """
    add new full entry to DB
    """
    if internal_Ip == 'empty':
        dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
        try:
            response = dynamodb.put_item(
                TableName='aem-mlic-autoscaling-mapping',
                Item={
                    'instance-id':{'S':dispatcher_instance_id},
                    'application-type':{'S':'dispatcher'},
                    'own-ip':{'S':dispatcher_internal_ip},
                    'az':{'S':dispatcher_az}
                    }
                )
        except:
            message = "un able to update dynamoDB new item"
            sent_notification(message)
            exit()
    else:
        dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
        try:
            response = dynamodb.put_item(
                TableName='aem-mlic-autoscaling-mapping',
                Item={
                    'instance-id':{'S':dispatcher_instance_id},
                    'application-type':{'S':'dispatcher'},
                    'dependent-ip':{'S':internal_Ip},
                    'own-ip':{'S':dispatcher_internal_ip},
                    'az':{'S':dispatcher_az}
                    }
                )
        except:
            message = "un able to update dynamoDB new item"
            sent_notification(message)
            exit()


def get_instance_ip():
    """
    get its own internal ip
    """
    requ = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4')
    ip = requ.text
    return ip


'''
Create a new dynamodb entry for orphan instances
'''
def new_ddb_item_orphan():
    dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
    response = dynamodb.put_item(
        TableName=config['table_name'],
        Item={
            'instance-id':{'S':'orphan-'+dispatcher_instance_id},
            'application-type':{'S':'orphan-dispatcher'},
            'own-ip':{'S':dispatcher_internal_ip},
            'az':{'S':dispatcher_az},
            'timestamp':{'S':datetime.datetime.now().strftime("%m-%d-%Y-%H:%M")},
            'is-orphan':{'S':'yes'}
            }
        )

def delete_item_ddb(instance_id,tbl_name):

    try:
        response = ddb_client.delete_item(TableName=tbl_name,Key={'instance-id': {'S': 'orphan-'+instance_id}})
    except:
        print("No orphan entry to delete")

def search_update_db():
    """
    1.Search DDB for null value and get instance-id
    2.add ip in null field
    3.update conf and add full entry
    """
    dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
    try:
        response =  dynamodb.scan(
            TableName=config['table_name'],
            ScanFilter={'dependent-ip':{
                    'ComparisonOperator':'NULL',
                                        },
                        'application-type':{
                        'AttributeValueList':[{'S':'publisher'}],
                        'ComparisonOperator':'EQ'                                    }
                        }
                            )
    except:
        message = "un able to scan NULL from dynamodb"
        sent_notification(message)
        exit()

    if response['Count'] == 0:
        new_db_item('empty')
        new_ddb_item_orphan()
        pass

    else:
        items = response['Items']
        item = items[0]
        internal_ip = get_instance_ip()
        try:
            response = dynamodb.update_item(
                TableName=config['table_name'],
                Key={
                    'instance-id':item['instance-id']
                    },
                AttributeUpdates={'dependent-ip':{
                    'Value':{'S':internal_ip}}}
                        )
        except:
            message = "un able to update dynamodb"
            sent_notification(message)
            exit()
        internal_Ip = get_ipv4(item['instance-id']['S'])
        new_db_item(internal_Ip)
        delete_item_ddb(item['instance-id'],config['table_name'])
        update_conf(item['instance-id']['S'])

def get_ipv4(instance_id):

    try:
        client = boto3.client('ec2',region_name='ap-south-1')
        response = client.describe_instances(InstanceIds=[instance_id])
        internal_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
    except:
        message = "un able to get ipv4 for instance id"
        sent_notification(message)
        exit()
    return internal_ip



def get_az(private_ip):
    """
    Getting az with private ip
    """
    response = ec2.describe_instances(Filters=[{'Name':'network-interface.addresses.private-ip-address','Values':[private_ip]}])
    az = response['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    return az




def get_instance_id():
    r = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
    instance_id = r.text
    return(instance_id)
    print("publisher instance id is: " +instance_id)



def load_action(current_count):
    """
    1.update publisher ASG desired count
    2.Update dynamodb table instance id and type
    """
    ## updating autoscale
    update_asg(config['publisher_asg'],current_count)
    ## updating dynamo db
    add_db()

def update_conf(inst_id):
    ip = get_ipv4(inst_id)
    command = config['update_conf_script'] + " " +ip
    try:
        subprocess.call(command,shell=True)
    except:
        message = "unable to update dispatcher conf"
        print(message)
        sent_notification(message)
        exit()

def pair_load_action():
    """
    1.db search for NULL and update values
    """
    search_update_db()

def main():
    """
    1. checks for as  trigger type
    """
    global dispatcher_instance_id
    dispatcher_instance_id = get_instance_id()
    global dispatcher_internal_ip
    dispatcher_internal_ip = get_ipv4(dispatcher_instance_id)
    global dispatcher_az
    dispatcher_az = get_az(dispatcher_internal_ip)

    trigger_type = get_trigger_type()

    if trigger_type['type'] == 'load':
        load_action(trigger_type['current_count'])
    elif trigger_type['type'] == 'pair_load':
        pair_load_action()
    else:
        message = "script panic!!!"
        sent_notification(message)
        exit()

if __name__ == '__main__':
    main()
