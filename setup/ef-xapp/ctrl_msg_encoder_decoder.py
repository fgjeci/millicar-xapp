import ctypes
from ctypes import POINTER, Structure, create_string_buffer
from ctypes import c_long, c_size_t, c_int, c_uint8, c_char_p, c_void_p
from ctypes import c_int16, c_uint16, c_uint32, c_ubyte

from typing import List

# class handover_control_message_t(Structure):
#     _fields_ = [
#         ("ue_id", c_long),
#         ("destination_cell_id", c_long)
#     ]

class buffer_lengtht_t(Structure):
    _fields_ = [
        ("length", c_int),
        ("buffer", POINTER(c_ubyte)) # POINTER(c_uint8)
    ]
class e2ap_stcp_buffer_t(Structure):
    _fields_ = [
        ("msg_length", c_int),
        ("bytes_consumed", c_int),
        ("msg_buffer", POINTER(c_ubyte)) # POINTER(c_uint8)
    ]

class RicControlMessageEncoder:
    def __init__(self):
        self._asn1_c_lib = ctypes.CDLL("libe2sim.so", mode=ctypes.RTLD_GLOBAL)

    def _wrap_asn1_function(self, funcname, restype, argtypes):
        func = self._asn1_c_lib.__getattr__(funcname)
        func.restype = restype
        func.argtypes = argtypes
        return func

    def encode_result(self, ef_ids: List[int], ef_start_allocation: List[int], ef_optimized_allocation: List[int]):

        _asn1_decode_handoverMsg = self._wrap_asn1_function(
        'gnerate_e2ap_encode_handover_control_message', POINTER(buffer_lengtht_t), 
        [POINTER(c_uint16), POINTER(c_uint16), POINTER(c_uint16), c_size_t]) 
        
        _length = len(ef_ids)
        id_vec = (c_uint16*_length)()
        start_pos = (c_uint16*_length)()
        end_pos = (c_uint16*_length)()
        for _ind in range(_length):
            id_vec[_ind] = ef_ids[_ind]
            start_pos[_ind] = ef_start_allocation[_ind]
            end_pos[_ind] = ef_optimized_allocation[_ind]

        # msg: POINTER(buffer_lengtht_t) = _asn1_decode_handoverMsg(id_vec, start_pos, end_pos, _length)
        msg: buffer_lengtht_t = _asn1_decode_handoverMsg(id_vec, start_pos, end_pos, _length)
        _buffer_res = ctypes.cast(msg.contents.buffer, ctypes.POINTER(ctypes.c_ubyte * msg.contents.length))

        _data_bytes = bytes(_buffer_res.contents)
        _data_length = msg.contents.length

        return _data_length, _data_bytes
    
    def encode_result_plmn(self, ef_ids: List[int], ef_start_allocation: List[int], ef_optimized_allocation: List[int], plmnId:str):

        _asn1_decode_handoverMsg = self._wrap_asn1_function(
        'generate_e2ap_encode_handover_control_message_plmn', POINTER(buffer_lengtht_t), 
        [POINTER(c_uint16), POINTER(c_uint16), POINTER(c_uint16), c_size_t, c_char_p]) 
        
        _length = len(ef_ids)
        id_vec = (c_uint16*_length)()
        start_pos = (c_uint16*_length)()
        end_pos = (c_uint16*_length)()
        for _ind in range(_length):
            id_vec[_ind] = ef_ids[_ind]
            start_pos[_ind] = ef_start_allocation[_ind]
            end_pos[_ind] = ef_optimized_allocation[_ind]
        
        plmnId_encoded = plmnId.encode("utf-8")
        plmnId_c = create_string_buffer(plmnId_encoded)
        
        msg: buffer_lengtht_t = _asn1_decode_handoverMsg(id_vec, start_pos, end_pos, _length, plmnId_c)
        _buffer_res = ctypes.cast(msg.contents.buffer, ctypes.POINTER(ctypes.c_ubyte * msg.contents.length))

        _data_bytes = bytes(_buffer_res.contents)
        _data_length = msg.contents.length

        return _data_length, _data_bytes
    
    def decode_e2ap_ric_indication_msg(self, input_bytes):

        _asn1_decode_e2ap = self._wrap_asn1_function(
        'decode_e2ap_to_xml', POINTER(e2ap_stcp_buffer_t), 
        [POINTER(c_uint8), c_size_t]) 
        _length: int = len(input_bytes)
        _input_bytes_cast = (c_uint8*_length)()
        for _ind in range(_length):
            _input_bytes_cast[_ind] = input_bytes[_ind]
        # _input_bytes_cast = ctypes.cast(input_bytes, ctypes.POINTER(ctypes.c_ubyte))

        msg: e2ap_stcp_buffer_t = _asn1_decode_e2ap(_input_bytes_cast, _length)
        try:
            _data_length = msg.contents.msg_length
            _bytes_consumed = msg.contents.bytes_consumed
            print("Data length " + str(_data_length) + " bytes consumed " + str(_bytes_consumed))
            _buffer_res = ctypes.cast(msg.contents.msg_buffer, ctypes.POINTER(ctypes.c_ubyte * _data_length))
            _data_bytes = bytes(_buffer_res.contents)
            # print("Data length " + str(_data_length))
            return _data_bytes, _data_length, _bytes_consumed
            # print(_data_bytes)
        except ValueError:
            # print("Null pointer returned")
            return None, None, None

        

# _test_data_3 =  b"\x00\x05@\x83\xd3\x00\x00\x08\x00\x1d\x00\x05\x00\x00\x18\x00\x00\x00\x05\x00\x02\x00\xc8\x00\x0f\x00\x01\x01\x00\x1b\x00\x02\x00\x01\x00\x1c\x00\x01\x00\x00\x19\x00\x13\x12\x00\x00\x00\x01\x87\x94\xa6\xdbD\x00111P2\x00\x00\x00\x00\x1a\x00\x83\x8c\x83\x8a0\x80\x00\x00`11132\x00\x00\x00\x00\x8b\x00\x8b\x02111\x00\x00`\x01\x80\x00\x00\x041112\x07\x00\xc0TB.TotNbrDl.1\x00\x02\x02\x90\x01\x10TB.TotNbrDlInitial\x00\x02\x022\x00\xc0RRU.PrbUsedDl\x00\x01Y\x01\x10TB.ErrTotalNbrDl.1\x00\x01^\x01\xd0QosFlow.PdcpPduVolumeDL_Filter\x00\x03\x02hZ\x01\x10DRB.BufferSize.Qos\x00\x03\x04'\x03\x01\x10DRB.MeanActiveUeDl\x00\x01\x04\x00\x03@\x0500008\x06\x01\x10TB.TotNbrDl.1.UEID\x00\x02\x00\xad\x01`TB.TotNbrDlInitial.UEID\x00\x02\x00\x85\x02 QosFlow.PdcpPduVolumeDL_Filter.UEID\x00\x02,\xc7\x01\x10RRU.PrbUsedDl.UEID\x00\x01\x18\x01`DRB.BufferSize.Qos.UEID\x00\x03\x01o\x15\x00\xf0DRB.UEThpDl.UEID \x00@\x0500009\x06\x01\x10TB.TotNbrDl.1.UEID\x00\x02\x00\xa1\x01`TB.TotNbrDlInitial.UEID\x00\x02\x00\x8f\x02 QosFlow.PdcpPduVolumeDL_Filter.UEID\x00\x02\x199\x01\x10RRU.PrbUsedDl.UEID\x00\x01\x16\x01`DRB.BufferSize.Qos.UEID\x00\x03\x01{\x9d\x00\xf0DRB.UEThpDl.UEID \x00@\x0500001\x06\x01\x10TB.TotNbrDl.1.UEID\x00\x02\x00\x9e\x01`TB.TotNbrDlInitial.UEID\x00\x02\x00\x92\x02 QosFlow.PdcpPduVolumeDL_Filter.UEID\x00\x03\x01J \x01\x10RRU.PrbUsedDl.UEID\x00\x01\x15\x01`DRB.BufferSize.Qos.UEID\x00\x02`\x1b\x00\xf0DRB.UEThpDl.UEID \x00@\x0500012\x06\x01\x10TB.TotNbrDl.1.UEID\x00\x02\x00\xa4\x01`TB.TotNbrDlInitial.UEID\x00\x02\x00\x8c\x02 QosFlow.PdcpPduVolumeDL_Filter.UEID\x00\x03\x00\xd8:\x01\x10RRU.PrbUsedDl.UEID\x00\x01\x16\x01`DRB.BufferSize.Qos.UEID\x00\x03\x00\xdc6\x00\xf0DRB.UEThpDl.UEID \x00\x00\x14\x00\x05\x04cpid"

# if __name__ == '__main__':
#     _encoder = RicControlMessageEncoder()
#     print("decoding data")
#     _encoder.decode_e2ap_ric_indication_msg(_test_data_3)