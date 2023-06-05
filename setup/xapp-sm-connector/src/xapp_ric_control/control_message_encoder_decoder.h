#ifndef CONTROL_MESSAGE_ENCODER_DECODER_HPP
#define CONTROL_MESSAGE_ENCODER_DECODER_HPP


#include <mdclog/mdclog.h>
#include <vector>

extern "C" {
#include "handover_item.h"
#include "all_handovers.h"
#include "all_handovers_plmn.h"
#include "cell_handovers_list.h"
#include "E2SM-RC-ControlMessage.h"
}


#define MAX_SCTP_BUFFER     100000

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sctp_buffer{
  int length;
  // uint8_t buffer[MAX_SCTP_BUFFER];
  uint8_t* buffer;
} sctp_buffer_t;

typedef struct e2ap_stcp_buffer{
    int msg_length;
    int bytes_consumed;
    uint8_t* msg_buffer;
  }e2ap_stcp_buffer_t;

int e2ap_asn1c_encode_handover_item(CellHandoverItem_t* pdu, unsigned char **buffer);

int e2ap_asn1c_encode_all_handovers_item_list(CellHandoverItemList_t* pdu, unsigned char **buffer);

int e2ap_asn1c_encode_all_handovers(AllHandoversList_t* pdu, unsigned char **buffer);

int e2ap_asn1c_encode_control_message(E2SM_RC_ControlMessage_t* pdu, unsigned char **buffer);

extern struct asn_dec_rval_s e2ap_asn1c_decode_handover_item(CellHandoverItem_t *pdu, enum asn_transfer_syntax syntax, unsigned char *buffer, int len);

extern sctp_buffer_t* gnerate_e2ap_encode_handover_control_message(uint16_t* ue_id, uint16_t* start_position, uint16_t* optimized, size_t size);

extern sctp_buffer_t* generate_e2ap_encode_handover_control_message_plmn(uint16_t* ue_id, uint16_t* start_position, uint16_t* optimized, size_t size, char* plmnId);

extern e2ap_stcp_buffer_t* decode_e2ap_to_xml(uint8_t* buffer, size_t buffSize);

  
#ifdef __cplusplus
}
#endif

#endif