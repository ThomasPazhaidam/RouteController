import configparser
import socket
import threading
import re
import time
import json
"""
rio added the following data

"""
dijkstra = {
    # "100": {
    #     "parent" : None,
    #     "cost" : 1000
    # },
    # "200": {
    #     "parent" : None,
    #     "cost" : 1000
    # },
    # "300": {
    #     "parent" : None,
    #     "cost" : 1000
    # },
    # "400": {
    #     "parent" : None,
    #     "cost" : 1000
    # }
}



#constructor for Route Controller object
class RouteController:
    def __init__(self, identifier, asn, ip, cost=0, bandwidth=0):
        self.identifier = identifier
        self.asn = asn
        self.ip = ip
        self.cost = cost
        self.bandwidth = bandwidth
        dijkstra[self.identifier] = {
            "parent" : self.identifier,
            "cost" : 0
        }

#constructor for Data Center object
class DataCenter:
    def __init__(self, identifier, bandwidth, cost):
        self.identifier = identifier
        self.bandwidth = bandwidth
        self.cost = cost

#get value for keys from config file
def GetKeyValuePairs(SectionName, KeyName):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config.get(SectionName, KeyName)

#Create Objects for RC and DC
def ParseRouteControllerConfig():
    LocalConfig = RouteController(GetKeyValuePairs('Local Config', 'Identifier'), GetKeyValuePairs('Local Config', 'ASN'), GetKeyValuePairs('Local Config', 'IP'))
    NumConnectedRCs = int(GetKeyValuePairs('Local Config', 'ConnectedRCs'))
    RCList = []
    #get connected RC from config
    for i in range(1, NumConnectedRCs+2): #+2 used here because need to add current RC for total RC count
        RCiD = f"RC{i}"
        if(RCiD!=LocalConfig.identifier):
            RCConfig = RouteController(RCiD, GetKeyValuePairs(RCiD, 'ASN'), GetKeyValuePairs(RCiD, 'IP'), int(GetKeyValuePairs(RCiD, 'Cost')), int(GetKeyValuePairs(RCiD, 'Bandwidth')))
            RCList.append(RCConfig)
    
    #get connected DC from config
    NumConnectedDCs = int(GetKeyValuePairs('Local Config', 'ConnectedDCs'))
    DCList = []
    #get connected RC from config
    for i in range(1, NumConnectedDCs+1):
        DCiD = f"DC{i}"
        DCConfig = DataCenter(DCiD, GetKeyValuePairs(DCiD, 'Bandwidth'), GetKeyValuePairs(DCiD, 'Cost'))
        DCList.append(DCConfig)
    
    return LocalConfig, RCList, DCList, NumConnectedRCs, NumConnectedDCs

LocalConfig, RCList, DCList, NumConnectedRCs, NumConnectedDCs = ParseRouteControllerConfig()

"""
#For Debug

print(f'{LocalConfig.identifier} {LocalConfig.asn} {LocalConfig.bandwidth} {LocalConfig.cost} {LocalConfig.ip}')
for config in RCList:
    print(f'{config.identifier} {config.asn} {config.bandwidth} {config.cost} {config.ip}')

for config in DCList:
    print(f'{config.identifier} {config.cost} {config.bandwidth}')

"""
#Initialize UDP server socket
def UdpServer(identifier):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDP_IP = "127.0.0.1"
    #extract unique number from identifier using regex
    identifier_number = int(re.search(r'\d+', identifier).group())  # Extract numeric part using regex

    UDP_PORT = 65000 + identifier_number
    server_socket.bind((UDP_IP, UDP_PORT))
    print("UDP server started on {}:{}".format(UDP_IP, UDP_PORT))
    while True:
        data, addr = server_socket.recvfrom(1024)
        print("Received message from {}: {}".format(addr, data.decode()))
        """
        parse data gram and use it to calculate shortest path 
        """
        recv_data = json.loads(data.decode())
        print("dijkstra")
        print(dijkstra)
        for node in recv_data["dijkstra"]:
            print("node")
            print(node)
            if node not in dijkstra:
                dijkstra[node] = recv_data["dijkstra"][node]
                dijkstra[node]["cost"] += recv_data["cost"]
            else:
                if dijkstra[node]["cost"] > recv_data["dijkstra"][node]["cost"] + recv_data["cost"]:
                    dijkstra[node] = recv_data["dijkstra"][node] + recv_data["cost"]

        print(dijkstra)


def CreateClientAddressList(RCList):
    AddressList = []
    for RC in RCList:
        identifier_number = int(re.search(r'\d+', RC.identifier).group())  # Extract numeric part using regex
        addr = ("127.0.0.1", 65000+identifier_number)
        AddressList.append(addr)
    return AddressList

AddrList = CreateClientAddressList(RCList)

def PeriodicMessages(AddressList, LocalConfig, RCList, DCList):
    #Periodically send RCU Message
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #build connected DC List
    ConnectedDCString =''
    for DC in DCList:
        ConnectedDCString += f'{DC.identifier},'
    
    while True:
        for i in range(len(AddressList)):
            # message = f"[{LocalConfig.identifier}, {LocalConfig.asn}, {RCList[i].cost}, {RCList[i].bandwidth}, [{ConnectedDCString}]]"
            message_data = {
                "local_id" : LocalConfig.identifier,
                "asn" : LocalConfig.asn,
                "cost" : RCList[i].cost,
                "bandwidth" : RCList[i].bandwidth,
                "DC" : [ConnectedDCString],
                "dijkstra" : dijkstra
            }
            print(message_data)
            message = json.dumps(message_data)
            # message = f"{{\"local_id\" : {LocalConfig.identifier}, \"asn\" : {LocalConfig.asn},\"cost\" : {RCList[i].cost}, \"bandwidth\" : {RCList[i].bandwidth}, \"DC\" : [{ConnectedDCString}], \"dijkstra\" : {dijkstra} }}" 
            try:

                client_socket.sendto(message.encode(), AddressList[i])
                print(f"Data sent from client to server {AddressList[i]}: {message}")
            
            except socket.error as err:
                print(f"Failed to send data from client to server {AddressList[i]}: {err}")

        # Sleep for 180 s
        time.sleep(10)

# Create and start the server thread with inputs
server_thread = threading.Thread(target=UdpServer, args=(LocalConfig.identifier,))
server_thread.start()

# Create a thread for sending messages periodically
message_thread = threading.Thread(target=PeriodicMessages, args=(AddrList, LocalConfig, RCList, DCList))
message_thread.start()