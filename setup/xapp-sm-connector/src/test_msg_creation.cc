#include <iostream>
#include <xapp_ric_control/control_message_encoder_decoder.h>

int main(){
    // std::cout << "Hello there " <<std::endl;
    std::vector<uint16_t> ue_id_vec = {22, 23, 24, 25, 26, 27, 28, 29, 30};
    std::vector<uint16_t> start_position_vec = {0, 7, 2, 0, 18, 17, 17, 1, 5};
    std::vector<uint16_t> end_position_vec = {1, 6, 2, 1, 18, 15, 16, 0, 3};
    uint16_t* ue_id;
    uint16_t* start_position;
    uint16_t* end_position;
    size_t length; 
    sctp_buffer_t* result;
    const char* plmnId = "111";
    // result = gnerate_e2ap_encode_handover_control_message(ue_id, start_position, end_position, length);
    result = generate_e2ap_encode_handover_control_message_plmn(ue_id, start_position, end_position, length, plmnId);

    std::cout << "Lenght " << result->length << std::endl;
}