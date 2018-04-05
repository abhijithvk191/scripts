import boto3
autoscale = boto3.client('autoscaling')
publisher_response = autoscale.describe_auto_scaling_groups(AutoScalingGroupNames=['IOT-ANALYTICS-DCOS'])
dispatcher_response = autoscale.describe_auto_scaling_groups(AutoScalingGroupNames=['tapeytapey-pre-prod'])
desired_publisher_count = publisher_response['AutoScalingGroups'][0]['DesiredCapacity']
desired_dispatcher_count = dispatcher_response['AutoScalingGroups'][0]['DesiredCapacity']

desired_publisher_count = 1
if (desired_dispatcher_count==desired_publisher_count):
    return("distpatcher")
elif (desired_publisher_count > desired_dispatcher_count):
    return("load")
else:
'''
Write exeption
'''
