

host_name =  publisher_internal_ip.replace(".", "-")
agent_title = "Replication to " + host_name
author_master = config['author_IP']
agent_description = "Agent that replicates to the publish instance " + host_name
own_internal_ip_input = "http://" + publisher_internal_ip + ":4503/bin/receive?sling:authRequestLogin=1&binaryless=true"
author_transport_password_value = config['author_transport_password']
author_transport_user_value = config['author_transport_user']
author_url_rep_agent = "http://" + author_master + ":4502/etc/replication/agents.author/"  + host_name
author_referer = "http://" + author_master + ":4502/ http://" + author_master + ":4502/etc/replication/agents.author"





keyvalues_replication = {'jcr:primaryType':'cq:Page',
                         'jcr:content/cq:template':'/libs/cq/replication/templates/agent',
                         'jcr:content/sling:resourceType':'cq/replication/components/agent',
                         'jcr:content/serializationType':'durbo',
                         'jcr:content/jcr:title':str(agent_title),
                         'jcr:content/enabled':'true',
                         'jcr:content/jcr:description':str(agent_description),
                         'jcr:content/logLevel':'info',
                         'jcr:content/retryDelay':'60000',
                         'jcr:content/transportUri':str(own_internal_ip_input),
                         'jcr:content/transportPassword':str(author_transport_password_value),
                         'jcr:content/transportUser':str(author_transport_user_value)}



#Setting up Replication in Author  Master
                         while True:
                             try:
                                 rep_request_data=requests.post(str(author_url_rep_agent), data=keyvalues_replication, auth=(author_transport_user_value, author_transport_password_value), headers={'referer': str(author_referer)})
                             except:
                                 errmsg = "Agent Generation on Author Failed"+" : "+ str(publisher_internal_ip)
                                 logging.exception("Unexpected error")
                                 sns.publish(arn, errmsg)
                                 time.sleep(60)
                                 continue
                             break
