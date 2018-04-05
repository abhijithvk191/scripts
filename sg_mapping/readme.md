# Security Group Mapping

This script will look through the vpc's security groups and will find the relation b/w them.
# Usage

You can specify the profile to call vpc settings and vpc id in config file

### Run command

``` python
/usr/bin/python main.py

```


### Output

You can see the network graph of security group mapping.


###Colours indication

>Red :- sg is publically open ( 0.0.0.0/0)

>Green :- normal sg 


PS, Peered security settings will not disply in graph.

