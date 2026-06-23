import os

# Define node lists
p_nodes = [f"p{i}" for i in range(1, 8)]
pe_nodes = [f"pe{i}" for i in range(1, 7)]
ce_hubs = ["ce-dc", "hub-a", "hub-b", "hub-c", "hub-d"]
gs_nodes = [f"gs{i}" for i in range(1, 17)]

# Links lists
core_links = [
    ("pe1", "eth1", "p1", "eth1"),
    ("p1", "eth2", "p5", "eth1"),
    ("p1", "eth3", "p6", "eth1"),
    ("p1", "eth4", "p2", "eth1"),
    ("p2", "eth2", "p6", "eth3"),
    ("p2", "eth3", "p3", "eth1"),
    ("p3", "eth2", "p4", "eth3"),
    ("p4", "eth1", "p6", "eth4"),
    ("p4", "eth2", "p7", "eth2"),
    ("p5", "eth2", "p6", "eth2"),
    ("p5", "eth3", "p7", "eth1"),
    ("p7", "eth3", "pe2", "eth1"),
    ("p4", "eth4", "pe2", "eth2"),
    ("p3", "eth3", "pe2", "eth3"),
    ("pe3", "eth1", "p5", "eth4"),
    ("pe4", "eth1", "p2", "eth4"),
    ("pe5", "eth1", "p7", "eth4"),
    ("pe6", "eth1", "p3", "eth4"),
]

ce_pe_links = [
    ("ce-dc", "eth1", "pe1", "eth2"),
    ("ce-dc", "eth2", "pe2", "eth4"),
    ("hub-a", "eth1", "pe3", "eth2"),
    ("hub-b", "eth1", "pe4", "eth2"),
    ("hub-c", "eth1", "pe5", "eth2"),
    ("hub-d", "eth1", "pe6", "eth2"),
]

gs_hub_links = [
    ("gs1", "eth1", "hub-a", "eth2"),
    ("gs2", "eth1", "hub-a", "eth3"),
    ("gs3", "eth1", "hub-a", "eth4"),
    ("gs4", "eth1", "hub-a", "eth5"),
    ("gs5", "eth1", "hub-b", "eth2"),
    ("gs6", "eth1", "hub-b", "eth3"),
    ("gs7", "eth1", "hub-b", "eth4"),
    ("gs8", "eth1", "hub-b", "eth5"),
    ("gs9", "eth1", "hub-c", "eth2"),
    ("gs10", "eth1", "hub-c", "eth3"),
    ("gs11", "eth1", "hub-c", "eth4"),
    ("gs12", "eth1", "hub-c", "eth5"),
    ("gs13", "eth1", "hub-d", "eth2"),
    ("gs14", "eth1", "hub-d", "eth3"),
    ("gs15", "eth1", "hub-d", "eth4"),
    ("gs16", "eth1", "hub-d", "eth5"),
]

all_links = core_links + ce_pe_links + gs_hub_links

# Build maps of which interfaces belong to which nodes
node_interfaces = {}
for src, src_intf, dst, dst_intf in all_links:
    if src not in node_interfaces:
        node_interfaces[src] = {}
    if dst not in node_interfaces:
        node_interfaces[dst] = {}
    node_interfaces[src][src_intf] = (dst, dst_intf)
    node_interfaces[dst][dst_intf] = (src, src_intf)

# Loopbacks maps
loopbacks = {}
for i, n in enumerate(p_nodes):
    loopbacks[n] = f"1.1.1.{i+1}"
for i, n in enumerate(pe_nodes):
    loopbacks[n] = f"2.2.2.{i+1}"
for i, n in enumerate(ce_hubs):
    loopbacks[n] = f"3.3.3.{i+1}"

# IP allocations for Core links (Systematically /30 subnets starting from 10.100.1.0/30)
core_ip_allocs = {}
for idx, (src, src_intf, dst, dst_intf) in enumerate(core_links):
    subnet_base = idx * 4
    ip_a = f"10.100.1.{subnet_base + 1}/30"
    ip_b = f"10.100.1.{subnet_base + 2}/30"
    core_ip_allocs[(src, src_intf)] = ip_a
    core_ip_allocs[(dst, dst_intf)] = ip_b

# IP allocations for CE-PE subinterfaces (Systematically /30 subnets for each VRF)
# ce_pe_links indexes:
# 0: ce-dc:eth1 - pe1:eth2
# 1: ce-dc:eth2 - pe2:eth4
# 2: hub-a:eth1 - pe3:eth2
# 3: hub-b:eth1 - pe4:eth2
# 4: hub-c:eth1 - pe5:eth2
# 5: hub-d:eth1 - pe6:eth2
vrfs = {
    "Launch_Ops": {"vlan": 10, "rd": "65001:10", "rt": "65001:10"},
    "Sat_Ops": {"vlan": 20, "rd": "65001:20", "rt": "65001:20"},
    "Tracking": {"vlan": 30, "rd": "65001:30", "rt": "65001:30"},
    "Admin": {"vlan": 40, "rd": "65001:40", "rt": "65001:40"},
}

ce_pe_ip_allocs = {}
for idx, (src, src_intf, dst, dst_intf) in enumerate(ce_pe_links):
    # src is ce, dst is pe
    subnet_base = idx * 4
    ce_pe_ip_allocs[(src, src_intf)] = {}
    ce_pe_ip_allocs[(dst, dst_intf)] = {}
    for vrf_name, vrf_info in vrfs.items():
        vlan = vrf_info["vlan"]
        ip_a = f"172.16.{vlan}.{subnet_base + 1}/30"
        ip_b = f"172.16.{vlan}.{subnet_base + 2}/30"
        ce_pe_ip_allocs[(src, src_intf)][vlan] = ip_a
        ce_pe_ip_allocs[(dst, dst_intf)][vlan] = ip_b

# IP allocations for GS to Hub links
gs_ip_allocs = {}
# gs1 to gs16
for idx, (src, src_intf, dst, dst_intf) in enumerate(gs_hub_links):
    # src is gs, dst is hub
    # gs_idx matches index
    gs_num = idx + 1
    ip_gs = f"192.168.{gs_num}.1/24"
    ip_hub = f"192.168.{gs_num}.254/24"
    gs_ip_allocs[(src, src_intf)] = ip_gs
    gs_ip_allocs[(dst, dst_intf)] = ip_hub

# Ensure output config directories exist
os.makedirs("config", exist_ok=True)

# Generate node files
all_nodes = p_nodes + pe_nodes + ce_hubs + gs_nodes

# Helper to generate daemons file
def write_daemons(node_path, bgp="no", ospf="no", ldp="no", static="yes"):
    content = f"""bgpd={bgp}
ospfd={ospf}
ospf6d=no
ripd=no
ripngd=no
isisd=no
pimd=no
pim6d=no
ldpd={ldp}
nhrpd=no
eigrpd=no
babeld=no
sharpd=no
pbrd=no
bfdd=no
fabricd=no
vrrpd=no
pathd=no

vtysh_enable=yes
zebra_options="  -A 127.0.0.1 -s 90000000"
bgpd_options="   -A 127.0.0.1"
ospfd_options="  -A 127.0.0.1"
ldpd_options="   -A 127.0.0.1"
staticd_options="-A 127.0.0.1"
"""
    with open(os.path.join(node_path, "daemons"), "w") as f:
        f.write(content)

# Process P nodes
for idx, node in enumerate(p_nodes):
    node_path = os.path.join("config", node)
    os.makedirs(node_path, exist_ok=True)
    write_daemons(node_path, bgp="no", ospf="yes", ldp="yes")
    
    # frr.conf
    interfaces_config = []
    # lo
    interfaces_config.append(f"""interface lo
 ip address {loopbacks[node]}/32
!""")
    
    # physical interfaces
    node_ints = node_interfaces.get(node, {})
    for intf in sorted(node_ints.keys()):
        ip_addr = core_ip_allocs.get((node, intf))
        interfaces_config.append(f"""interface {intf}
 ip address {ip_addr}
 ip ospf area 0
!""")
        
    ldp_interfaces = " ".join(sorted(node_ints.keys()))
    label_start = 100000 + (idx + 1) * 10000
    label_end = label_start + 9999
    
    frr_content = f"""frr version 8.4
frr defaults traditional
hostname {node}
service integrated-vtysh-config
!
mpls label dynamic-block {label_start} {label_end}
!
""" + "\n".join(interfaces_config) + f"""
!
router ospf
 ospf router-id {loopbacks[node]}
 network {loopbacks[node]}/32 area 0
 network 10.100.1.0/24 area 0
!
mpls ldp
 router-id {loopbacks[node]}
 !
 address-family ipv4
  discovery transport-address {loopbacks[node]}
  !
""" + "\n".join([f"  interface {intf}" for intf in sorted(node_ints.keys())]) + """
  !
 exit-address-family
!
line vty
!
"""
    with open(os.path.join(node_path, "frr.conf"), "w") as f:
        f.write(frr_content)

# Process PE nodes
for idx, node in enumerate(pe_nodes):
    node_path = os.path.join("config", node)
    os.makedirs(node_path, exist_ok=True)
    write_daemons(node_path, bgp="yes", ospf="yes", ldp="yes")
    
    interfaces_config = []
    # lo
    interfaces_config.append(f"""interface lo
 ip address {loopbacks[node]}/32
!""")
    
    # physical interfaces
    node_ints = node_interfaces.get(node, {})
    core_ints = []
    ce_ints = []
    for intf in sorted(node_ints.keys()):
        target, target_intf = node_ints[intf]
        if target.startswith("p") and not target.startswith("pe"): # core link
            ip_addr = core_ip_allocs.get((node, intf))
            interfaces_config.append(f"""interface {intf}
 ip address {ip_addr}
 ip ospf area 0
!""")
            core_ints.append(intf)
        else: # CE link
            # Parent interface description
            interfaces_config.append(f"""interface {intf}
 description Connection to {target}
!""")
            ce_ints.append((intf, target))
            
            # Subinterfaces in VRFs
            sub_allocs = ce_pe_ip_allocs.get((node, intf), {})
            for vrf_name, vrf_info in vrfs.items():
                vlan = vrf_info["vlan"]
                ip_addr = sub_allocs.get(vlan)
                interfaces_config.append(f"""interface {intf}.{vlan}
 vrf {vrf_name}
 ip address {ip_addr}
!""")
                
    label_start = 200000 + (idx + 1) * 10000
    label_end = label_start + 9999
    
    # Configure PE full mesh neighbors
    bgp_neighbors = []
    for pe_other in pe_nodes:
        if pe_other != node:
            bgp_neighbors.append(f" neighbor {loopbacks[pe_other]} peer-group PE_PEERS")
            
    # Configure VRF Static Routes on PE
    static_routes = []
    for intf, target in ce_ints:
        # target is CE Hub/DC
        if target == "ce-dc":
            # For ce-dc, its loopback is 3.3.3.1
            # We route 3.3.3.1/32 to ce-dc's subinterface IP
            sub_allocs = ce_pe_ip_allocs.get((node, intf), {})
            for vrf_name, vrf_info in vrfs.items():
                vlan = vrf_info["vlan"]
                ce_ip = ce_pe_ip_allocs[(target, node_interfaces[node][intf][1])][vlan].split("/")[0]
                static_routes.append(f"ip route 3.3.3.1/32 {ce_ip} vrf {vrf_name}")
        else:
            # target is hub-a..d
            # hub-a matches 192.168.1..4, hub-b matches 5..8, hub-c matches 9..12, hub-d matches 13..16
            hub_idx = ord(target[-1]) - ord('a') # 0 for a, 1 for b, 2 for c, 3 for d
            start_gs = hub_idx * 4 + 1
            for vrf_idx, (vrf_name, vrf_info) in enumerate(vrfs.items()):
                vlan = vrf_info["vlan"]
                gs_subnet = f"192.168.{start_gs + vrf_idx}.0/24"
                ce_ip = ce_pe_ip_allocs[(target, node_interfaces[node][intf][1])][vlan].split("/")[0]
                static_routes.append(f"ip route {gs_subnet} {ce_ip} vrf {vrf_name}")

    frr_content = f"""frr version 8.4
frr defaults traditional
hostname {node}
service integrated-vtysh-config
!
mpls label dynamic-block {label_start} {label_end}
!
""" + "\n".join(interfaces_config) + f"""
!
router ospf
 ospf router-id {loopbacks[node]}
 network {loopbacks[node]}/32 area 0
 network 10.100.1.0/24 area 0
!
mpls ldp
 router-id {loopbacks[node]}
 !
 address-family ipv4
  discovery transport-address {loopbacks[node]}
  !
""" + "\n".join([f"  interface {intf}" for intf in core_ints]) + f"""
  !
 exit-address-family
!
router bgp 65001
 bgp router-id {loopbacks[node]}
 no bgp default ipv4-unicast
 neighbor PE_PEERS peer-group
 neighbor PE_PEERS remote-as 65001
 neighbor PE_PEERS update-source lo
""" + "\n".join(bgp_neighbors) + f"""
 !
 address-family vpnv4 unicast
  neighbor PE_PEERS activate
 exit-address-family
!
""" + "\n".join([f"""router bgp 65001 vrf {vrf_name}
 rd {vrf_info["rd"]}
 route-target import {vrf_info["rt"]}
 route-target export {vrf_info["rt"]}
 !
 address-family ipv4 unicast
  redistribute connected
  redistribute static
 exit-address-family
!""" for vrf_name, vrf_info in vrfs.items()]) + "\n" + "\n".join(static_routes) + """
!
line vty
!
"""
    with open(os.path.join(node_path, "frr.conf"), "w") as f:
        f.write(frr_content)

# Process CE Hub / DC nodes
for idx, node in enumerate(ce_hubs):
    node_path = os.path.join("config", node)
    os.makedirs(node_path, exist_ok=True)
    write_daemons(node_path, bgp="no", ospf="no", ldp="no", static="yes")
    
    interfaces_config = []
    # lo
    interfaces_config.append(f"""interface lo
 ip address {loopbacks[node]}/32
!""")
    
    # physical interfaces
    node_ints = node_interfaces.get(node, {})
    ce_pe_ints = []
    gs_ints = []
    
    for intf in sorted(node_ints.keys()):
        target, target_intf = node_ints[intf]
        if target.startswith("pe"): # CE-PE interface
            interfaces_config.append(f"""interface {intf}
 description Connection to PE {target}
!""")
            ce_pe_ints.append((intf, target))
            
            # Subinterfaces in VRFs
            sub_allocs = ce_pe_ip_allocs.get((node, intf), {})
            for vrf_name, vrf_info in vrfs.items():
                vlan = vrf_info["vlan"]
                ip_addr = sub_allocs.get(vlan)
                interfaces_config.append(f"""interface {intf}.{vlan}
 vrf {vrf_name}
 ip address {ip_addr}
!""")
        else: # CE-GS interface (GS)
            # Find which VRF it belongs to
            # gs1..4 are Launch, Sat, Tracking, Admin respectively
            # gs5..8 are Launch, Sat, Tracking, Admin etc.
            gs_idx = int(target.replace("gs", ""))
            vrf_idx = (gs_idx - 1) % 4
            vrf_name = list(vrfs.keys())[vrf_idx]
            
            ip_addr = gs_ip_allocs.get((node, intf))
            interfaces_config.append(f"""interface {intf}
 vrf {vrf_name}
 ip address {ip_addr}
!""")
            gs_ints.append((intf, target, vrf_name))

    # Static default routes inside VRFs pointing to the PE node's subinterface IPs
    static_routes = []
    for intf, target in ce_pe_ints:
        # For each VRF, route default traffic to PE's subinterface IP
        for vrf_name, vrf_info in vrfs.items():
            vlan = vrf_info["vlan"]
            pe_ip = ce_pe_ip_allocs[(target, node_interfaces[node][intf][1])][vlan].split("/")[0]
            static_routes.append(f"ip route 0.0.0.0/0 {pe_ip} vrf {vrf_name}")
            
    frr_content = f"""frr version 8.4
frr defaults traditional
hostname {node}
service integrated-vtysh-config
!
""" + "\n".join(interfaces_config) + "\n!\n" + "\n".join(static_routes) + """
!
line vty
!
"""
    with open(os.path.join(node_path, "frr.conf"), "w") as f:
        f.write(frr_content)

# Process GS nodes
for idx, node in enumerate(gs_nodes):
    node_path = os.path.join("config", node)
    os.makedirs(node_path, exist_ok=True)
    write_daemons(node_path, bgp="no", ospf="no", ldp="no", static="yes")
    
    interfaces_config = []
    # GS only has eth1 connecting to hub
    node_ints = node_interfaces.get(node, {})
    intf = "eth1"
    target, target_intf = node_ints[intf]
    
    ip_addr = gs_ip_allocs.get((node, intf))
    interfaces_config.append(f"""interface {intf}
 description Connection to Hub {target}
 ip address {ip_addr}
!""")
    
    hub_ip = gs_ip_allocs[(target, target_intf)].split("/")[0]
    
    frr_content = f"""frr version 8.4
frr defaults traditional
hostname {node}
service integrated-vtysh-config
!
""" + "\n".join(interfaces_config) + f"""
!
ip route 0.0.0.0/0 {hub_ip}
!
line vty
!
"""
    with open(os.path.join(node_path, "frr.conf"), "w") as f:
        f.write(frr_content)

# Generate Containerlab topology file topology.clab.yml
clab_nodes = []

# Core nodes
for node in p_nodes:
    clab_nodes.append(f"""    {node}:
      kind: linux
      image: quay.io/frrouting/frr:10.0.0
      binds:
        - ./config/{node}/daemons:/etc/frr/daemons
        - ./config/{node}/frr.conf:/etc/frr/frr.conf""")

# PE nodes
for node in pe_nodes:
    # Build exec commands for creating VRFs and subinterfaces
    node_ints = node_interfaces[node]
    ce_ints = []
    for intf in sorted(node_ints.keys()):
        target, target_intf = node_ints[intf]
        if not target.startswith("p") or target.startswith("pe"): # CE link
            ce_ints.append(intf)
            
    exec_cmds = [
        "ip link add Launch_Ops type vrf table 10",
        "ip link set Launch_Ops up",
        "ip link add Sat_Ops type vrf table 20",
        "ip link set Sat_Ops up",
        "ip link add Tracking type vrf table 30",
        "ip link set Tracking up",
        "ip link add Admin type vrf table 40",
        "ip link set Admin up"
    ]
    for intf in ce_ints:
        for vrf_name, vrf_info in vrfs.items():
            vlan = vrf_info["vlan"]
            exec_cmds.append(f"ip link add link {intf} name {intf}.{vlan} type vlan id {vlan}")
            exec_cmds.append(f"ip link set {intf}.{vlan} master {vrf_name}")
            exec_cmds.append(f"ip link set {intf}.{vlan} up")
            
    exec_block = "\n".join([f"        - {cmd}" for cmd in exec_cmds])
    clab_nodes.append(f"""    {node}:
      kind: linux
      image: quay.io/frrouting/frr:10.0.0
      binds:
        - ./config/{node}/daemons:/etc/frr/daemons
        - ./config/{node}/frr.conf:/etc/frr/frr.conf
      exec:
{exec_block}""")

# CE Hub nodes
for node in ce_hubs:
    # Build exec commands
    node_ints = node_interfaces[node]
    ce_pe_ints = []
    gs_ints = []
    for intf in sorted(node_ints.keys()):
        target, target_intf = node_ints[intf]
        if target.startswith("pe"):
            ce_pe_ints.append(intf)
        else:
            gs_ints.append((intf, target))
            
    exec_cmds = [
        "ip link add Launch_Ops type vrf table 10",
        "ip link set Launch_Ops up",
        "ip link add Sat_Ops type vrf table 20",
        "ip link set Sat_Ops up",
        "ip link add Tracking type vrf table 30",
        "ip link set Tracking up",
        "ip link add Admin type vrf table 40",
        "ip link set Admin up"
    ]
    for intf in ce_pe_ints:
        for vrf_name, vrf_info in vrfs.items():
            vlan = vrf_info["vlan"]
            exec_cmds.append(f"ip link add link {intf} name {intf}.{vlan} type vlan id {vlan}")
            exec_cmds.append(f"ip link set {intf}.{vlan} master {vrf_name}")
            exec_cmds.append(f"ip link set {intf}.{vlan} up")
            
    for intf, target in gs_ints:
        gs_idx = int(target.replace("gs", ""))
        vrf_idx = (gs_idx - 1) % 4
        vrf_name = list(vrfs.keys())[vrf_idx]
        exec_cmds.append(f"ip link set {intf} master {vrf_name}")
        exec_cmds.append(f"ip link set {intf} up")
        
    exec_block = "\n".join([f"        - {cmd}" for cmd in exec_cmds])
    clab_nodes.append(f"""    {node}:
      kind: linux
      image: quay.io/frrouting/frr:10.0.0
      binds:
        - ./config/{node}/daemons:/etc/frr/daemons
        - ./config/{node}/frr.conf:/etc/frr/frr.conf
      exec:
{exec_block}""")

# GS nodes
for node in gs_nodes:
    clab_nodes.append(f"""    {node}:
      kind: linux
      image: quay.io/frrouting/frr:10.0.0
      binds:
        - ./config/{node}/daemons:/etc/frr/daemons
        - ./config/{node}/frr.conf:/etc/frr/frr.conf""")

# Links config
clab_links = []
for src, src_intf, dst, dst_intf in all_links:
    clab_links.append(f'    - endpoints: ["{src}:{src_intf}", "{dst}:{dst_intf}"]')

clab_content = f"""name: mpls_topology

topology:
  nodes:
""" + "\n".join(clab_nodes) + """

  links:
""" + "\n".join(clab_links) + "\n"

with open("topology.clab.yml", "w") as f:
    f.write(clab_content)

print("All configuration files and topology.clab.yml have been successfully generated!")
