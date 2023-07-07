import socket
from ctrl_msg_encoder_decoder import RicControlMessageEncoder

_delimiter_bytes = bytes(";;;", 'utf-8')

global _buffer 
_buffer = ""

# open control socket
def open_control_socket(port: int):

    print('Waiting for xApp connection on port ' + str(port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(('', port))

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
    global _buffer

    data = socket.recv(20000)

    try:
        data = data.decode('utf-8')
        _buffer += data.replace('\x00','').strip()
        # print(_buffer)
        
    except UnicodeDecodeError:
        return ''

    if ack in data:
        data = data[len(ack):]

    if len(_buffer) > 0:

        # print(_buffer) # .strip('\t')[:200]
        _open_tag_pos = _buffer.find('<message>', 0)
        _close_tag_pos = _buffer.find('</message>', 0)
        # print("Open pos " + str(_open_tag_pos) + " close pos " + str(_close_tag_pos))
        if ((_open_tag_pos!=-1) & (_close_tag_pos!=-1)):
            _complete_msg = _buffer[_open_tag_pos: _close_tag_pos+10]
            _buffer = _buffer[_close_tag_pos+10:]
            return _complete_msg
        else:
            return ''
    else:
        return ''

