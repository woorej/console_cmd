from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import time

class MyListener(ServiceListener):
    def __init__(self):
        self.services = []
        
    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str):
        info = zeroconf.get_service_info(service_type, name)
        addr, port = info.parsed_addresses()[0], info.port
        if info:
            #print(f"Service {name} added, addr: {addr}:{port}")
            self.services.append((name, addr, port))
            
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        #print(f"Service {name} removed")
        self.services = [service for service in self.services if service[0] != name]
        
        
def discover_services(service_type: str= "_mgmt._udp.local.", timeout: int=3, max_attempts: int=3):
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, service_type, listener)
    attempts = 0
    
    while attempts < max_attempts:
        print(f"({attempts+1}/{max_attempts}) Searching...")
        time.sleep(timeout)
        
        if listener.services:
            break
        
        attempts += 1
        
        
    zeroconf.close()
    
    return listener.services

def discover_service(service_type: str= "_mgmt._udp.local.", timeout: int=3):
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, service_type, listener)
        
    print(f"Searching...")
    time.sleep(timeout)
        
    zeroconf.close()
    
    return listener.services

if __name__ == "__main__":
    discovered_services = discover_services()
    
    if discovered_services:
        for name, addr, port in discovered_services:
            ip_and_port = f"{addr}:{port}"
            print(f"Discovered service: {name} at {ip_and_port}")
    else:
        print("No services discovered.")
