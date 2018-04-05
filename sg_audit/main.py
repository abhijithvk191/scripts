from sys import exit
import boto3
from config import config
from config import ip_list
from netaddr import IPNetwork, IPAddress
import sys
import urllib3
import json
http = urllib3.PoolManager()


def get_vpc_name(vpc):
    """
    Getting vpc name from vpc id and return it
    """
    name = ""
    for i in vpc.tags:
        if 'Key' in i.keys() and i['Key'] == 'Name':
            name = i['Value']
    return name


def get_sg_ids(vpc):
    """
    fetching all security groups from given vpc and return list
    """
    list = [i.id for i in vpc.security_groups.all()]
    return list


def main():
    vpc_id = config['vpc_id']
    session = boto3.Session(profile_name=config['profile'])
    ec2 = session.resource('ec2')
    vpc = ec2.Vpc(vpc_id)
    vpc_name = get_vpc_name(vpc)
    print 'Script is looking for security groups in VPC %s' % vpc_name
    sg_ids = get_sg_ids(vpc)
    print sg_ids
    for sg_id in sg_ids:
        security_group = ec2.SecurityGroup(sg_id)
        name = security_group.group_name
        print "\n\nchecking security group %s - %s" % (sg_id,name)
        rules = security_group.ip_permissions
        for rule in rules:
            if len(rule['IpRanges']) > 0:
                for ip in rule['IpRanges']:
                    ip_check(ip, sg_id)


def ip_check(cidr_block, sg_id):

    count = 0
    for cidr in ip_list:
        count += 1
        if int(count) < int(len(ip_list)):
            if IPNetwork(cidr_block['CidrIp']) in IPNetwork(cidr):
                break
            elif IPNetwork(cidr_block['CidrIp']) in IPNetwork('10.0.0.0/8'):
                break
        elif IPNetwork(cidr_block['CidrIp']) in IPNetwork('172.16.0.0/12'):
            print ("             " + str(cidr_block['CidrIp']) + "  - Private IP range")
            return
        elif IPNetwork(cidr_block['CidrIp']) in IPNetwork('192.168.0.0/16'):
            print ("             " + str(cidr_block['CidrIp']) + "  - Private IP range")
            return
        else:
            """
            #FUNCTION TO GET IP WHOIS DETAILS
            ipaddr = cidr_block['CidrIp'].split("/")[0]
            url = "http://ip-api.com/json/" + ipaddr
            response = http.request('GET', url)
            data = json.loads(response.data)
            if 'as' in data:
                isp = data['as']
                isp1 = data['isp']
                print ("           " + str(cidr_block['CidrIp']) + "  ISP- " + isp + " - " + isp1)
            else:
                print ("           " + str(cidr_block['CidrIp']) + "  - Private IP range")
                return
            """
            print ("             " + str(cidr_block['CidrIp']))
            return


    return

if __name__ == '__main__':
    main()


