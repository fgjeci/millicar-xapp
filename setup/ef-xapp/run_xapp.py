import logging
from xapp_control import *
import os
import transform_xml_to_dict as transform
import time, threading
# from threading import Thread
from ipso.trasform_pre_optimize import EfAssignDataPreparation
from ipso.greddy_formulation import GreedyFormulation
from ipso.ipso_formulation import IntegerPSO
from ctrl_msg_encoder_decoder import RicControlMessageEncoder

# _data_to_send_back = '<E2AP-PDU><initiatingMessage><procedureCode>5</procedureCode><criticality><ignore/></criticality><value><RICindication><protocolIEs><RICindication-IEs><id>29</id><criticality><reject/></criticality><value><RICrequestID><ricRequestorID>24</ricRequestorID><ricInstanceID>0</ricInstanceID></RICrequestID></value></RICindication-IEs><RICindication-IEs><id>5</id><criticality><reject/></criticality><value><RANfunctionID>200</RANfunctionID></value></RICindication-IEs><RICindication-IEs><id>15</id><criticality><reject/></criticality><value><RICactionID>1</RICactionID></value></RICindication-IEs><RICindication-IEs><id>27</id><criticality><reject/></criticality><value><RICindicationSN>1</RICindicationSN></value></RICindication-IEs><RICindication-IEs><id>28</id><criticality><reject/></criticality><value><RICindicationType><report/></RICindicationType></value></RICindication-IEs><RICindication-IEs><id>25</id><criticality><reject/></criticality><value><RICindicationHeader>\n                                00 00 00 01 87 33 BA 70 0F 00 31 31 31 50 33 00 \n                                B4 A6\n                            </RICindicationHeader></value></RICindication-IEs><RICindication-IEs><id>26</id><criticality><reject/></criticality><value><RICindicationMessage>\n                                10 A0 00 20 31 31 31 00 00 60 00 00 00 00 00 00 \n                                00 00 00 01 40 05 30 30 30 30 33 00 40 05 30 30 \n                                30 30 35 00\n                            </RICindicationMessage></value></RICindication-IEs><RICindication-IEs><id>20</id><criticality><reject/></criticality><value><RICcallProcessID>63 70 69 64</RICcallProcessID></value></RICindication-IEs></protocolIEs></RICindication></value></initiatingMessage><E2SM-KPM-IndicationHeader><indicationHeader-Format1><collectionStartTime>00 00 01 87 33 BA 70 0F</collectionStartTime><id-GlobalE2node-ID><gNB><global-gNB-ID><plmn-id>31 31 31</plmn-id><gnb-id><gnb-ID>33 00 B4 A6\n                        </gnb-ID></gnb-id></global-gNB-ID></gNB></id-GlobalE2node-ID></indicationHeader-Format1></E2SM-KPM-IndicationHeader><E2SM-KPM-IndicationMessage><indicationMessage-Format1><pm-Containers><PM-Containers-Item><performanceContainer><oCU-UP><pf-ContainerList><PF-ContainerListItem><interface-type><x2-u/></interface-type><o-CU-UP-PM-Container><plmnList><PlmnID-Item><pLMN-Identity>31 31 31</pLMN-Identity><cu-UP-PM-EPC><perQCIReportList-cuup><PerQCIReportListItemFormat><drbqci>0</drbqci><pDCPBytesDL>0</pDCPBytesDL><pDCPBytesUL>0</pDCPBytesUL></PerQCIReportListItemFormat></perQCIReportList-cuup></cu-UP-PM-EPC></PlmnID-Item></plmnList></o-CU-UP-PM-Container></PF-ContainerListItem></pf-ContainerList></oCU-UP></performanceContainer></PM-Containers-Item></pm-Containers><cellObjectID/><list-of-matched-UEs><PerUE-PM-Item><ueId>30 30 30 30 33</ueId><list-of-PM-Information/></PerUE-PM-Item><PerUE-PM-Item><ueId>30 30 30 30 35</ueId><list-of-PM-Information/></PerUE-PM-Item></list-of-matched-UEs></indicationMessage-Format1></E2SM-KPM-IndicationMessage></E2AP-PDU>'

# _data_to_send_back = "Hello back from xapp!"

def send_optimized_data(socket, encoder_class:RicControlMessageEncoder):
    def send_data(ue_ids, initial_assignment, optimized_assignment):
        data_length, data_bytes = encoder_class.encode_result(ue_ids, initial_assignment, optimized_assignment)
        # we could make a check here that data length is identical to received data length from c++ function
        logging.info('Sending back the data: ')
        send_socket(socket, data_bytes)
    return send_data

def _optimize_and_send_data(transform: transform.XmlToDictDataTransform, sendingDataCallback):
    _pre_optimize_data = EfAssignDataPreparation(assignments=transform.assignments, 
                                                            measurements=transform.measurements,
                                                            gnbAvailableResources=transform.gnb_resources)
    
    greedy = GreedyFormulation(allUsers=_pre_optimize_data.allImsi, mcsTable=_pre_optimize_data.mcsTable,
                                          gnbResources=_pre_optimize_data.gnbResources, startingAssignment=_pre_optimize_data.assignmentsTable)
    

    _optimized_assign_list = greedy.optimize()

    # return the resulting of optimization
    # return  _pre_optimize_data.allImsi, _pre_optimize_data.assignmentsArray, _optimized_assign_list
    sendingDataCallback(_pre_optimize_data.allImsi, _pre_optimize_data.assignmentsArray, _optimized_assign_list)


def main():
    # configure logger and console output
    # logging_filename = os.path.join(os.getcwd(), 'xapp-logger.log')
    logging_filename = os.path.join(os.getcwd(), '/home/xapp-logger.log')
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
    

    while True:
        data_sck = receive_from_socket(control_sck)

        if len(data_sck) <= 0:
            if len(data_sck) == 0:
                continue
            else:
                logging.info('Negative value for socket')
                break
        else:
            logging.info('Received data: ' + repr(data_sck))
            # appending the data to the tranformer
            _transform.append_msg(repr(data_sck))
            # have to decide what to do next; when to start optimizing
            # one option might be to wait for a certain time and eventually start doing the optimization
            # optimize after 10 ms and send the result
            _optimizer_timer = threading.Timer(interval=0.01, function=_optimize_and_send_data, args=(_transform, send_optimized_data(control_sck, _msg_encoder)))
            _optimizer_timer.start()

        # logging.info('Sending back the data: ' + repr(_data_to_send_back))
        # send_socket(control_sck, _data_to_send_back)


if __name__ == '__main__':
    main()

