from sys import exit
from config import config

import boto3

import networkx as nx
import matplotlib.pyplot as plt


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

def get_sg_name(ec2,s_id):
    """
    Get security group name from security group id and return name
    """
    name = ""
    try:
        security_group = ec2.SecurityGroup(s_id)
        # name = security_group.description
        name = security_group.group_name
    except:
        name = s_id

    return name

def get_edges_sg(ec2,sg_id,sg_ids_all):
    """
    with security group fetching the all connected security groups and,
    check if security group is opened for 0.0.0.0/0
    """
    security_group = ec2.SecurityGroup(sg_id)
    asso_sgs = []
    rules = security_group.ip_permissions
    colours = False
    for rule in rules:
        if len(rule['UserIdGroupPairs']) > 0:
            for s in rule['UserIdGroupPairs']:
                if s['GroupId'] in sg_ids_all:
                    asso_sgs.append(s['GroupId'])

        if len(rule['IpRanges']) > 0:
            for ip in rule['IpRanges']:
                if ip['CidrIp'] == '0.0.0.0/0':
                    colours = True
    return asso_sgs,colours

def main():
    """
    Programe main, with all sg details drawing the network graph
    """
    vpc_id = config['vpc_id']
    session = boto3.Session(profile_name=config['profile'])
    ec2 = session.resource('ec2')
    vpc = ec2.Vpc(vpc_id)
    vpc_name = get_vpc_name(vpc)

    print 'Script is looking for VPC %s' % vpc_name

    sg_ids = get_sg_ids(vpc)
    if len(sg_ids) > 0:
        print 'Found %d sgs'%len(sg_ids)
        print sg_ids
    else:
        print "Didn't find any sgs. Exiting"
        exit()

    sg_names = []
    for i in sg_ids:
        sg_names.append(get_sg_name(ec2,i))

    g = nx.DiGraph()
    g.add_nodes_from(sg_names)
    node_cols = {}

    for id in sg_ids:
        id_name = get_sg_name(ec2,id)
        edges,cols = get_edges_sg(ec2,id,sg_ids)
        if cols:
            # node_cols.append('g')
            node_cols[id_name] = 'r'
        else:
            node_cols[id_name] = 'g'
        if len(edges)>0:
            for e in edges:
                e_name = get_sg_name(ec2,e)
                g.add_edge(e_name,id_name)

    tmp_cls = []
    for node in g:
        tmp_cls.append(node_cols[str(node)])

    nx.draw(g, with_labels=True, node_size=2500,node_color=tmp_cls)
    plt.draw()
    plt.show()

if __name__ == '__main__':
    main()
