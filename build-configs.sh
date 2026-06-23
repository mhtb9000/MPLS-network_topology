#!/bin/bash

cat > p1/frr.conf << 'EOC'
frr version 8.4
frr defaults traditional
hostname p1
service integrated-vtysh-config

interface lo
 ip address 1.1.1.1/32

interface eth1
 ip address 10.0.1.2/30

interface eth2
 ip address 10.0.1.9/30

interface eth3
 ip address 10.0.1.13/30

interface eth4
 ip address 10.0.1.17/30

router ospf
 ospf router-id 1.1.1.1
 network 1.1.1.1/32 area 0
 network 10.0.1.0/24 area 0

line vty
EOC

cat > p2/frr.conf << 'EOC'
frr version 8.4
frr defaults traditional
hostname p2
service integrated-vtysh-config

interface lo
 ip address 2.2.2.2/32

interface eth1
 ip address 10.0.1.6/30

interface eth2
 ip address 10.0.1.10/30

interface eth3
 ip address 10.0.1.21/30

interface eth4
 ip address 10.0.1.25/30

router ospf
 ospf router-id 2.2.2.2
 network 2.2.2.2/32 area 0
 network 10.0.1.0/24 area 0

line vty
EOC

cat > p3/frr.conf << 'EOC'
frr version 8.4
frr defaults traditional
hostname p3
service integrated-vtysh-config

interface lo
 ip address 3.3.3.3/32

interface eth1
 ip address 10.0.1.14/30

interface eth2
 ip address 10.0.1.22/30

interface eth3
 ip address 10.0.1.29/30

router ospf
 ospf router-id 3.3.3.3
 network 3.3.3.3/32 area 0
 network 10.0.1.0/24 area 0

line vty
EOC

cat > p4/frr.conf << 'EOC'
frr version 8.4
frr defaults traditional
hostname p4
service integrated-vtysh-config

interface lo
 ip address 4.4.4.4/32

interface eth1
 ip address 10.0.1.18/30

interface eth2
 ip address 10.0.1.26/30

interface eth3
 ip address 10.0.1.30/30

interface eth4
 ip address 10.0.2.1/30

router ospf
 ospf router-id 4.4.4.4
 network 4.4.4.4/32 area 0
 network 10.0.1.0/24 area 0
 network 10.0.2.0/30 area 0

line vty
EOC

cat > pe1/frr.conf << 'EOC'
frr version 8.4
frr defaults traditional
hostname pe1
service integrated-vtysh-config

interface lo
 ip address 11.11.11.11/32

interface eth2
 ip address 10.0.1.1/30

interface eth3
 ip address 10.0.1.5/30

router ospf
 ospf router-id 11.11.11.11
 network 11.11.11.11/32 area 0
 network 10.0.1.0/24 area 0

line vty
EOC

cat > pe2/frr.conf << 'EOC'
frr version 8.4
frr defaults traditional
hostname pe2
service integrated-vtysh-config

interface lo
 ip address 22.22.22.22/32

interface eth1
 ip address 10.0.2.2/30

router ospf
 ospf router-id 22.22.22.22
 network 22.22.22.22/32 area 0
 network 10.0.2.0/30 area 0

line vty
EOC

echo "Configs generated."
