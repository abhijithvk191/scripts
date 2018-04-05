import boto3
import ast
import os
import logging
import botocore
import re
import requests

#Logging module configuration
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


try:
    logger.info("Trying to connect dynamodb Client")
    ddb_client = boto3.client('dynamodb',region_name='ap-south-1')
    logger.info("Connected to Dynamodb client")
except botocore.exceptions.ClientError as e:
    logger.error("Error in connecting Dynamodb client ")
    print ("Unexpected Error: " +str(e))
    exit()

try:
    logger.info("Trying to connect ec2 Client")
    ec2_client = boto3.client('ec2',region_name='ap-south-1')
    logger.info("Connected to ec2 client")
except botocore.exceptions.ClientError as e:
    logger.error("Error in connecting ec2 client ")
    print ("Unexpected Error: " +str(e))
    exit()

try:
    logger.info("Trying to connect autoscaling Client")
    as_client = boto3.client('autoscaling',region_name='ap-south-1')
    logger.info("Connected to autoscaling client")
except botocore.exceptions.ClientError as e:
    logger.error("Error in connecting autoscaling client ")
    print ("Unexpected Error: " +str(e))
    exit()

def cleanup_agent(publisher_internal_ip):
    publisher_hostname = publisher_internal_ip.replace(".","-")
    author_endpoint = os.environ['AUTHOR_ENDPOINT']
    agent_url_to_del = "http://" + author_endpoint + ":4502/etc/replication/agents.author/" + publisher_hostname
    requests.delete(agent_url_to_del, auth=(os.environ['AEM_USER'],os.environ['AEM_PASS']))
    logger.info(("Replication agent deleted") + str(publisher_hostname))



def scan_dynamodb(instance_id,tbl_name):

    # try:
    #     logger.info("Trying to connect dynamodb Client")
    #     ddb_client = boto3.client('dynamodb',region_name='ap-south-1')
    #     logger.info("Connected to Dynamodb client")
    # except botocore.exceptions.ClientError as e:
    #     logger.error("Error in connecting Dynamodb client ")
    #     print ("Unexpected Error: " +str(e))
    #     exit()

    logger.info("Fetching private ip of instance: " + str(instance_id))
    private_ip=get_ipv4(instance_id)
    logger.info("Private IP of instance ID: " + str(instance_id) + " is " + private_ip)
    logger.info("Scanning Dynamodb: " + str(tbl_name))
    response =  ddb_client.scan(
        TableName=tbl_name)
    #print (response)
    logger.info("Checking the items count of Dynamodb table: " + str(tbl_name))
    if len(response['Items']) == 0:
        logger.info("Items empty in Dynamodb Table")
        #print ("Items empty in Dynamodb Table")
    else:
        logger.info("Items count greater than Zero. Searching instance id: " + str(instance_id))
        for resp in response['Items']:
            try:
                if resp['instance-id']['S'] == instance_id:
                    logger.info("Found instance id: " + instance_id)
                    logger.info("Deleteing dynamodb items with primary key: " + str(instance_id))
                    delete_item_ddb(resp['instance-id']['S'],tbl_name)
            except KeyError:
                logger.info("Instance ID null in dynamodb table")
            try:
                if resp['dependent-ip']['S'] == private_ip:
                    logger.info("Deleteing dependent ip")
                    update_item_ddb(resp['instance-id']['S'],resp['application-type']['S'],tbl_name)
                    application_type = resp['application-type']['S']
                    if re.search('publisher',application_type.lower()):
                        cleanup_agent(private_ip)
            except KeyError:
                logger.info("Private IP null in dynamodb table")



def delete_item_ddb(instance_id,tbl_name):

    # try:
    #     logger.info("Trying to connect dynamodb Client")
    #     ddb_client = boto3.client('dynamodb',region_name='ap-south-1')
    #     logger.info("Connected to Dynamodb client")
    # except botocore.exceptions.ClientError as e:
    #     logger.error("Error in connecting Dynamodb client ")
    #     print ("Unexpected Error: " +str(e))
    #     exit()

    try:
        response = ddb_client.delete_item(TableName=tbl_name,Key={'instance-id': {'S': instance_id}})
    except botocore.exceptions.ClientError as e:
        print ("Unexpected Error: %s" % e)
        exit()


def update_item_ddb(instance_id,application_type,tbl_name):

    # try:
    #     logger.info("Trying to connect dynamodb Client")
    #     ddb_client = boto3.client('dynamodb',region_name='ap-south-1')
    #     logger.info("Connected to Dynamodb client")
    # except botocore.exceptions.ClientError as e:
    #     logger.error("Error in connecting Dynamodb client ")
    #     print ("Unexpected Error: " +str(e))
    #     exit()

    try:
        response = ddb_client.put_item(TableName=tbl_name,Item={'instance-id': {'S': instance_id},'application-type': {'S':application_type}})
    except botocore.exceptions.ClientError as e:
        print ("Unexpected Error: %s" % e)
        exit()

def get_ipv4(instance_id):

    # try:
    #     logger.info("Trying to connect ec2 Client")
    #     ec2_client = boto3.client('ec2',region_name='ap-south-1')
    #     logger.info("Connected to ec2 client")
    # except botocore.exceptions.ClientError as e:
    #     logger.error("Error in connecting ec2 client ")
    #     print ("Unexpected Error: " +str(e))
    #     exit()

    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        internal_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
        logger.info("Private IP: " + str(internal_ip))
        return internal_ip

    except botocore.exceptions.ClientError as e:
        print ("Unexpected Error: %s" % e)
        exit()

def complete_hook(lc_hook,lc_token,asg_name,inst_id):
    # try:
    #     logger.info("Trying to connect autoscaling Client")
    #     as_client = boto3.client('autoscaling',region_name='ap-south-1')
    #     logger.info("Connected to autoscaling client")
    # except botocore.exceptions.ClientError as e:
    #     logger.error("Error in connecting autoscaling client ")
    #     print ("Unexpected Error: " +str(e))
    #     exit()

    try:
        response = as_client.complete_lifecycle_action(LifecycleHookName=lc_hook,AutoScalingGroupName=asg_name,LifecycleActionToken=lc_token,LifecycleActionResult='CONTINUE',InstanceId=inst_id)
    except botocore.exceptions.ClientError as e:
        print ("Unexpected Error: %s" % e)
        exit()


def handler(event, context):
    logger.info("Starting lambda function.. |-)")
    evnt1=ast.literal_eval(event['Records'][0]['Sns']['Message'])
    logger.info("EVENT: " + str(evnt1))
    instance_id=evnt1['EC2InstanceId']
    logger.info("Instance ID: " + str(instance_id))
    lifecycle_action_token=evnt1['LifecycleActionToken']
    logger.info("LifecycleActionToken: " + str(lifecycle_action_token))
    lifecycle_hook_name=evnt1['LifecycleHookName']
    logger.info("lifecycle_hook_name: " + str(lifecycle_hook_name))
    autoscale_grp_name=evnt1['AutoScalingGroupName']
    logger.info("autoscale_grp_name: " + str(autoscale_grp_name))
    scan_dynamodb(instance_id,os.environ['DYNAMODB_TABLE_NAME'])
    logger.info("Running lifecycle hook complete action..!!")
    complete_hook(lifecycle_hook_name,lifecycle_action_token,autoscale_grp_name,instance_id)
    logger.info("Lambda function completed.. :-)")
