config = {
'publisher_asg':'MLIC_Publisher_ASG',
'dispatcher_asg':'MLIC_Dispatcher_ASG',
'sns_arn':'arn:aws:sns:ap-south-1:675013145414:aem-mlic-automation',
'author_transport_user':'admin',
'author_transport_password':'admin',
'author_IP':'10.12.20.116',
'update_conf_script':'/opt/scripts/update_conf.sh',
'BACKUP_MAPPING_TABLE':'aem-mlic-snapshot-mapping',
'dynamodb_table_name':'aem-mlic-autoscaling-mapping',
'publisher_volume_tag':"Mlic_Publisher_/data",
}
