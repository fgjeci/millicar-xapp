import socket
import sctp
# import asn1
# import asn1tools
# from ipso import scenario_creation


_delimiter_bytes = bytes(";;;", 'utf-8')

# open control socket
def open_control_socket(port: int):

    print('Waiting for xApp connection on port ' + str(port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # server = sctp.sctpsocket_tcp(socket.AF_INET)
    # host = socket.gethostname()
    # bind to INADDR_ANY
    server.bind(('', port))
    # server.bind(('0.0.0.0', port))

    server.listen(5)

    control_sck, client_addr = server.accept()
    print('xApp connected: ' + client_addr[0] + ':' + str(client_addr[1]))

    return control_sck


# send through socket
def send_socket(socket, msg: str):
    bytes_num = socket.send(msg.encode('utf-8'))
    print('Socket sent ' + str(bytes_num) + ' bytes')


# receive data from socker
def receive_from_socket(socket): # -> tuple[list[dict], list[dict], list[dict]]:

    ack = 'Indication ACK\n'

    # data = socket.recv(4096)
    # data = socket.recv(41406)
    data = socket.recv(4200)
    # data = socket.recv(7000)

    # measurement_encoded_bytes, assign_encoded_bytes, resources_encoded_bytes  = data.split(_delimiter_bytes)

    # try:
    #     # data = data.decode('utf-8')
    #     # data = scenario_creation.decode_measurements_data(data)
    #     gnbMesurements = scenario_creation.decode_measurements_data(measurement_encoded_bytes)
    #     gnbAssignments = scenario_creation.decode_assignment_data(assign_encoded_bytes)
    #     gnbResources = scenario_creation.decode_gnb_resources_data(resources_encoded_bytes)
    # except UnicodeDecodeError:
    #     return [], [], []

    # return gnbMesurements, gnbAssignments, gnbResources

    if data != b'':
        # print("Data received ")
        print(data)
        # decoder.start(data)
        # tag, value = decoder.read()

        # print(tag)
        # print(value)

    # decoder = asn1.Decoder()
    # _asn1 = asn1tools.compile_files('e2sm-kpm-rc.asn', codec='per')
    # _data_dict =  _asn1.decode("E2SM-KPM-ActionDefinition", data)
    # print(_data_dict)

    # print(data)

    

    try:
        data = data.decode('utf-8')
    except UnicodeDecodeError:
        return ''

    if ack in data:
        data = data[len(ack):]

    if len(data) > 0:
        # print("Received: ", str(data))

        return data.strip()
    else:
        return ''

