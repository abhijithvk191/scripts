import boto3
autoscale = boto3.client('autoscaling')
publisher_response = autoscale.describe_auto_scaling_groups(AutoScalingGroupNames=['IOT-ANALYTICS-DCOS'])
current_count = publisher_response
