/*
==================================================================================

        Copyright (c) 2019-2020 AT&T Intellectual Property.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
==================================================================================
*/
/*
 * msgs_proc.cc
 * Created on: 2019
 * Author: Ashwin Shridharan, Shraboni Jana
 */


#include "msgs_proc.hpp"
#include <stdio.h>
#include "RICindicationHeader.h"
#include "RICindicationMessage.h"
#include "E2SM-KPM-IndicationHeader-Format1.h"
#include <TimeStamp.h>
#include <GlobalE2node-ID.h>
#include <GlobalE2node-en-gNB-ID.h>
#include <GlobalE2node-ng-eNB-ID.h>
#include <GlobalE2node-eNB-ID.h>
#include <GlobalE2node-gNB-ID.h>
#include <xer_encoder.h>
// #include <BIT_STRING.h>

#include "E2SM-KPM-IndicationMessage-Format1.h"
#include "E2SM-KPM-IndicationMessage.h"

// #include "NRCGI.h"
#include "PM-Containers-Item.h"
#include "PF-Container.h"
#include "PF-ContainerListItem.h"
#include "OCUUP-PF-Container.h"
#include "OCUCP-PF-Container.h"
#include "ODU-PF-Container.h"
#include "CellResourceReportListItem.h"
#include "ServedPlmnPerCellListItem.h"
#include "PlmnID-Item.h"
// #include "PLMN-Identity.h"
#include "EPC-DU-PM-Container.h"
#include "EPC-CUUP-PM-Format.h"
#include "PerQCIReportListItem.h"
#include "PerQCIReportListItemFormat.h"
#include "NRCellIdentity.h"
#include "MeasurementTypeName.h"
#include "MeasurementValue.h"
#include "PM-Info-Item.h"

#include "L3-RRC-Measurements.h"
#include "E2SM-KPM-IndicationHeader.h"
// #include "tinyxml2.h"
#include "../xapp-tinyxml2/tinyxml2.h"



using namespace tinyxml2;

bool XappMsgHandler::encode_subscription_delete_request(unsigned char* buffer, size_t *buf_len){

	subscription_helper sub_helper;
	sub_helper.set_request(0); // requirement of subscription manager ... ?
	sub_helper.set_function_id(0);

	subscription_delete e2ap_sub_req_del;

	  // generate the delete request pdu

	  bool res = e2ap_sub_req_del.encode_e2ap_subscription(&buffer[0], buf_len, sub_helper);
	  if(! res){
	    mdclog_write(MDCLOG_ERR, "%s, %d: Error encoding subscription delete request pdu. Reason = %s", __FILE__, __LINE__, e2ap_sub_req_del.get_error().c_str());
	    return false;
	  }

	return true;

}

bool XappMsgHandler::decode_subscription_response(unsigned char* data_buf, size_t data_size){

	subscription_helper subhelper;
	subscription_response subresponse;
	bool res = true;
	E2AP_PDU_t *e2pdu = 0;

	asn_dec_rval_t rval;

	ASN_STRUCT_RESET(asn_DEF_E2AP_PDU, e2pdu);

	rval = asn_decode(0,ATS_ALIGNED_BASIC_PER, &asn_DEF_E2AP_PDU, (void**)&e2pdu, data_buf, data_size);
	switch(rval.code)
	{
		case RC_OK:
			   //Put in Subscription Response Object.
			   //asn_fprint(stdout, &asn_DEF_E2AP_PDU, e2pdu);
			   break;
		case RC_WMORE:
				mdclog_write(MDCLOG_ERR, "RC_WMORE");
				res = false;
				break;
		case RC_FAIL:
				mdclog_write(MDCLOG_ERR, "RC_FAIL");
				res = false;
				break;
		default:
				break;
	 }
	ASN_STRUCT_FREE(asn_DEF_E2AP_PDU, e2pdu);
	return res;

}

bool  XappMsgHandler::a1_policy_handler(char * message, int *message_len, a1_policy_helper &helper){

  rapidjson::Document doc;
  if (doc.Parse(message).HasParseError()){
    mdclog_write(MDCLOG_ERR, "Error: %s, %d :: Could not decode A1 JSON message %s\n", __FILE__, __LINE__, message);
    return false;
  }

  //Extract Operation
  rapidjson::Pointer temp1("/operation");
    rapidjson::Value * ref1 = temp1.Get(doc);
    if (ref1 == NULL){
      mdclog_write(MDCLOG_ERR, "Error : %s, %d:: Could not extract policy type id from %s\n", __FILE__, __LINE__, message);
      return false;
    }

   helper.operation = ref1->GetString();

  // Extract policy id type
  rapidjson::Pointer temp2("/policy_type_id");
  rapidjson::Value * ref2 = temp2.Get(doc);
  if (ref2 == NULL){
    mdclog_write(MDCLOG_ERR, "Error : %s, %d:: Could not extract policy type id from %s\n", __FILE__, __LINE__, message);
    return false;
  }
   //helper.policy_type_id = ref2->GetString();
    helper.policy_type_id = to_string(ref2->GetInt());

    // Extract policy instance id
    rapidjson::Pointer temp("/policy_instance_id");
    rapidjson::Value * ref = temp.Get(doc);
    if (ref == NULL){
      mdclog_write(MDCLOG_ERR, "Error : %s, %d:: Could not extract policy type id from %s\n", __FILE__, __LINE__, message);
      return false;
    }
    helper.policy_instance_id = ref->GetString();

    if (helper.policy_type_id == "1" && helper.operation == "CREATE"){
    	helper.status = "OK";
    	Document::AllocatorType& alloc = doc.GetAllocator();

    	Value handler_id;
    	handler_id.SetString(helper.handler_id.c_str(), helper.handler_id.length(), alloc);

    	Value status;
    	status.SetString(helper.status.c_str(), helper.status.length(), alloc);


    	doc.AddMember("handler_id", handler_id, alloc);
    	doc.AddMember("status",status, alloc);
    	doc.RemoveMember("operation");
    	StringBuffer buffer;
    	Writer<StringBuffer> writer(buffer);
    	doc.Accept(writer);
    	strncpy(message,buffer.GetString(), buffer.GetLength());
    	*message_len = buffer.GetLength();
    	return true;
    }
    return false;
 }


//For processing received messages.XappMsgHandler should mention if resend is required or not.
void XappMsgHandler::operator()(rmr_mbuf_t *message, bool *resend){
	mdclog_write(MDCLOG_INFO, "Received RIC message");
	if (message->len > MAX_RMR_RECV_SIZE){
		mdclog_write(MDCLOG_ERR, "Error : %s, %d, RMR message larger than %d. Ignoring ...", __FILE__, __LINE__, MAX_RMR_RECV_SIZE);
		return;
	}
	a1_policy_helper helper;
	bool res=false;
	switch(message->mtype){
		//need to fix the health check.
		case (RIC_HEALTH_CHECK_REQ):
				message->mtype = RIC_HEALTH_CHECK_RESP;        // if we're here we are running and all is ok
				message->sub_id = -1;
				strncpy( (char*)message->payload, "HELLOWORLD OK\n", rmr_payload_size( message) );
				*resend = true;
				break;

		case (RIC_INDICATION): {

			mdclog_write(MDCLOG_INFO, "Received RIC indication message of type = %d", message->mtype);

			unsigned char *me_id_null; 
			unsigned char *me_id = rmr_get_meid(message, me_id_null);
			mdclog_write(MDCLOG_INFO,"RMR Received MEID: %s",me_id);

			process_ric_indication(message->mtype, me_id, message->payload, message->len);

			break;
		}

		case (RIC_SUB_RESP): {
        		mdclog_write(MDCLOG_INFO, "Received subscription message of type = %d", message->mtype);

				unsigned char *me_id_null;
				unsigned char *me_id = rmr_get_meid(message, me_id_null);
				mdclog_write(MDCLOG_INFO,"RMR Received MEID: %s",me_id);

				if(_ref_sub_handler !=NULL){
					_ref_sub_handler->manage_subscription_response(message->mtype, me_id, message->payload, message->len);
				} else {
					mdclog_write(MDCLOG_ERR, " Error :: %s, %d : Subscription handler not assigned in message processor !", __FILE__, __LINE__);
				}
				*resend = false;
				break;
		 }

	case A1_POLICY_REQ:

		    mdclog_write(MDCLOG_INFO, "In Message Handler: Received A1_POLICY_REQ.");
			helper.handler_id = xapp_id;

			res = a1_policy_handler((char*)message->payload, &message->len, helper);
			if(res){
				message->mtype = A1_POLICY_RESP;        // if we're here we are running and all is ok
				message->sub_id = -1;
				*resend = true;
			}
			break;

	default:
		{
			mdclog_write(MDCLOG_ERR, "Error :: Unknown message type %d received from RMR", message->mtype);
			*resend = false;
		}
	}

	return;

};

void process_ric_indication(int message_type, transaction_identifier id, const void *message_payload, size_t message_len) {
	mdclog_write(MDCLOG_INFO,"In Process RIC indication with size: %ld",message_len);
	// std::cout << "In Process RIC indication with size " << message_len << std::endl;

	std::string agent_ip = find_agent_ip_from_gnb(id); 
	mdclog_write(MDCLOG_INFO,"Sending data to agent %s ", agent_ip.c_str());
	
	send_payload_socket(message_payload, message_len, agent_ip); 

	// decode received message payload
	E2AP_PDU_t *pdu = nullptr;
	auto retval = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2AP_PDU, (void **) &pdu, message_payload, message_len);
	
	// print decoded payload
	if (retval.code == RC_OK) {
		char *printBuffer; 
		size_t size;
		FILE *stream = open_memstream(&printBuffer, &size);
		// asn_fprint(stream, &asn_DEF_E2AP_PDU, pdu);
		xer_fprint(stream, &asn_DEF_E2AP_PDU, pdu);
		mdclog_write(MDCLOG_INFO, "Decoded E2AP PDU: %s", printBuffer);

		// send payload to agent
		// std::string agent_ip = find_agent_ip_from_gnb(gnb_id);
		// send_socket(payload, agent_ip); 
		// send_payload_socket((char*)message_payload, message_len, "127.0.0.1");
		// send_socket((char*)message_payload, "127.0.0.1");

		// uint8_t res = procRicIndication(pdu, id);
	}
	else {
		std::cout << "process_ric_indication, retval.code " << retval.code << std::endl;
	}
}

/**
 * Handle RIC indication
 * TODO doxy
 */

uint8_t procRicIndication(E2AP_PDU_t *e2apMsg, transaction_identifier gnb_id)
{
	mdclog_write(MDCLOG_INFO,"In Process RIC indication");
   	uint8_t idx;
	uint8_t ied;
	uint8_t ret = RC_OK;
	uint32_t recvBufLen;
	RICindication_t *ricIndication;
	RICaction_ToBeSetup_ItemIEs_t *actionItem;
// 
	std::string agent_ip = find_agent_ip_from_gnb(gnb_id);

	XMLDocument pduDoc;
	XMLDocument headerDoc;
	XMLDocument msgDoc;
// 
	char *printBuffer;
	size_t size;
	FILE *stream = open_memstream(&printBuffer, &size);
	xer_fprint(stream, &asn_DEF_E2AP_PDU, e2apMsg);
	// std::cout << "File stream size " << size << std::endl;
	// mdclog_write(MDCLOG_DEBUG, "Decoded E2AP PDU: %s", printBuffer);
	pduDoc.Parse(printBuffer);
// 
	mdclog_write(MDCLOG_INFO,"\nE2AP : RIC Indication received");
	ricIndication = &e2apMsg->choice.initiatingMessage->value.choice.RICindication;
// 
	mdclog_write(MDCLOG_INFO,"\nprotocolIEs elements %d\n", ricIndication->protocolIEs.list.count);	
// 
	for (idx = 0; idx < ricIndication->protocolIEs.list.count; idx++)
	{
		switch(ricIndication->protocolIEs.list.array[idx]->id)
		{
			case 28:  // RIC indication type
			{
				long ricindicationType = ricIndication->protocolIEs.list.array[idx]-> \
											value.choice.RICindicationType;
// 
				printf("ricindicationType %ld\n", ricindicationType);
// 
				break;
			}
			case 26:  // RIC indication message
			{
				// break;
			  int payload_size = ricIndication->protocolIEs.list.array[idx]-> \
			                              value.choice.RICindicationMessage.size;
// 
			  char* payload = (char*) calloc(payload_size, sizeof(char));
			  memcpy(payload, ricIndication->protocolIEs.list.array[idx]-> \
			                              value.choice.RICindicationMessage.buf, payload_size);
// 
			//   printf("Message size %d\n", payload_size);
// 
			  E2SM_KPM_IndicationMessage_t *descriptor = 0;
			// 
			  auto retvalMsgKpm = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2SM_KPM_IndicationMessage, (void **) &descriptor, payload, payload_size);
// 
			  char *printBufferMessage;
			  size_t sizeMessage;
			  FILE *streamMessage = open_memstream(&printBufferMessage, &sizeMessage);
			  xer_fprint(streamMessage, &asn_DEF_E2SM_KPM_IndicationMessage, descriptor);
			  msgDoc.Parse(printBufferMessage);
			//   msgDoc.Print();
			break;
// 
			  E2SM_KPM_IndicationMessage_Format1_t *format = descriptor->choice.indicationMessage_Format1;
// 
			//   // pm containers
			  for(uint8_t pmContInd = 0; pmContInd<format->pm_Containers.list.count; pmContInd++){
// 
			    PM_Containers_Item_t *containers_list = format->pm_Containers.list.array[pmContInd];
// 
			    PF_Container_t *ranContainer = containers_list->performanceContainer;
// 
			    switch (ranContainer->present)
				{
				case PF_Container_PR_oDU:
					{
				    //   NS_LOG_DEBUG ("O-DU: Get Cell Resource Report Item");
					  mdclog_write(MDCLOG_DEBUG, "O-DU: Get Cell Resource Report Item");
				      ODU_PF_Container_t *odu = ranContainer->choice.oDU;
				      for (uint8_t id_cellReports = 0; id_cellReports < odu->cellResourceReportList.list.count; id_cellReports++)
				      {
				        CellResourceReportListItem_t *cellResourceReportList = odu->cellResourceReportList.list.array[id_cellReports];
				        for (uint8_t id_servedcellReports = 0; id_servedcellReports < cellResourceReportList->servedPlmnPerCellList.list.count; id_servedcellReports++)
				        {
				          ServedPlmnPerCellListItem_t* servedCellItem = cellResourceReportList->servedPlmnPerCellList.list.array[id_servedcellReports];
				          PLMN_Identity_t	 pLMN_Identity = servedCellItem->pLMN_Identity;
				          EPC_DU_PM_Container_t *edpc = servedCellItem->du_PM_EPC;
				          for (uint8_t id_cqiReports = 0; id_cqiReports < edpc->perQCIReportList_du.list.count; id_cqiReports++)
				          {
				            PerQCIReportListItem_t* cqiReportItem = edpc->perQCIReportList_du.list.array[id_cqiReports];
				            long *dlUsedPrbs = cqiReportItem->dl_PRBUsage;
				            long *ulUsedPrbs = cqiReportItem->ul_PRBUsage;
				            long qci = cqiReportItem->qci;
				          }
				        }
				        long *dlAvailablePrbs = cellResourceReportList->dl_TotalofAvailablePRBs;
				        long *ulAvailablePrbs = cellResourceReportList->ul_TotalofAvailablePRBs;
				        PLMN_Identity_t pLMN_Identity = cellResourceReportList->nRCGI.pLMN_Identity;
						NRCellIdentity_t nRCellIdentity = cellResourceReportList->nRCGI.nRCellIdentity;
				      }
					}
					break;
// 
				case PF_Container_PR_oCU_CP:
					{
						mdclog_write(MDCLOG_DEBUG, "O-CU: Get Cell Resource Report Item");
				      OCUCP_PF_Container_t *ocucp = ranContainer->choice.oCU_CP;
				      long *numActiveUes = ocucp->cu_CP_Resource_Status.numberOfActive_UEs;
				    }
				    break;
// 
				  case PF_Container_PR_oCU_UP:
				    {
						mdclog_write(MDCLOG_DEBUG, "O-CU-UP: Get Cell Resource Report Item");
				      OCUUP_PF_Container_t* ocuup = ranContainer->choice.oCU_UP;
				      for (uint8_t id_pfContainers = 0; id_pfContainers < ocuup->pf_ContainerList.list.count; id_pfContainers++)
				      {
				        PF_ContainerListItem_t * pf_Container = ocuup->pf_ContainerList.list.array[id_pfContainers];
				        long interfaceType = pf_Container->interface_type;
				        for (uint8_t plmnListInd = 0; plmnListInd< pf_Container->o_CU_UP_PM_Container.plmnList.list.count; plmnListInd++){
				          PlmnID_Item_t* plmnIdItem = pf_Container->o_CU_UP_PM_Container.plmnList.list.array[plmnListInd];
				          PLMN_Identity_t	 pLMN_Identity = plmnIdItem->pLMN_Identity;
				          EPC_CUUP_PM_Format_t* cuuppmf = plmnIdItem->cu_UP_PM_EPC;
				          for (uint8_t cqiReportInd = 0; cqiReportInd< cuuppmf->perQCIReportList_cuup.list.count; cqiReportInd++){
				            PerQCIReportListItemFormat_t* pqrli = cuuppmf->perQCIReportList_cuup.list.array[cqiReportInd];
				            INTEGER_t *pDCPBytesDL = pqrli->pDCPBytesDL;
				            INTEGER_t *pDCPBytesUL = pqrli->pDCPBytesUL;
							long drbqci = pqrli->drbqci;
				          }
				        }
				      }
					}
					break;
				// 
				default:
					break;
				}
// 
			  }
			  // list of pm information
			  for(uint8_t pmInfoInd = 0; pmInfoInd<format->list_of_PM_Information->list.count; pmInfoInd++){
			    PM_Info_Item_t* pmInfoItem = format->list_of_PM_Information->list.array[pmInfoInd];
				// 
			    MeasurementTypeName_t measName = pmInfoItem->pmType.choice.measName;
// 
			    switch (pmInfoItem->pmVal.present)
			    {
			    case MeasurementValue_PR_valueInt:
			      {
			        long value = pmInfoItem->pmVal.choice.valueInt;
			      }
			      break;
			    case MeasurementValue_PR_valueReal:
			      {
			        double value = pmInfoItem->pmVal.choice.valueReal;
			      }
			      break;
			    case MeasurementValue_PR_valueRRC:
			      {
					L3_RRC_Measurements_t *valueRRC = pmInfoItem->pmVal.choice.valueRRC;
			      }
			      break;
				// 
			    default:
			      break;
			    }
// 
			    MeasurementValue_t pmVal = pmInfoItem->pmVal;
				// 
				// 
				// 
			    // pmInfoItem->pmVal
			  }
// 
			  std::cout << "E2SM type " <<descriptor->present << std::endl;
			}
			break;
// 
			case 25:  // RIC indication header
			{
				// break;
				std::cout << "Ric indication header at index " << (int)idx << std::endl;
				int payload_size = ricIndication->protocolIEs.list.array[idx]-> \
											value.choice.RICindicationHeader.size;
// 
// 
				char* payload = (char*) calloc(payload_size, sizeof(char));
				memcpy(payload, ricIndication->protocolIEs.list.array[idx]-> \
											value.choice.RICindicationHeader.buf, payload_size);
// 
				E2SM_KPM_IndicationHeader_t *descriptor = 0;
// 
				auto retvalMsgKpm = asn_decode(nullptr, ATS_ALIGNED_BASIC_PER, &asn_DEF_E2SM_KPM_IndicationHeader, (void **) &descriptor, payload, payload_size);
// 
				char *printBufferHeader;
				size_t sizeHeader;
				FILE *streamHeader = open_memstream(&printBufferHeader, &sizeHeader);
// 
				xer_fprint(streamHeader, &asn_DEF_E2SM_KPM_IndicationHeader, descriptor);
				std::cout << "Printer header doc " << (int)idx << std::endl;
				// 
				headerDoc.Parse(printBufferHeader);
// 
				break;
				// 
				E2SM_KPM_IndicationHeader_Format1_t* ind_header = descriptor->choice.indicationHeader_Format1;
// 
				std::cout << "E2SM type " <<descriptor->present << std::endl;
				std::cout << "global e2 node type " <<ind_header->id_GlobalE2node_ID.present << std::endl;
// 
				std::string plmId = "";
				std::string gnbId = "";
				uint64_t _timestamp = 0;
// 
				switch(ind_header->id_GlobalE2node_ID.present){
					case GlobalE2node_ID_PR_NOTHING: {
// 
					}
					break;
					case GlobalE2node_ID_PR_gNB: {
					GlobalE2node_gNB_ID_t* _gnbChoice = ind_header->id_GlobalE2node_ID.choice.gNB;
					int gnbIdSize = _gnbChoice->global_gNB_ID.gnb_id.choice.gnb_ID.size;
					// std::cout << "Size of gnb id " << gnbIdSize << std::endl;
					if (gnbIdSize>0){
						char gnbIdOut[gnbIdSize + 1];
						std::memcpy (gnbIdOut, _gnbChoice->global_gNB_ID.gnb_id.choice.gnb_ID.buf, gnbIdSize);
						gnbIdOut[gnbIdSize] = '\0';
						std::cout << "Value of gnb id " << gnbIdOut << std::endl;
						gnbId = std::string(gnbIdOut);
					}
// 
					int plmnIdSize = _gnbChoice->global_gNB_ID.plmn_id.size;
					char plmnIdOut[plmnIdSize + 1];
					std::memcpy (plmnIdOut, _gnbChoice->global_gNB_ID.plmn_id.buf, plmnIdSize);
					plmnIdOut[plmnIdSize] = '\0';
					plmId = std::string(plmnIdOut);
					}
					break;
					case GlobalE2node_ID_PR_en_gNB: {
					GlobalE2node_en_gNB_ID_t	* _gnbChoice = ind_header->id_GlobalE2node_ID.choice.en_gNB;
					int gnbIdSize = _gnbChoice->global_gNB_ID.gNB_ID.choice.gNB_ID.size;
					// std::cout << "Size of gnb id " << gnbIdSize << std::endl;
					if (gnbIdSize>0){
						char gnbIdOut[gnbIdSize + 1];
						std::memcpy (gnbIdOut, _gnbChoice->global_gNB_ID.gNB_ID.choice.gNB_ID.buf, gnbIdSize);
						gnbIdOut[gnbIdSize] = '\0';
						// std::cout << "Value of gnb id " << std::string(gnbIdOut) << std::endl;
						gnbId = std::string(gnbIdOut);
					}
// 
					int plmnIdSize = _gnbChoice->global_gNB_ID.pLMN_Identity.size;
					char plmnIdOut[plmnIdSize + 1];
					std::memcpy (plmnIdOut, _gnbChoice->global_gNB_ID.pLMN_Identity.buf, plmnIdSize);
					plmnIdOut[plmnIdSize] = '\0';
					plmId = std::string(plmnIdOut);
					}
					break;
					case GlobalE2node_ID_PR_ng_eNB: {
					GlobalE2node_ng_eNB_ID_t	* _gnbChoice = ind_header->id_GlobalE2node_ID.choice.ng_eNB;
					BIT_STRING_t _bit_string_obj;
					switch (_gnbChoice->global_ng_eNB_ID.enb_id.present)
					{
						case ENB_ID_Choice_PR_enb_ID_macro:
						_bit_string_obj = _gnbChoice->global_ng_eNB_ID.enb_id.choice.enb_ID_macro;
						break;
						case ENB_ID_Choice_PR_enb_ID_shortmacro:
						_bit_string_obj = _gnbChoice->global_ng_eNB_ID.enb_id.choice.enb_ID_shortmacro;
						break;
						case ENB_ID_Choice_PR_enb_ID_longmacro:
						_bit_string_obj = _gnbChoice->global_ng_eNB_ID.enb_id.choice.enb_ID_longmacro;
						break;
						// 
						default:
						break;
					}
					int gnbIdSize = _bit_string_obj.size;
					// std::cout << "Size of gnb id " << gnbIdSize << std::endl;
					if (gnbIdSize>0){
						char gnbIdOut[gnbIdSize + 1];
						std::memcpy (gnbIdOut, _bit_string_obj.buf, gnbIdSize);
						gnbIdOut[gnbIdSize] = '\0';
						// std::cout << "Value of gnb id " << gnbIdOut << std::endl;
						gnbId = std::string(gnbIdOut);
					}
// 
					int plmnIdSize = _gnbChoice->global_ng_eNB_ID.plmn_id.size;
					char plmnIdOut[plmnIdSize + 1];
					std::memcpy (plmnIdOut, _gnbChoice->global_ng_eNB_ID.plmn_id.buf, plmnIdSize);
					plmnIdOut[plmnIdSize] = '\0';
					plmId = std::string(plmnIdOut);
					}
					break;
					case GlobalE2node_ID_PR_eNB: {
					GlobalE2node_eNB_ID_t* _gnbChoice = ind_header->id_GlobalE2node_ID.choice.eNB;
					// std::cout << "Type of enb id " << (int) _gnbChoice->global_eNB_ID.eNB_ID.present << std::endl;
					BIT_STRING_t _bit_string_obj;
					switch (_gnbChoice->global_eNB_ID.eNB_ID.present)
					{
					case ENB_ID_PR_macro_eNB_ID:
						_bit_string_obj = _gnbChoice->global_eNB_ID.eNB_ID.choice.macro_eNB_ID;
						break;
					case ENB_ID_PR_home_eNB_ID:
						_bit_string_obj = _gnbChoice->global_eNB_ID.eNB_ID.choice.home_eNB_ID;
						break;
					case ENB_ID_PR_short_Macro_eNB_ID:
						_bit_string_obj = _gnbChoice->global_eNB_ID.eNB_ID.choice.short_Macro_eNB_ID;
						break;
					case ENB_ID_PR_long_Macro_eNB_ID:
						_bit_string_obj = _gnbChoice->global_eNB_ID.eNB_ID.choice.long_Macro_eNB_ID;
						break;
					// 
					default:
						break;
					}
					// 
					int gnbIdSize = (int) _bit_string_obj.size;
					// std::cout << "Size of gnb id " << gnbIdSize << std::endl;
					if (gnbIdSize>0){
						char gnbIdOut[gnbIdSize + 1];
						std::memcpy (gnbIdOut, _bit_string_obj.buf, gnbIdSize);
						gnbIdOut[gnbIdSize] = '\0';
						// std::cout << "Value of gnb id " << gnbIdOut << std::endl;
						gnbId = std::string(gnbIdOut);
					}
					// std::cout << "Consider plmn" << std::endl;
					PLMN_Identity_t plmn_identity = _gnbChoice->global_eNB_ID.pLMN_Identity;
					int plmnIdSize = plmn_identity.size;
					// std::cout << "Size of plmn id " << plmnIdSize << std::endl;
					if (plmnIdSize > 0){
						char plmnIdOut[plmnIdSize + 1];
						// std::cout << "Size of gnb buffer " << plmn_identity.buf << std::endl;
						// std::cout << "Size of gnb buffer " << plmn_identity.buf << std::endl;
						std::memcpy (plmnIdOut, plmn_identity.buf, plmnIdSize);
						plmnIdOut[plmnIdSize] = '\0';
						plmId = std::string(plmnIdOut);
						// 
					}
					// 
					}
					break;
				}
// 
				long _firstConversion = 0;
// 
				std::memcpy(&_firstConversion, ind_header->collectionStartTime.buf, ind_header->collectionStartTime.size);
// 
				_timestamp = be64toh(_firstConversion);
// 
				// 
				break;
			}
			// 
		}
	}
// 
	// merging the data
// 
	XMLNode* rootHeader = headerDoc.FirstChild()->DeepClone(&pduDoc); 
    pduDoc.FirstChild()->InsertEndChild(rootHeader);
// 
    XMLNode* rootMessage = msgDoc.FirstChild()->DeepClone(&pduDoc);
    pduDoc.FirstChild()->InsertEndChild(rootMessage);
// 
	// sending the final
	char *printBufferFinal;
	size_t sizeFinal;
	FILE *streamFinal = open_memstream(&printBufferFinal, &sizeFinal);
// 
	// pduDoc.SaveFile(streamFinal);
// 
	printf("\nSaving the file");
	pduDoc.SaveFile(streamFinal, true);
	std::cout << "\nSending to the socket buffer with size "<<sizeFinal << std::endl;
	// pduDoc.Print();
// 
	fflush(streamFinal);
// sending to socket
	send_socket(printBufferFinal, agent_ip);
	// 
   return ret; // TODO update ret value in case of errors
}
