import requests
import boto3
import subprocess
from config import config
from time import sleep

az = requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone')
availability_zone = az.text
req = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
instance_id = req.text

dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
ec2 = boto3.client('ec2',region_name='ap-south-1')
sns = boto3.client('sns', region_name='ap-south-1')




'''
Send sns notification
'''
def sent_notification(message):
    try:
        sns.publish(TopicArn=config['sns_arn'], Message=message)
        exit()
    except:
        print (" unable to send notification")




'''
Find the latest snapshot by scanning the dynamodb table
'''
def find_snapshot():
    response =  dynamodb.scan(
        TableName=config['BACKUP_MAPPING_TABLE'],
        ScanFilter={
                    'instance':{
                    'AttributeValueList':[{'S':'publisher'}],
                    'ComparisonOperator':'EQ'                                    }
                    }
                        )
    items = response['Items']
    item = items[0]
    snapshot = item['snapshotId']['S']
    return (snapshot)





'''
Create the volume with the latest snapshot as per the dynamodb tables
'''
def create_volume(snapshot_id):
    response = ec2.create_volume(
    AvailabilityZone=availability_zone,
    SnapshotId=snapshot_id,
    VolumeType='gp2',
    TagSpecifications=[
        {
        'ResourceType':'volume',
        'Tags':[
                {
                'Key': 'Name',
                  'Value': config['publisher_volume_tag']
                  }
                ]
               }
            ]
          )
    print (response)
    volume_id = response['VolumeId']
    return volume_id




'''
Attach the newly created volume as /dev/sdp
'''
def attach_volume(volume_id):
    response = ec2.attach_volume(
    Device='/dev/sdp',
    InstanceId=instance_id,
    VolumeId=volume_id
)




'''
Mount the newly attached volume as /data
'''
def mount_device():
    subprocess.call("mount /dev/xvdp /data",shell=True)




def main():
    try:
        snap_id = find_snapshot()
    except:
        message = "unable to get the latest snapshot id"
        print(message)
        sent_notification(message)
    try:
        vol_id = create_volume(snap_id)
    except:
        message = "unable to create volume with the latest snapshot"
        print(message)
        sent_notification(message)

    waiter = ec2.get_waiter('volume_available')
    waiter.wait(VolumeIds=[vol_id])
    try:
        attach_volume(vol_id)
    except:
        message = "unable to attach the new volume to the instance"
        print(message)
        sent_notification(message)
    waiter = ec2.get_waiter('volume_in_use')
    waiter.wait(VolumeIds=[vol_id])
    sleep(5)
    try:
        mount_device()
    except Exception as e:
        print(e.message)
        message = e.message
        sent_notification(message)


if __name__ == '__main__':
    main()
