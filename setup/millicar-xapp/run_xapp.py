import logging
from xapp_control import *
import functools 
import os
import transform_xml_to_dict_millicar as transform
import socket
import sctp

def send_optimized_data(socket, encoder_class:RicControlMessageEncoder):
    # @functools.wraps(socket, encoder_class)
    def send_data(ue_ids, initial_assignment, optimized_assignment):
        data_length, data_bytes = encoder_class.encode_result(ue_ids, initial_assignment, optimized_assignment)
        # we could make a check here that data length is identical to received data length from c++ function
        logging.info('Sending back the data with size ..' + str(data_length))
        send_socket(socket, data_bytes)
        # send_socket_bytes(socket, data_bytes)
    return send_data 

def _optimize_and_send_data(transform: transform.XmlToDictDataTransform, sendingDataCallback):
    ## optimization part missing and return vector
    sendingDataCallback([1,2,3,4,5], [0,1,2,2,2], [0,1,0,0,1])
    # Reseting data for the next round
    transform.reset()
    

def main():
    # configure logger and console output
    logging_filename = os.path.join(os.getcwd(), 'xapp-logger.log')
    # logging_filename = '/home/millicar-xapp/xapp-logger.log' # os.path.join(os.getcwd(), )
    logging.basicConfig(level=logging.DEBUG, filename=logging_filename, filemode='a+',
                        format='%(asctime)-15s %(levelname)-8s %(message)s')
    formatter = logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    control_sck = open_control_socket(4200)

    _transform = transform.XmlToDictDataTransform()
    _msg_encoder = RicControlMessageEncoder()
    _send_encoded_data_func = send_optimized_data(control_sck, _msg_encoder)

    while True:
        data_sck = receive_from_socket(control_sck, _msg_encoder)

        if len(data_sck) <= 0:
            if len(data_sck) == 0:
                continue
            else:
                logging.info('Negative value for socket')
                break
        else:
            # logging.info('Received data: ' + data_sck)
            # appending the data to the tranformer
            # _transform.parse_incoming_data(data_sck)
            if isinstance(data_sck, list):
                for _msg in data_sck:
                    # logging.info('Received data: ' + str(_msg))
                    _transform.parse_incoming_data(_msg)
            else:
                # logging.info('Received data: ' + data_sck)
                _transform.parse_incoming_data(data_sck)
            if _transform.can_perform_optimization():
                _optimize_and_send_data(_transform, _send_encoded_data_func)

if __name__ == '__main__':
    # main()
    server = sctp.sctpsocket_tcp(socket.AF_INET)
    # Let's set up a connection:
    server_ip = "0.0.0.0"                                                       
    server.events.clear()                                                                    
    server.bind((server_ip, 46422))                                                    
    server.listen(3)
    control_sck, client_addr = server.accept()
    print('xApp connected: ' + client_addr[0] + ':' + str(client_addr[1])) 
    control_sck.send(b'Hello')
