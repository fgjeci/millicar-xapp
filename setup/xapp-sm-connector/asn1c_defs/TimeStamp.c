/*
 * Generated by asn1c-0.9.29 (http://lionet.info/asn1c)
 * From ASN.1 module "E2SM-KPM-RC"
 * 	found in "e2sm-kpm-rc.asn"
 * 	`asn1c -fcompound-names -fno-include-deps -findirect-choice -pdu=auto -gen-PER -gen-OER -no-gen-example -D .`
 */

#include <TimeStamp.h>

int
TimeStamp_constraint(const asn_TYPE_descriptor_t *td, const void *sptr,
			asn_app_constraint_failed_f *ctfailcb, void *app_key) {
	const OCTET_STRING_t *st = (const OCTET_STRING_t *)sptr;
	size_t size;
	
	if(!sptr) {
		ASN__CTFAIL(app_key, td, sptr,
			"%s: value not given (%s:%d)",
			td->name, __FILE__, __LINE__);
		return -1;
	}
	
	size = st->size;
	
	if((size == 8)) {
		/* Constraint check succeeded */
		return 0;
	} else {
		ASN__CTFAIL(app_key, td, sptr,
			"%s: constraint failed (%s:%d)",
			td->name, __FILE__, __LINE__);
		return -1;
	}
}

/*
 * This type is implemented using OCTET_STRING,
 * so here we adjust the DEF accordingly.
 */

// original
// static asn_oer_constraints_t asn_OER_type_TimeStamp_constr_1 CC_NOTUSED = {
// 	{ 0, 0 },
// 	8	/* (SIZE(8..8)) */};
// end original

// modified
static asn_per_constraints_t asn_OER_type_TimeStamp_constr_1 CC_NOTUSED = {
{ 0, 0 },
8	/* (SIZE(8..8)) */};
// end modification

asn_per_constraints_t asn_PER_type_TimeStamp_constr_1 CC_NOTUSED = {
	{ APC_UNCONSTRAINED,	-1, -1,  0,  0 },
	{ APC_CONSTRAINED,	 0,  0,  8,  8 }	/* (SIZE(8..8)) */,
	0, 0	/* No PER value map */
};
static const ber_tlv_tag_t asn_DEF_TimeStamp_tags_1[] = {
	(ASN_TAG_CLASS_UNIVERSAL | (4 << 2))
};
asn_TYPE_descriptor_t asn_DEF_TimeStamp = {
	"TimeStamp",
	"TimeStamp",
	&asn_OP_OCTET_STRING,
	asn_DEF_TimeStamp_tags_1,
	sizeof(asn_DEF_TimeStamp_tags_1)
		/sizeof(asn_DEF_TimeStamp_tags_1[0]), /* 1 */
	asn_DEF_TimeStamp_tags_1,	/* Same as above */
	sizeof(asn_DEF_TimeStamp_tags_1)
		/sizeof(asn_DEF_TimeStamp_tags_1[0]), /* 1 */
	// original
	// { &asn_OER_type_TimeStamp_constr_1, &asn_PER_type_TimeStamp_constr_1, TimeStamp_constraint },
	// end original
	// modified
	{0, &asn_PER_type_TimeStamp_constr_1, TimeStamp_constraint },
	// end modification
	0, 0,	/* No members */
	&asn_SPC_OCTET_STRING_specs	/* Additional specs */
};
