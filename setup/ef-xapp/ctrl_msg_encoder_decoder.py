import ctypes
from ctypes import POINTER, Structure
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

class RicControlMessageEncoder:
    def __init__(self):
        self._asn1_c_lib = ctypes.CDLL("libe2sim.so", mode=ctypes.RTLD_GLOBAL)

    def _wrap_asn1_function(self, funcname, restype, argtypes):
        func = self._asn1_c_lib.__getattr__(funcname)
        func.restype = restype
        func.argtypes = argtypes
        return func

    def encode_result(self, ef_ids: List[int], ef_start_allocation, ef_optimized_allocation):

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