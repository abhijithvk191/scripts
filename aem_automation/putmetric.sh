#!/bin/bash -x
export TZ=UTC

#check current time and time one min ago

time_one_minute_ago=`date --date='6 minute ago' +%T`
date_one_min_ago=`date --date='6 minute ago' +%F`
current_time=`date --date='5 minute ago' +%T`
current_date=`date --date='5 minute ago' +%F`
datetime=($current_date"T"$current_time)
echo $datetime
datetime_one_minute_ago=($date_one_min_ago"T"$time_one_minute_ago)
echo $datetime_one_minute_ago

publisher_asg='MLIC_Publisher_ASG'
dispatcher_asg='MLIC_Dispatcher_ASG'
cpu_threshold=30
desired_count=1

#Publisher autoscale CPU (in percent)

publisher_cpu_percentage=`aws cloudwatch get-metric-statistics --metric-name CPUUtilization --start-time $datetime_one_minute_ago --end-time $datetime --period 60 --namespace AWS/EC2 --statistics Average --dimensions Name=AutoScalingGroupName,Value=$publisher_asg | grep Average | awk '{print $2}' | tr -d ,`

#Dispatcher autoscale CPU (in percent)

dispatcher_cpu_percentage=`aws cloudwatch get-metric-statistics --metric-name CPUUtilization --start-time $datetime_one_minute_ago --end-time $datetime --period 60 --namespace AWS/EC2 --statistics Average --dimensions Name=AutoScalingGroupName,Value=$dispatcher_asg | grep Average | awk '{print $2}' | tr -d ,`

#Check publisher desired count

#Publisher_desired=`aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name $publisher_asg | grep DesiredCapacity | awk '{print $2}' | tr -d ,`
Publisher_desired=`aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name $publisher_asg | python -c "import sys, json; print json.load(sys.stdin)['AutoScalingGroups'][0]['DesiredCapacity']"`

#Check Dispatcher desired count

#dispatcher_desired=`aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name $dispatcher_asg | grep DesiredCapacity | awk '{print $2}' | tr -d ,`
dispatcher_desired=`aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name $dispatcher_asg | python -c "import sys, json; print json.load(sys.stdin)['AutoScalingGroups'][0]['DesiredCapacity']"`

#rounding publisher and dispatcher CPU from float to int

publisher_cpu_percentage_round=`printf '%.*f\n' 0 $publisher_cpu_percentage`

dispatcher_cpu_percentage_round=`printf '%.*f\n' 0 $dispatcher_cpu_percentage`

echo $publisher_cpu_percentage_round $dispatcher_cpu_percentage_round $dispatcher_desired $Publisher_desired

#If CPU of Publisher and Dispatcher greater than 70 and desired count of both publisher and dispatcher greater than 2, create custom metric 1 for downscale

if [ $publisher_cpu_percentage_round -lt $cpu_threshold ] && [ $dispatcher_cpu_percentage_round -lt $cpu_threshold ] && [ $dispatcher_desired -gt $desired_count ] && [ $Publisher_desired -gt $desired_count ]; then

   aws cloudwatch put-metric-data --metric-name Downscale --namespace MLICAutomation --storage-resolution 1 --unit Count --value 1

else

   aws cloudwatch put-metric-data --metric-name Downscale --namespace MLICAutomation --storage-resolution 1 --unit Count --value 0

fi

