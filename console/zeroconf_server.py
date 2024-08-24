from zeroconf import ServiceInfo, Zeroconf
import socket
import threading

service_event = threading.Event()

def advertise_service(ip: str, port: int, identifier="SVC_BroadCast", svc_type="_mgmt._udp.local."):
    service_name = identifier # identifier
    service_type = svc_type # _{svc_name}._udp.local
    # The IP and port number to be provieded if found through the identifier
    # The server operates Avahi on port 5353 by default
    # The Port number is for transmitting information if found through the identifier  
    service_port = port
    service_ip = ip

    service_info = ServiceInfo(
        service_type,
        f"{service_name}.{service_type}",
        addresses=[socket.inet_aton(service_ip)],
        port=service_port,
        properties={},
    )

    zeroconf = Zeroconf()
    print(f"Registering service {service_name}")
    zeroconf.register_service(service_info)

    try:
        print("Service is running. Call stop_advertise_service() to exit.")
        service_event.wait()
    finally:
        print("Unregistering...")
        zeroconf.unregister_service(service_info)
        zeroconf.close()

def stop_advertise_service():
    service_event.set()
    print("Service stopping...")


if __name__ == "__main__":
    from zeroconf_server import advertise_service
    from utils import get_ip_address
    
    advertise_service(ip=get_ip_address(), port=1234, identifier="SVC_BroadCast", svc_type="_mgmt._udp.local.")