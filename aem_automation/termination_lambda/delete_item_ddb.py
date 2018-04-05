import boto3
import ast
import os
import logging
import botocore
import requests
from time import sleep

#Logging module configuration
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
sns = boto3.client('sns', region_name='ap-south-1')
autoscale = boto3.client('autoscaling',region_name='ap-south-1')
dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
ec2 = boto3.client('ec2',region_name='ap-south-1')
cloudwatch = boto3.client('cloudwatch',region_name='ap-south-1')




'''
Send sns notification
'''
def sent_notification(message):
    try:
        sns.publish(TopicArn=os.environ['SNS_ARN'], Message=message)
    except:
        print (" unable to send notification")




def select_one_instance():
    response = dynamodb.scan(TableName=os.environ['DYNAMODB_TABLE_NAME'],AttributesToGet=['instance-id','dependent-ip','application-type','az','own-ip'])
    instances = response['Items']
    disp_list = []
    for inst in instances:
        if inst['application-type']['S'] == 'dispatcher':
            print (inst)
            disp_list.append(inst)
    az1 = 0
    az2 = 0
    for disp in disp_list:
        if disp['az']['S'] == 'ap-south-1a':
            az1 += 1
        else:
            az2 += 1
    print (az1)
    print (az2)

    disp_list = []
    pub_iplist = []
    if az1 == az2:
        for inst in instances:
            if inst['application-type']['S'] == 'dispatcher':
                return inst['instance-id']['S']

    elif az1 > az2:
        for inst in instances:
            if inst['application-type']['S'] == 'dispatcher' and inst['az']['S'] == 'ap-south-1a':
                disp_list.append(inst)
                pub_iplist.append(inst['dependent-ip']['S'])
    else:
        for inst in instances:
            if inst['application-type']['S'] == 'dispatcher' and inst['az']['S'] == 'ap-south-1b':
                disp_list.append(inst)
                pub_iplist.append(inst['dependent-ip']['S'])
    print (disp_list)
    print (pub_iplist)

    linked_pub_list = []
    for inst in instances:
        if inst['application-type']['S'] == 'publisher' and inst['own-ip']['S'] in pub_iplist:
            linked_pub_list.append(inst)
    print (linked_pub_list)

    pub_list = []
    for inst in instances:
        if inst['application-type']['S'] == 'publisher':
            print (inst)
            pub_list.append(inst)
    az1 = 0
    az2 = 0
    for pub in pub_list:
        if pub['az']['S'] == 'ap-south-1a':
            az1 += 1
        else:
            az2 += 1
    if az1 > az2:
        az = 'ap-south-1a'
    else :
        az = 'ap-south-1b'


    for inst in linked_pub_list:
        if inst['az']['S'] == az:
            dis_ip = inst['dependent-ip']['S']
            for ins in instances:
                if ins['own-ip']['S'] == dis_ip:
                    print (ins['instance-id']['S'],inst['instance-id']['S'])
                    return (ins['instance-id']['S'])




def get_ipv4(instance_id):
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        internal_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
        return internal_ip
    except:
        message = "unable to describe instance on running get_ipv4 instance: " + instance_id
        print(message)
        sent_notification(message)
        exit()





def scan_dynamodb(instance_Id):
    response =  dynamodb.scan(
        TableName=os.environ['DYNAMODB_TABLE_NAME'],
        ScanFilter={'instance-id':{
                    'AttributeValueList':[{'S':str(instance_Id)}],
                    'ComparisonOperator':'EQ'                                    }
                    }
                        )
    print (response)
    items = response['Items']
    item = items[0]
    linked_publisher_ip = item['dependent-ip']['S']
    filters = [{'Name': 'network-interface.addresses.private-ip-address', 'Values': [linked_publisher_ip]}]

    response = ec2.describe_instances(Filters=filters)
    linked_publisher_instance_id    = response['Reservations'][0]['Instances'][0]['InstanceId']
    return (linked_publisher_instance_id)






def detatch_from_asg(instance_Id,asg):
    print (str(instance_Id) + " " + str(asg))
    response = autoscale.detach_instances(InstanceIds=[instance_Id],AutoScalingGroupName=asg,ShouldDecrementDesiredCapacity=True)





def delete_ddb_item(instance_list):
    for instance in instance_list:
        response = dynamodb.delete_item(TableName=os.environ['DYNAMODB_TABLE_NAME'],Key={'instance-id': {'S': instance}})





def cleanup_agent(publisher_internal_ip):
    publisher_hostname = publisher_internal_ip.replace(".","-")
    author_endpoint = os.environ['AUTHOR_ENDPOINT']
    agent_url_to_del = "http://" + author_endpoint + ":4502/etc/replication/agents.author/" + publisher_hostname
    requests.delete(agent_url_to_del, auth=(os.environ['AEM_USER'],os.environ['AEM_PASS']))




def terminate_instances(instance_list):
    try:
        ec2.terminate_instances(InstanceIds=instance_list)
        logger.info("Instances terminated " + str(instance_list))
    except botocore.exceptions.ClientError as e:
        logger.error("Error in terminating ec2 instances ")
        print ("Unexpected Error: " +str(e))



def putmetric():
    response = cloudwatch.put_metric_data(
    Namespace=os.environ['CLOUDWATCH_NAMESPACE'],
    MetricData=[
        {
            'MetricName': 'Downscale',
            'Value': 0,
            'Unit': 'Count',
            'StorageResolution': 1
        }
        ]
        )


def handler(event, context):

    print (event)
    logger.info("Starting lambda function)")
    global latest_dispatcher
    try:
        latest_dispatcher = select_one_instance()
    except:
        message = "unable to fetch the latest launched dispatcher details from asg"
        sent_notification(message)
        exit()
    logger.info("Found latest launched dispatcher :" + str(latest_dispatcher))
    global linked_publisher
    try:
        linked_publisher = scan_dynamodb(latest_dispatcher)
    except:
        message = "unable to scan dynamodb for getting details of linked publisher"
        sent_notification(message)
        exit()
    logger.info("Found latest linked publisher :" + str(linked_publisher))
    dispatcher_asg = os.environ['DISPATCHER_ASG']
    try:
        detatch_from_asg(latest_dispatcher,dispatcher_asg)
    except:
        message = "unable to detatch dispatcher from asg"
        sent_notification(message)
        exit()
    logger.info("Detatched dispatcher from : " + str(os.environ['DISPATCHER_ASG']))
    try:
        detatch_from_asg(linked_publisher,os.environ['PUBLISHER_ASG'])
    except:
        message = "unable to detatch publisher from asg"
        sent_notification(message)
        exit()
    logger.info("Detatched publisher from : " + str(os.environ['PUBLISHER_ASG']))
    try:
        delete_ddb_item([latest_dispatcher,linked_publisher])
    except:
        message = "unable to delete dynamodb table entries"
        sent_notification(message)
        exit()
    logger.info("Dynamodb items deleted for dispatcher and publisher")
    try:
        publisher_internal_ip = get_ipv4(str(linked_publisher))
    except:
        message = "unable to fetch the internal IP of publisher"
        sent_notification(message)
        exit()
    try:
        cleanup_agent(publisher_internal_ip)
    except:
        message = "unable to clean publisher agent on author"
        sent_notification(message)
        exit()
    logger.info("Cleaned author replication agent for publisher")
    try:
        terminate_instances([latest_dispatcher,str(linked_publisher)])
    except:
        message = "unable to terminate instances"
        sent_notification(message)
        exit()
    logger.info("Termination completed")
    try:
        putmetric()
    except:
        message = "unable to put metrics to cloudwatch"
        sent_notification(message)
        exit()
    logger.info("Lambda function completed.. :-)")
