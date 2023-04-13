/*
 * Generated by asn1c-0.9.29 (http://lionet.info/asn1c)
 * From ASN.1 module "E2SM-KPM-IEs"
 * 	found in "E2SM-KPM-v02.00.03.asn"
 * 	`asn1c -pdu=auto -fno-include-deps -fcompound-names -findirect-choice -gen-PER -gen-OER -no-gen-example -D E2SM-KPM-v02.00.03`
 */

#ifndef	_HANDOVER_CONTROL_MESSAGE_H_
#define	_HANDOVER_CONTROL_MESSAGE_H_

// #include <asn_application.h>

extern "C" {


/* Including external dependencies */

#include <constr_SEQUENCE.h>
#include <NativeInteger.h>

}

// #include "stddef.h"

#ifdef __cplusplus
extern "C" {
#endif

/* MeasurementRecord */
typedef struct CellHandoverItem {
	// UE_Identity_t ueId;
    // NRCellIdentity_t destinationCellId;

	long ueId;
    long destinationCellId;
	
	/* Context for parsing across buffer boundaries */
	asn_struct_ctx_t _asn_ctx;
} CellHandoverItem_t;

/* Implementation */
extern asn_TYPE_descriptor_t asn_DEF_CellHandoverItem;
extern asn_SEQUENCE_specifics_t asn_SPC_CellHandoverItem_specs_1;
extern asn_TYPE_member_t asn_MBR_CellHandoverItem_1[2];
// extern asn_per_constraints_t asn_PER_type_CellHandoverItem_constr_1;
asn_struct_free_f CellHandoverItem_free;
asn_struct_print_f CellHandoverItem_print;

#ifdef __cplusplus
}
#endif

#endif	/* _CellHandoverItem_H_ */
#include <asn_internal.h>