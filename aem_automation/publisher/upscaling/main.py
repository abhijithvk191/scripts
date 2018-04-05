import boto3
from config import config
autoscale = boto3.client('autoscaling',region_name='ap-south-1')
ec2 = boto3.client('ec2',region_name='ap-south-1')
import requests
sns = boto3.client('sns', region_name='ap-south-1')
dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
import subprocess






'''
Send sns notification
'''
def sent_notification(message):
    try:
        sns.publish(TopicArn=config['sns_arn'], Message=message)
    except:
        print (" unable to send notification")



'''
 Check how this instance is launched
 Compares desired count in both autoscaling groups
'''
def get_trigger_type():
    try:
        publisher_response = autoscale.describe_auto_scaling_groups(AutoScalingGroupNames=[config['publisher_asg']])
    except:
        message = "unable describe publisher autoscaling group"
        sent_notification(message)
        exit()
    try:
        dispatcher_response = autoscale.describe_auto_scaling_groups(AutoScalingGroupNames=[config['dispatcher_asg']])
    except:
        message = "unable to describe dispatcher autoscaling group"
        print(message)
        sent_notification(message)
        exit()
    desired_publisher_count = publisher_response['AutoScalingGroups'][0]['DesiredCapacity']
    print(desired_publisher_count)
    desired_dispatcher_count = dispatcher_response['AutoScalingGroups'][0]['DesiredCapacity']
    print(desired_dispatcher_count)

    if (desired_publisher_count > desired_dispatcher_count):
        return("load")
        print("load")
    else:
        return("non_load")
        print("non_load")



'''
Add entries to dynamodb tables
Map instance-id of publisher and internal ip of dispatcher
'''
def add_to_ddb(instance_Id):
    print("adding entry to dynamodb")
    try:
        response = dynamodb.put_item(
            TableName=config['dynamodb_table_name'],
            Item={
                'instance-id':{'S':instance_Id},
                'application-type':{'S':'publisher'}
                }
                        )
    except:

        message = "unable to put into dynamodb- add_to_ddb function failed"
        print(message)
        sent_notification(message)
        exit()




'''
Send curl request to author for creating replication agent
'''
def create_author_replication_agent():

    host_name =  publisher_internal_ip.replace(".", "-")
    agent_title = "Replication to " + host_name
    author_master = config['author_IP']
    agent_description = "Agent that replicates to the publish instance " + host_name
    own_internal_ip_input = "http://" + publisher_internal_ip + ":4503/bin/receive?sling:authRequestLogin=1&binaryless=true"
    author_transport_password_value = config['author_transport_password']
    author_transport_user_value = config['author_transport_user']
    author_url_rep_agent = "http://" + author_master + ":4502/etc/replication/agents.author/"  + host_name
    author_referer = "http://" + author_master + ":4502/ http://" + author_master + ":4502/etc/replication/agents.author"


    keyvalues_replication = {'jcr:primaryType':'cq:Page',
                             'jcr:content/cq:template':'/libs/cq/replication/templates/agent',
                             'jcr:content/sling:resourceType':'cq/replication/components/agent',
                             'jcr:content/serializationType':'durbo',
                             'jcr:content/jcr:title':str(agent_title),
                             'jcr:content/enabled':'true',
                             'jcr:content/jcr:description':str(agent_description),
                             'jcr:content/logLevel':'info',
                             'jcr:content/retryDelay':'60000',
                             'jcr:content/transportUri':str(own_internal_ip_input),
                             'jcr:content/transportPassword':str(author_transport_password_value),
                             'jcr:content/transportUser':str(author_transport_user_value)}


    #Setting up Replication in Author  Master
    try:
        rep_request_data=requests.post(str(author_url_rep_agent), data=keyvalues_replication, auth=(author_transport_user_value, author_transport_password_value), headers={'referer': str(author_referer)})
    except:
        message = "Agent Generation on Author Failed"+" : "+ str(publisher_internal_ip)
        #logging.exception("Unexpected error")
        sns.publish(TopicArn=config['sns_arn'], Message=message)
        time.sleep(60)





"""
Increment autoscale desired count
"""
def update_asg(gp_name,current_count):
   try:
       response = autoscale.update_auto_scaling_group(AutoScalingGroupName=gp_name,DesiredCapacity=int(current_count)+1)
   except:
       message = "unable to update autoscale gp"
       print(message)
       sent_notification(message)
       exit()




'''
Get instance id of running instance
'''
def get_instance_id():
    r = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
    instance_id = r.text
    return(instance_id)
    print("publisher instance id is: " +instance_id)




'''
Return local ipv4 on passing instance_id
'''
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




'''
Instance is launched due to load in publisher autoscaling group
update minimum and desired values in dispatcher asg
update dispatcher configuration
update dynamodb
'''
def load_triggered():
    print ("starting load triggered operations")

    try:
        response = autoscale.describe_auto_scaling_groups(AutoScalingGroupNames=[config['dispatcher_asg']])
        current_count = response['AutoScalingGroups'][0]['DesiredCapacity']
    except:
        message = "unable to get current desired count in dispatcher asg"
        print(message)
        sent_notification(message)
        exit()
    update_asg(config['dispatcher_asg'],current_count)


    '''ADDING NEW DYNAMODB ENTRY'''
    add_to_ddb(publisher_instance_id)
    create_author_replication_agent()



'''
Create a new dynamodb entry with instance-id and linked
'''
def new_ddb_item(instance_Id,internal_Ip):
    response = dynamodb.put_item(
        TableName=config['dynamodb_table_name'],
        Item={
            'instance-id':{'S':instance_Id},
            'application-type':{'S':'publisher'},
            'dependent-ip':{'S':internal_Ip}
            }
        )





'''
instance is launched as part of dispatcher autoscaling
'''
def dispatcher_triggered():
    response =  dynamodb.scan(
        TableName=config['dynamodb_table_name'],
        ScanFilter={'dependent-ip':{
                'ComparisonOperator':'NULL',
                                    },
                    'application-type':{
                    'AttributeValueList':[{'S':'dispatcher'}],
                    'ComparisonOperator':'EQ'                                    }
                    }
                        )
    print (response)
    count = response['Count']
    items = response['Items']
    item = items[0]
    print (item)
    print (publisher_instance_id)
    print (publisher_internal_ip)
    response = dynamodb.update_item(
    TableName=config['dynamodb_table_name'],
    Key={
        'instance-id':item['instance-id']
        },
    AttributeUpdates={'dependent-ip':{
        'Value':{'S':publisher_internal_ip}}}
            )
    dispatcher_internal_ip = get_ipv4(item['instance-id']['S'])
    update_dispatcher_conf(dispatcher_internal_ip)
    new_ddb_item(publisher_instance_id,dispatcher_internal_ip)
    create_author_replication_agent()






'''
script to update dispatcher conf
'''
def update_dispatcher_conf(dispatcher_Ip):
    command = "ssh -o StrictHostKeyChecking=no root@" + dispatcher_Ip + " " + config['update_conf_script'] + " " + publisher_internal_ip
    try:
        subprocess.call(command,shell=True)
    except:
        message = "unable to connect to dispatcher for updating conf"
        print(message)
        sent_notification(message)
        exit()



def main():
    global publisher_instance_id
    publisher_instance_id = get_instance_id()
    global publisher_internal_ip
    publisher_internal_ip = get_ipv4(publisher_instance_id)
    print ("starting")
    trigger_type = get_trigger_type()
    print ("trigger type: " + trigger_type)
    if trigger_type == "load":
        load_triggered()
        pass
    elif trigger_type == "non_load":
        dispatcher_triggered()
        pass


if __name__ == '__main__':
    main()
