import configparser

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
    
    return LocalConfig, RCList, DCList

LocalConfig, RCList, DCList = ParseRouteControllerConfig()
print(f'{LocalConfig.identifier} {LocalConfig.asn} {LocalConfig.bandwidth} {LocalConfig.cost} {LocalConfig.ip}')
for config in RCList:
    print(f'{config.identifier} {config.asn} {config.bandwidth} {config.cost} {config.ip}')

for config in DCList:
    print(f'{config.identifier} {config.cost} {config.bandwidth}')