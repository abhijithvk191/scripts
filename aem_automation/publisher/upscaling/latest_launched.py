import boto3
autoscale = boto3.client('autoscaling',region_name='ap-south-1')
ec2 = boto3.client('ec2',region_name='ap-south-1')
activity_list = {}
response = autoscale.describe_scaling_activities(AutoScalingGroupName="IOT-ANALYTICS-DCOS")
for i in response['Activities']:
    if i['Description'].split(':')[0] == "Launching a new EC2 instance":
        activity_list[i['ActivityId']] = i['EndTime']
latest_launch_activity = [k for k, v in sorted(activity_list.items(), key=lambda p: p[1], reverse=True)][0]
latest_launched_instance = (autoscale.describe_scaling_activities(ActivityIds=[latest_launch_activity]))['Activities'][0]['Description']
instance_id = latest_launched_instance.split(':')[1].split(' ')[1]
response = ec2.describe_instances(InstanceIds=[instance_id])
print response
print (instance_id)
