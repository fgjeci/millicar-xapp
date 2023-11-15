import socket
# import sctp
# import asn1
# import asn1tools
# from ipso import scenario_creation
from ctrl_msg_encoder_decoder import RicControlMessageEncoder


_delimiter_bytes = bytes(";;;", 'utf-8')

# open control socket
def open_control_socket(port: int):

    print('Waiting for xApp connection on port ' + str(port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # server = sctp.sctpsocket_tcp(socket.AF_INET)
    # host = socket.gethostname()
    # bind to INADDR_ANY
    # port = 37423
    server.bind(('', port))
    # server.bind(('0.0.0.0', port))

    server.listen(5)

    control_sck, client_addr = server.accept()
    print('xApp connected: ' + client_addr[0] + ':' + str(client_addr[1]))

    return control_sck


# send through socket
def send_socket(socket, msg: str):
    bytes_num = socket.send(msg)
    # bytes_num = socket.send(msg.encode('utf-8'))
    print('Socket sent ' + str(bytes_num) + ' bytes')


# receive data from socker
def receive_from_socket(socket, ric_encoder: RicControlMessageEncoder): # -> tuple[list[dict], list[dict], list[dict]]:

    ack = 'Indication ACK\n'

    data = socket.recv(50000)

    # might happen that multiple messages arrive at the same time
    # thus they are appended one another and the buffer appears as continuos
    # we have to decode the message one by one until there is no more data to the buffer
    _list_of_ric_messages = []
    _input_data_length: int = len(data)
    _total_bytes_consumed = 0
    while(_total_bytes_consumed < _input_data_length):
        # means we have attached messages, so we have to separate them
        # and put in a the list
        _data_buffer, _data_length, _bytes_consumed =  ric_encoder.decode_e2ap_ric_indication_msg(data[_total_bytes_consumed:])
        # print("Data buffer")
        # print(_data_buffer)
        # print("Bytes consumed " + str(_bytes_consumed) + " input data length " + str(_input_data_length))
        if _data_buffer is not None:
            _total_bytes_consumed+=_bytes_consumed
            print("Total bytes consumed " + str(_total_bytes_consumed) + " input length " + str(_input_data_length) + " & bytes consumed " + str(_bytes_consumed))
            # return str(_data_buffer)
            # print(_data_buffer)
            _list_of_ric_messages.append(_data_buffer.decode('utf-8'))
        else:
            break
    if len(_list_of_ric_messages) > 0:
        return _list_of_ric_messages

    try:
        data = data.decode('utf-8')
    except UnicodeDecodeError:
        return ''

    if ack in data:
        data = data[len(ack):]

    if len(data) > 0:
        return data.strip()
    else:
        return ''

