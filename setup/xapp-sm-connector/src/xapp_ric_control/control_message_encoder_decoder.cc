#include <mdclog/mdclog.h>
#include <vector>
#include <iostream>
#include <list>
#include <set>
#include <algorithm>
#include <memory>

#include "control_message_encoder_decoder.h"
// extern "C" {
#include "E2SM-RC-ControlMessage.h"
// }
#include "E2AP-PDU.h"
#include "E2SM-KPM-IndicationMessage.h"
#include "E2SM-KPM-IndicationHeader.h"
#include "RICindication.h"
#include "InitiatingMessage.h"
#include "ProtocolIE-Field.h"

#include "tinyxml2.h"

template<typename T>
std::vector<int> findItems(std::vector<T> const &v, int target) {
    std::vector<int> indices;
    auto it = v.begin();
    while ((it = std::find_if(it, v.end(), [&] (T const &e) { return e == target; }))
        != v.end())
    {
        indices.push_back(std::distance(v.begin(), it)); 
        it++;
    }
    return indices;
}

CellHandoverItem_t* create_handover_item(long ueId, long destinationCellId){
    CellHandoverItem_t* control_message = (CellHandoverItem_t *) calloc(1, sizeof(CellHandoverItem_t));
    control_message->ueId = ueId;
    control_message->destinationCellId = destinationCellId;
    return control_message;
}

CellHandoverItemList_t* create_handover_item_list(std::list<CellHandoverItem_t*> handoverItems){
    CellHandoverItemList_t* cellHandoverList = (CellHandoverItemList_t *) calloc(1, sizeof(CellHandoverItemList_t));
    for (auto it = handoverItems.begin(); it != handoverItems.end(); ++it){
        ASN_SEQUENCE_ADD(&cellHandoverList->list, (*it));
    }
    return cellHandoverList;
}

int e2ap_asn1c_encode_handover_item(CellHandoverItem_t* pdu, unsigned char **buffer)
{
    int len;

    *buffer = NULL;
    assert(pdu != NULL);
    assert(buffer != NULL);

    return aper_encode_to_new_buffer(&asn_DEF_CellHandoverItem, 0, pdu, (void **)buffer);

    // len = aper_encode_to_new_buffer(&asn_DEF_CellHandoverItem, 0, pdu, (void **)buffer);

    if (len < 0) {
        // mdclog_write(MDCLOG_INFO,"[E2AP ASN] Unable to aper encode");
    } else {
        // mdclog_write(MDCLOG_INFO, "[E2AP ASN] Encoded succesfully, encoded size = %d", len);
        xer_fprint(stderr, &asn_DEF_CellHandoverItem, pdu);
    }

    // ASN_STRUCT_RESET(asn_DEF_CellHandoverItem, pdu);
    // ASN_STRUCT_FREE_CONTENTS_ONLY(asn_DEF_CellHandoverItem, pdu);

    // return len;
}

int e2ap_asn1c_encode_all_handovers_item_list(CellHandoverItemList_t* pdu, unsigned char **buffer){
    int len;

    *buffer = NULL;
    assert(pdu != NULL);
    assert(buffer != NULL);

    len = aper_encode_to_new_buffer(&asn_DEF_CellHandoverItemList, 0, pdu, (void **)buffer);

    if (len < 0) {
        // mdclog_write(MDCLOG_INFO,"[E2AP ASN] Unable to aper encode");
    } else {
        // mdclog_write(MDCLOG_INFO, "[E2AP ASN] Encoded succesfully, encoded size = %d", len);
        xer_fprint(stderr, &asn_DEF_CellHandoverItemList, pdu);
    }

    return len;
}

int e2ap_asn1c_encode_cell_handovers(CellHandoverList_t* pdu, unsigned char **buffer)
{
    int len;

    *buffer = NULL;
    assert(pdu != NULL);
    assert(buffer != NULL);

    len = aper_encode_to_new_buffer(&asn_DEF_CellHandoverList, 0, pdu, (void **)buffer);

    if (len < 0) {
        // mdclog_write(MDCLOG_INFO,"[E2AP ASN] Unable to aper encode");
    } else {
        // mdclog_write(MDCLOG_INFO, "[E2AP ASN] Encoded succesfully, encoded size = %d", len);
        xer_fprint(stderr, &asn_DEF_CellHandoverList, pdu);
    }

    return len;
}

int e2ap_asn1c_encode_all_handovers(AllHandoversList_t* pdu, unsigned char **buffer)
{
    int len;

    *buffer = NULL;
    assert(pdu != NULL);
    assert(buffer != NULL);

    len = aper_encode_to_new_buffer(&asn_DEF_AllHandoversList, 0, pdu, (void **)buffer);

    if (len < 0) {
        // mdclog_write(MDCLOG_INFO,"[E2AP ASN] Unable to aper encode");
    } else {
        // mdclog_write(MDCLOG_INFO, "[E2AP ASN] Encoded succesfully, encoded size = %d", len);
        xer_fprint(stderr, &asn_DEF_AllHandoversList, pdu);
    }

    return len;
}

int e2ap_asn1c_encode_control_message(E2SM_RC_ControlMessage_t* pdu, unsigned char **buffer){
    int len;

    *buffer = NULL;
    assert(pdu != NULL);
    assert(buffer != NULL);

    len = aper_encode_to_new_buffer(&asn_DEF_E2SM_RC_ControlMessage, 0, pdu, (void **)buffer);

    if (len < 0) {
        // mdclog_write(MDCLOG_INFO,"[E2AP ASN] Unable to aper encode");
    } else {
        // mdclog_write(MDCLOG_INFO, "[E2AP ASN] Encoded succesfully, encoded size = %d", len);
        xer_fprint(stderr, &asn_DEF_E2SM_RC_ControlMessage, pdu);
    }

    return len;
}

struct asn_dec_rval_s e2ap_asn1c_decode_handover_item(CellHandoverItem_t *pdu, enum asn_transfer_syntax syntax, unsigned char *buffer, int len) {
    asn_dec_rval_t dec_ret;
    assert(buffer != NULL);

    dec_ret = asn_decode(NULL, syntax, &asn_DEF_CellHandoverItem, (void **) &pdu, buffer, len);
    if (dec_ret.code != RC_OK) {
        // mdclog_write(MDCLOG_ERR,"[E2AP ASN] Failed to decode pdu");
        // exit(EXIT_FAILURE);
    } else {
        // mdclog_write(MDCLOG_INFO, "[E2AP ASN] Decoded successfully");
        return dec_ret;
    }
    return dec_ret;
}

e2ap_stcp_buffer_t*
decode_e2ap_to_xml(uint8_t* buffer, size_t buffSize){
    // std::cout << "Buffer length " << buffSize << std::endl;
    // E2AP_PDU_t *pdu = nullptr;
    E2AP_PDU_t *pdu = (E2AP_PDU_t * )calloc(1, sizeof(E2AP_PDU_t));
    uint8_t* buff = (uint8_t *) calloc(1, buffSize);
    memcpy(buff, buffer, buffSize);
    InitiatingMessage_t* initMsg; 
    e2ap_stcp_buffer* data = (e2ap_stcp_buffer *) calloc(1, sizeof(e2ap_stcp_buffer));
    // return data;
    tinyxml2::XMLDocument pduDoc;
	tinyxml2::XMLDocument headerDoc;
	tinyxml2::XMLDocument msgDoc;
    // printf("Entered 1 \n");
    // printf("Buffer %s \n", buff);
	auto retval = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2AP_PDU, (void **) &pdu, (void *)buff, buffSize);
	// auto retval = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2AP_PDU, (void **) &pdu, buffer, buffSize);
    uint8_t idx;
    if (retval.code == RC_OK) {
        // printf("Bytes consumed %s ", std::to_string(retval.consumed).c_str());
        if(pdu->present == E2AP_PDU_PR_initiatingMessage){
            initMsg = pdu->choice.initiatingMessage;
            RICindication_t* ricIndication = &initMsg->value.choice.RICindication;
            for (idx = 0; idx < ricIndication->protocolIEs.list.count; idx++)
            {
                switch(ricIndication->protocolIEs.list.array[idx]->id)
                {
                    case 26:  // RIC indication message
                    {
                        // printf("Entered 3 \n");
                        // break;
                        int payload_size = ricIndication->protocolIEs.list.array[idx]-> \
                                                    value.choice.RICindicationMessage.size;

                        char* payload = (char*) calloc(payload_size, sizeof(char));
                        memcpy(payload, ricIndication->protocolIEs.list.array[idx]-> \
                                                value.choice.RICindicationMessage.buf, payload_size);

                        E2SM_KPM_IndicationMessage_t *descriptor = 0;
                        auto retvalMsgKpm = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2SM_KPM_IndicationMessage, (void **) &descriptor, payload, payload_size);
                        char *printBufferMessage;
                        size_t sizeMessage;
                        FILE *streamMessage = open_memstream(&printBufferMessage, &sizeMessage);
                        xer_fprint(streamMessage, &asn_DEF_E2SM_KPM_IndicationMessage, descriptor);
                        msgDoc.Parse(printBufferMessage);
                        break;
                    }
                    break;
                    case 25:  // RIC indication header
                    {
                        // printf("Entered 4 \n");
                        // break;
                        // std::cout << "Ric indication header at index " << (int)idx << std::endl;
                        int payload_size = ricIndication->protocolIEs.list.array[idx]-> \
                                                    value.choice.RICindicationHeader.size;
                        char* payload = (char*) calloc(payload_size, sizeof(char));
                        memcpy(payload, ricIndication->protocolIEs.list.array[idx]-> \
                                                    value.choice.RICindicationHeader.buf, payload_size);
                        E2SM_KPM_IndicationHeader_t *descriptor = 0;
                        auto retvalMsgKpm = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2SM_KPM_IndicationHeader, (void **) &descriptor, payload, payload_size);
                        char *printBufferHeader;
                        size_t sizeHeader;
                        FILE *streamHeader = open_memstream(&printBufferHeader, &sizeHeader);
                        xer_fprint(streamHeader, &asn_DEF_E2SM_KPM_IndicationHeader, descriptor);
                        headerDoc.Parse(printBufferHeader);
                        break;
                    }
                }
            }
            // printf("Entered 5 \n");
            tinyxml2::XMLElement* mainElement = pduDoc.NewElement("message");
            tinyxml2::XMLNode* headerNode = pduDoc.InsertFirstChild(mainElement->DeepClone(&pduDoc));
            tinyxml2::XMLNode* rootHeader = headerDoc.FirstChild()->DeepClone(&pduDoc); 
            pduDoc.FirstChild()->InsertEndChild(rootHeader);
            tinyxml2::XMLNode* rootMessage = msgDoc.FirstChild()->DeepClone(&pduDoc);
            pduDoc.FirstChild()->InsertEndChild(rootMessage);
            // sending the final
            char* printBufferFinal;
            size_t sizeFinal;
            // printf("Entered 6 \n");
            FILE *streamFinal = open_memstream(&printBufferFinal, &sizeFinal);
            pduDoc.SaveFile(streamFinal, true);
            fflush(streamFinal);
            data->msg_length = sizeFinal; 
            data->bytes_consumed = retval.consumed;
            // printf( "Data length of decoded message %d", data->msg_length); 
            data->msg_buffer = (uint8_t *) calloc(1, data->msg_length);
            memcpy(data->msg_buffer, printBufferFinal, std::min(data->msg_length, MAX_SCTP_BUFFER));
            // printf("Entered 7 \n");
        }
    }
    // printf("Entered 8 \n");
    fflush(stdout);
    return data;
}

sctp_buffer_t* gnerate_e2ap_encode_handover_control_message(uint16_t* ue_id, uint16_t* start_position, uint16_t* optimized, size_t size){
    // default value
    std::string plmn("111");
    std::vector<long> ue_id_vec (size);
    std::vector<long> start_position_vec (size);
    std::vector<long> optimized_vec (size);
    for(int _ind = 0; _ind<size; ++_ind){
        ue_id_vec[_ind] = (ue_id[_ind]);
        start_position_vec[_ind] = (start_position[_ind]);
        optimized_vec[_ind] = (optimized[_ind]);
    }

    std::set<long> sourceCellIdSet;
    for (long x: start_position_vec){
        sourceCellIdSet.insert(x);
    }
    AllHandoversListPlmn_t* allHandoversListPlmn = (AllHandoversListPlmn_t *) calloc(1, sizeof(AllHandoversListPlmn_t));
    AllHandoversList_t* allHandoversList = (AllHandoversList_t *) calloc(1, sizeof(AllHandoversList_t));
    allHandoversListPlmn->allHandoversList = allHandoversList;
    allHandoversListPlmn->plmn_id.buf = (uint8_t *) calloc (1, 3);
    allHandoversListPlmn->plmn_id.size = 3;
    memcpy (allHandoversListPlmn->plmn_id.buf, plmn.c_str (), 3);

    for (long sourceCellId: sourceCellIdSet){
        CellHandoverList_t* cellHandovers = (CellHandoverList_t *) calloc(1, sizeof(CellHandoverList_t));
        cellHandovers->sourceCellId = sourceCellId;
        // find items in the starting vec from the set
        std::vector<int> indices = findItems(start_position_vec, sourceCellId);
        std::list<CellHandoverItem_t*> handoverItems;
        for (int index : indices){
            long _ue_ind = ue_id_vec.at(index);
            long _dst_cell_id = optimized_vec.at(index);
            CellHandoverItem_t* control_message = create_handover_item(_ue_ind, _dst_cell_id);
            handoverItems.push_back(control_message);
        }
        CellHandoverItemList_t* cellHandoverList = create_handover_item_list(handoverItems);
        cellHandovers->cellHandoverItemList = cellHandoverList;
        ASN_SEQUENCE_ADD(&allHandoversList->list, cellHandovers);
    }

    // create E2SM
    // this is to keeep compatability with decoding in ns3
    E2SM_RC_ControlMessage_t* rcControlMessage = (E2SM_RC_ControlMessage_t *) calloc(1, sizeof(E2SM_RC_ControlMessage_t));
    rcControlMessage->present = E2SM_RC_ControlMessage_PR_handoverMessage_Format;
    // rcControlMessage->choice.handoverMessage_Format = allHandoversList;
    rcControlMessage->choice.handoverMessage_Format = allHandoversListPlmn;

    uint8_t *buf;
    sctp_buffer_t* data = (sctp_buffer_t *) calloc(1, sizeof(sctp_buffer_t));

    // data->length = e2ap_asn1c_encode_all_handovers_item_list(cellHandoverList, &buf);
    // data->length = e2ap_asn1c_encode_cell_handovers(cellHandovers, &buf);
    // data->length = e2ap_asn1c_encode_all_handovers(allHandoversList, &buf);
    data->length = e2ap_asn1c_encode_control_message(rcControlMessage, &buf);
    // printf( "Data length %d", data->length);
    data->buffer = (uint8_t *) calloc(1, data->length);
    memcpy(data->buffer, buf, std::min(data->length, MAX_SCTP_BUFFER));
    // data->buffer = buf;
    // printf( "Data length %d", data->length);

    delete allHandoversList;
    return data;
}

sctp_buffer_t* generate_e2ap_encode_handover_control_message_plmn(uint16_t* ue_id, uint16_t* start_position, uint16_t* optimized, size_t size, char* plmnId){
    
    std::string plmn(plmnId);
    // std::cout<< "Plmn " << plmn << std::endl;
    std::vector<long> ue_id_vec (size);
    std::vector<long> start_position_vec (size);
    std::vector<long> optimized_vec (size);
    for(int _ind = 0; _ind<size; ++_ind){
        ue_id_vec[_ind] = (ue_id[_ind]);
        start_position_vec[_ind] = (start_position[_ind]);
        optimized_vec[_ind] = (optimized[_ind]);
    }

    std::set<long> sourceCellIdSet;
    for (long x: start_position_vec){
        sourceCellIdSet.insert(x);
    }

    AllHandoversListPlmn_t* allHandoversListPlmn = (AllHandoversListPlmn_t *) calloc(1, sizeof(AllHandoversListPlmn_t));
    AllHandoversList_t* allHandoversList = (AllHandoversList_t *) calloc(1, sizeof(AllHandoversList_t));
    allHandoversListPlmn->plmn_id.buf = (uint8_t *) calloc (1, 3);
    allHandoversListPlmn->plmn_id.size = 3;
    memcpy (allHandoversListPlmn->plmn_id.buf, plmn.c_str (), 3);

    // memcpy (allHandoversList->plmn_id.buf, plmn.c_str (), 3);

    allHandoversListPlmn->allHandoversList = allHandoversList;

    for (long sourceCellId: sourceCellIdSet){
        CellHandoverList_t* cellHandovers = (CellHandoverList_t *) calloc(1, sizeof(CellHandoverList_t));
        cellHandovers->sourceCellId = sourceCellId;
        // find items in the starting vec from the set
        std::vector<int> indices = findItems(start_position_vec, sourceCellId);
        std::list<CellHandoverItem_t*> handoverItems;
        for (int index : indices){
            long _ue_ind = ue_id_vec.at(index);
            long _dst_cell_id = optimized_vec.at(index);
            CellHandoverItem_t* control_message = create_handover_item(_ue_ind, _dst_cell_id);
            handoverItems.push_back(control_message);
        }
        CellHandoverItemList_t* cellHandoverList = create_handover_item_list(handoverItems);
        cellHandovers->cellHandoverItemList = cellHandoverList;
        ASN_SEQUENCE_ADD(&allHandoversList->list, cellHandovers);
    }

    // create E2SM
    // this is to keeep compatability with decoding in ns3
    E2SM_RC_ControlMessage_t* rcControlMessage = (E2SM_RC_ControlMessage_t *) calloc(1, sizeof(E2SM_RC_ControlMessage_t));
    rcControlMessage->present = E2SM_RC_ControlMessage_PR_handoverMessage_Format;
    // rcControlMessage->choice.handoverMessage_Format = allHandoversList;
    rcControlMessage->choice.handoverMessage_Format = allHandoversListPlmn;

    uint8_t *buf;
    sctp_buffer_t* data = (sctp_buffer_t *) calloc(1, sizeof(sctp_buffer_t));

    // data->length = e2ap_asn1c_encode_all_handovers_item_list(cellHandoverList, &buf);
    // data->length = e2ap_asn1c_encode_cell_handovers(cellHandovers, &buf);
    // data->length = e2ap_asn1c_encode_all_handovers(allHandoversList, &buf);
    data->length = e2ap_asn1c_encode_control_message(rcControlMessage, &buf);
    // printf( "Data length %d", data->length);
    data->buffer = (uint8_t *) calloc(1, data->length);
    memcpy(data->buffer, buf, std::min(data->length, MAX_SCTP_BUFFER));
    // data->buffer = buf;
    // printf( "Data length %d", data->length);

    delete allHandoversListPlmn;
    return data;
}
 