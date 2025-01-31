Claude.ai generated this python script, and I added some customization.

This script generates an SONIC Access List based on user input and outputs it to a text file. The text file can be copy-pasted into the specific switche(s) physical interface or SVI interface.

usage: python3 sonic-acl-generator.py


The scipt requires requires python3
It asks the user for two three pieces of information: the customer name, the Data Center name, and the GPU name.
* customer_name is a test string
* Data Center name follows our standard: ftw1, str1, pyl1. aln1 is not include.
* Node names, in the form of "gxxx". The node name can be copy-pasted from the Customer Onboarding spreadsheet.

The script matches the node-name to the private IP address of the node. It then optimizes the IP addresses into CIDR prefixes, and summarizes to the shortest prefix length. 
For example, for the IP addresses 10.10.10.1, 10.10.10.2, 10.10.10.3, the script will summarize to 10.10.10.0/30. If there are 16 nodes in the list that are all in the same subnet, the script will summarize to a /24. 
The script also appends a permit for each applicable default gateway, as this is necessary. So 10.10.10.254 will be added for the 10.10.10.x subnet(s).
If there are more than one subnet present, each of the subnets are summarized seperately and a gateway is added for each subnet. E.g. 10.10.10.x and 10.10.11.x will get to 10.10.10.255 and 10.10.11.255. 
