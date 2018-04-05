import boto3
dynamodb = boto3.client('dynamodb',region_name='ap-south-1')
response =  dynamodb.scan(
    TableName='aem-mlic-autoscaling-mapping',
    ScanFilter={'dependent-ip':{
            'ComparisonOperator':'NULL'
                                },
                'application-type':{
                'AttributeValueList':[{'S':'publisher'}],
                'ComparisonOperator':'EQ'                                    }
                }
                    )
count = response['Count']
items = response['Items']
for item in items:
    print (item)
    response = dynamodb.update_item(
    TableName='aem-mlic-autoscaling-mapping',
    Key={
        'instance-id':item['instance-id']
        },
    AttributeUpdates={'dependent-ip':{
        'Value':{'S':'10.10.10.10'}}}
            )
