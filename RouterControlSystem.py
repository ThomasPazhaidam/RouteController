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
    "RC1": {
        "parent" : "RC1",
        "cost" : 1000
    },
    "RC2": {
        "parent" : "RC2",
        "cost" : 1000
    },
    "RC3": {
        "parent" : "RC3",
        "cost" : 1000
    },
    "RC4": {
        "parent" : "RC4",
        "cost" : 1000
    }
}



#constructor for Route Controller object
class RouteController:
    def __init__(self, identifier, asn, ip, cost=0, bandwidth=0):
        self.identifier = identifier
        self.asn = asn
        self.ip = ip
        self.cost = cost
        self.bandwidth = bandwidth


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

def print_routing_table(dijkstra):
    print("Routing Table:")
    print(f"{'Destination':<12} {'Next Hop':<12} {'Cost':<6} {'Bandwidth':<10}")
    print("-" * 40)  # Print a divider line for clarity
    for destination, info in dijkstra.items():
        # Use dict.get(key, default) to provide a default value for bandwidth if it's not present
        bandwidth = info.get('bandwidth', 'N/A')  # 'N/A' or perhaps 0 or any default you see fit
        print(f"{destination:<12} {info['parent']:<12} {info['cost']:<6} {bandwidth:<10}")

#Initialize UDP server socket
def UdpServer(identifier):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDP_IP = "127.0.0.1"
    identifier_number = int(re.search(r'\d+', identifier).group())
    UDP_PORT = 65000 + identifier_number
    server_socket.bind((UDP_IP, UDP_PORT))
    print("UDP server started on {}:{}".format(UDP_IP, UDP_PORT))
    while True:
        data, addr = server_socket.recvfrom(1024)
        print("Received message from {}: {}".format(addr, data.decode()))
        recv_data = json.loads(data.decode())

        for node in recv_data["dijkstra"].keys():
            new_cost = recv_data["dijkstra"][node]["cost"] + recv_data["cost"]
            new_bandwidth = recv_data["bandwidth"]

            normalized_bandwidth = 1000 / max(new_bandwidth, 1)  

            # Calculate the weighted score for the new path
            new_score = (new_cost * 0.6) + (normalized_bandwidth * 0.4)

            # Calculate the current weighted score for comparison
            current_cost = dijkstra[node]["cost"]
            current_bandwidth = dijkstra[node].get("bandwidth", 1000)  # Use a default value if not set
            normalized_current_bandwidth = 1000 / max(current_bandwidth, 1)
            current_score = (current_cost * 0.6) + (normalized_current_bandwidth * 0.4)

            if new_score < current_score:
                dijkstra[node]["cost"] = new_cost
                dijkstra[node]["bandwidth"] = new_bandwidth  # Store the bandwidth for information
                dijkstra[node]["parent"] = recv_data["local_id"]

        print_routing_table(dijkstra)



def CreateClientAddressList(RCList):
    AddressList = []
    for RC in RCList:
        identifier_number = int(re.search(r'\d+', RC.identifier).group())  # Extract numeric part using regex
        addr = ("127.0.0.1", 65000+identifier_number)
        AddressList.append(addr)
    return AddressList

AddrList = CreateClientAddressList(RCList)

def PeriodicMessages(AddressList, LocalConfig, RCList, DCList):
    dijkstra[LocalConfig.identifier] = {
        "parent" : LocalConfig.identifier,
        "cost" : 0
    }
    #Periodically send RCU Messages
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