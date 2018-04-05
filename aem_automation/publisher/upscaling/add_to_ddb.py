import boto3
dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
response = dynamodb.put_item(
    TableName='aem-mlic-autoscaling-mapping',
    Item={
        'instance-id':{'S':'i-0011f00bf6f7abda3'},
        'application-type':{'S':'publisher'},
        }
    )
