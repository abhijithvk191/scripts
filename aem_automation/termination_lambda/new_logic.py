
import boto3

s = boto3.session.Session(profile_name='mlic')
dynamodb = s.client('dynamodb',region_name='ap-south-1')
ec2 = s.client('ec2',region_name='ap-south-1')
autoscale = s.client('autoscaling',region_name='ap-south-1')








def get_az(p_ip):
    """
    Getting az with private ip
    """
    response = ec2.describe_instances(Filters=[{'Name':'network-interface.addresses.private-ip-address','Values':[p_ip]}])
    az = response['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    return az



def get_ipv4(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    internal_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
    return internal_ip



def get_all_values():
    """
    Getting all values from DDB
    """
    out = {}
    response = dynamodb.scan(TableName='aem-mlic-autoscaling-mapping',AttributesToGet=['instance-id','dependent-ip'])
    for i in response['Items']:
        out[i['instance-id']['S']]=i['dependent-ip']['S']
    return out



def ddb_find_instance_type(instance_Id):
    response =  dynamodb.scan(
        TableName='aem-mlic-autoscaling-mapping',
        ScanFilter={'instance-id':{
                    'AttributeValueList':[{'S':str(instance_Id)}],
                    'ComparisonOperator':'EQ'                                    }
                    }
                        )
    print (response)
    items = response['Items']
    item = items[0]
    app_type = item['application-type']['S']
    return app_type




def mapp_instanceid_ip(d):
    """
    Mapping all table values with ip-ip mapp
    """
    mapped = {}
    for i in d:
        ip1 = get_ipv4(i)
        az1 = get_az(ip1)
        az2 = get_az(d[i])
        mapped[i]={'own':[ip1,az1],'dep':[d[i],az2]}
    return mapped


ddb_dict = get_all_values()

mapped_dict = mapp_instanceid_ip(ddb_dict)
instances_to_terminate = []

for i in mapped_dict:
    if mapped_dict[i]['dep'][1] != mapped_dict[i]['own'][1]:
        instances_to_terminate.append(i)
print (instances_to_terminate)
for i in instances_to_terminate:
    instance_type = scan_dynamodb(i)
    if instance_type == 'dispatcher':
        print i
        exit(0)
