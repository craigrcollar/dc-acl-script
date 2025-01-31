import csv
import ipaddress
from typing import List, Set, Dict, Optional
from collections import defaultdict

def get_user_input() -> Optional[tuple[str, str, List[str]]]:
    """Get customer name, data center ID, and list of node names from user."""
    while True:
        customer_name = input("Enter Customer Name (or 'q' to quit): ").strip()
        
        # Check for quit option
        if customer_name.lower() in ['q', 'quit']:
            return None
        
        data_center_id = input("Enter Data Center ID (or 'q' to quit): ").strip()
        
        # Check for quit option
        if data_center_id.lower() in ['q', 'quit']:
            return None
        
        print("Enter Node Names (one per line, empty line to finish):")
        node_names = []
        while True:
            node = input().strip()
            
            # Check for quit option
            if node.lower() in ['q', 'quit']:
                return None
            
            if not node:
                break
            node_names.append(node)
        
        return customer_name, data_center_id, node_names

def read_inventory_data(filename: str) -> List[tuple[str, str, str]]:
    """Read inventory data from CSV file."""
    inventory_data = []
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            inventory_data.append((
                row['data_center_id'],
                row['node_name'],
                row['ip_address']
            ))
    return inventory_data

def group_and_process_ips(ip_addresses: List[str]) -> tuple[List[str], Set[str]]:
    """
    Group IPs by first three octets and process them according to rules.
    Returns processed IP list and gateways to generate.
    """
    # Group IPs by their first three octets
    prefix_groups: Dict[str, List[str]] = defaultdict(list)
    for ip in ip_addresses:
        first_three_octets = '.'.join(ip.split('.')[:3])
        prefix_groups[first_three_octets].append(ip)
    
    result_ips = []
    gateways_needed = set()
    
    # Process each group
    for prefix, ips in prefix_groups.items():
        if len(ips) == 16:
            # Exactly 16 IPs - summarize to /24
            result_ips.append(f"{prefix}.0/24")
            # No gateway needed for this prefix
        else:
            # Less than 16 IPs - keep original IPs and need gateway
            result_ips.extend(ips)
            gateways_needed.add(prefix)
    
    return result_ips, gateways_needed

def get_matching_ips(inventory_data: List[tuple[str, str, str]], 
                    data_center_id: str, 
                    node_names: List[str]) -> tuple[List[str], Set[str]]:
    """Get IP addresses matching data center ID and node names."""
    matched_ips = [ip for dc, node, ip in inventory_data 
                  if dc == data_center_id and node in node_names]
    
    return group_and_process_ips(matched_ips)

def get_gateway_ips(prefix_groups: Set[str]) -> Set[str]:
    """Generate gateway IPs (*.*.*.254) for specified prefix groups."""
    return {f"{prefix}.254" for prefix in prefix_groups}

def generate_acl_rules(cidr_prefixes: List[ipaddress.IPv4Network], 
                      gateway_ips: Set[str]) -> List[str]:
    """Generate ACL rules with sequence numbers."""
    rules = []
    seq = 100
    
    # Add rules for CIDR prefixes
    for prefix in cidr_prefixes:
        rules.append(f" seq {seq} permit ip {prefix} any")
        seq += 5
    
    # Add rules for gateway IPs
    for gateway in sorted(gateway_ips):
        rules.append(f" seq {seq} permit ip host {gateway} any")
        seq += 5
    
    return rules

def process_template_and_save(template_file: str, 
                            output_file: str, 
                            customer_name: str, 
                            acl_rules: List[str]) -> None:
    """Process template file and save with new ACL rules."""
    try:
        with open(template_file, 'r') as f:
            template_content = f.read()
        
        # Replace customer_name placeholder
        modified_content = template_content.replace('customer_name', customer_name)
        
        # Append ACL rules
        modified_content += '\n' + '\n'.join(acl_rules)
        
        with open(output_file, 'w') as f:
            f.write(modified_content)
            
    except FileNotFoundError:
        print(f"Template file {template_file} not found!")
        return False
    
    return True

def main():
    # Read inventory data once, outside the main loop
    try:
        inventory_data = read_inventory_data('data_center-inventory.csv')
    except FileNotFoundError:
        print("Error: data_center-inventory.csv file not found!")
        return
    
    # Main processing loop
    while True:
        # Get user input
        user_input = get_user_input()
        
        # Check if user wants to quit
        if user_input is None:
            print("Exiting script.")
            break
        
        customer_name, data_center_id, node_names = user_input
        
        # Get matching IP addresses and required gateways
        list_of_ips, prefixes_needing_gateways = get_matching_ips(
            inventory_data, data_center_id, node_names)
        
        # Check if any matching IPs found
        if not list_of_ips:
            print(f"No matching IP addresses found for data center {data_center_id} and nodes {node_names}.")
            print("Please re-enter node names or data center ID.\n")
            continue
        
        # Convert IP addresses to IPv4Interface objects
        ip_interfaces = []
        for ip in list_of_ips:
            if '/' not in ip:
                ip = f"{ip}/32"  # Add /32 mask if no CIDR notation
            ip_interfaces.append(ipaddress.IPv4Interface(ip))
        
        # Get gateway IPs only for groups that need them
        gateway_ips = get_gateway_ips(prefixes_needing_gateways)
        
        # Collapse addresses into CIDR prefixes
        cidr_prefixes = list(ipaddress.collapse_addresses(
            [iface.network for iface in ip_interfaces]
        ))
        
        # Generate ACL rules
        acl_rules = generate_acl_rules(cidr_prefixes, gateway_ips)
        
        # Process template and save output
        template_file = f"{data_center_id}_acl_template"
        output_file = f"{customer_name}_acl_in.txt"
        
        success = process_template_and_save(template_file, output_file, customer_name, acl_rules)
        
        if success:
            print(f"\nACL rules generated successfully! Output saved to {output_file}")
        else:
            print("Failed to process template. Please check the template file.")
        
        print("\n")  # Add a blank line for readability between iterations

if __name__ == "__main__":
    main()
