from concurrent.futures import ThreadPoolExecutor
import grpc
import sys

# import himsai_pb2 as himsai
# import himsai_pb2_grpc as himsai_grpc

import sample_pb2
import sample_pb2_grpc

from typing import Any, Tuple, Optional
        
class StubProxy:
    """
    A proxy for a gRPC stub, with support for automatic reconnection on failure.
    """
    def __init__(self, real_stub, reconn_func) -> None:
        self._real_stub = real_stub
        self._reconn_func = reconn_func
        
    def update_stub(self, real_stub):
        """
        Update the real stub reference.

        :param real_stub: The new real stub to use.
        """
        self._real_stub = real_stub
    
    def __getattr__(self, name):
        """
        Override the attribute access method to provide a wrapper around stub method calls.
        This allows for reconnection attempts if a method call fails.

        :param name: The name of the attribute being accessed.
        :return: A wrapper function around the real stub method.
        """
        def wrapper(*args, **kwrags):
            max_retries = 3
            attempts = 0
            while attempts < max_retries:
                try:
                    method = getattr(self._real_stub, name)
                    response = method(*args, **kwrags)    
                    return response
                    #return getattr(self._real_stub, name)(*args, **kwrags)
                except Exception as e:
                    attempts +=1
                    #print(f"({attempts}/{max_retries}) ERROR occurred:{e}\nattempting to reconnect ...")      
                    self._reconn_func()
            return None
        return wrapper


class rev_grpc():
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def get_stub(svc):
        if svc in ['client', 'ai_client']:
            stub = sample_pb2_grpc.ClientStub
        elif svc in ['ai', 'ai_service']:
            stub = sample_pb2_grpc.AIStub
        elif svc in ['Netshell', 'netshell', 'nsh']:
            stub = sample_pb2_grpc.NetShellStub
        elif svc in ['test']:
            stub = sample_pb2_grpc.TestStub
        else:
            raise NameError(f"Unknown service type: {svc}")
        return stub

    @staticmethod
    def get_conn(svc: str, addr: str, ca_data: bytes = None):
        """
        Create the connection to the General service server
        """
        
        if ca_data:
            cred = grpc.ssl_channel_credentials(ca_data)
            channel = grpc.secure_channel(addr, cred, options=[('grpc.ssl_target_name_override', 'HAIF')])
        else:
            channel = grpc.insecure_channel(addr)
        stub = rev_grpc.get_stub(svc)(channel)

        return channel, stub

    
    
class conn_info(rev_grpc):
    def __init__(self, name=None, ip=None, port=None, is_conn=True, **kwargs):
        self.name = name
        self.ip = ip
        self.port = port
        self.stub = None
        self.channel = None
        self.dump = None
        
        self.ca_data = kwargs.get('ca_data', None)
        
        if is_conn:
            self.create_conn()
       
    @property
    def addr(self):
        return f"{self.ip}:{self.port}" 

    def set_address(self, ip: str, port: str):
        self.ip = ip
        self.port = port
        
    def create_conn(self):
        self.channel, real_stub = self.get_conn(self.name, self.addr, self.ca_data)

        def reconn():
            self.channel.close()
            self.channel, new_real_stub = self.get_conn(self.name, self.addr, self.ca_data)
            self.stub.update_stub(new_real_stub)
        
        self.stub = StubProxy(real_stub, reconn)

    def test_conn(self, stub=None):
        if stub is None and self.stub is None:
            raise ValueError("Please input a stub")
        elif stub is None and self.stub is not None:
            sb = self.stub
        else:
            sb = stub
            
        resp = sb.Ping(sample_pb2.MessageBool(value=True), timeout=3)
        if resp is None:
            return False
        
        return True

    def __str__(self) -> str:
        return f"{self.addr} {self.stub}"


rpc_stub = rev_grpc.get_stub
rpc_conn = rev_grpc.get_conn

__all__ = [
    'grpc',
    'sample_pb2_grpc',
    'rpc_stub',
    'rpc_conn',
    'rpc_serv',
    'conn_info',
]

if __name__=='__main__':
    client = conn_info('client', '192.168.1.102', '30001')
    