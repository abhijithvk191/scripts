#!/bin/bash

ip=$1
conf_home='/data/aem/www/conf/'
conf_name='dispatcher.any'

sed -i "s@/hostname.*@/hostname \"$ip\"@g" $conf_home$conf_name

#restating httpd
/data/aem/httpd/bin/httpd -k restart
