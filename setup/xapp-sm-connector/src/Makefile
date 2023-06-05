CXX:= g++ --std=c++14 -O2 -L/usr/local/lib
CC:= gcc -O2 -L/usr/local/lib

SRC:=./
HWSRC:=./
UTILSRC=./xapp-utils
MSGSRC:=./xapp-mgmt

ASNSRC:=../asn1c_defs
E2APSRC:=./xapp-asn/e2ap
E2SMSRC:=./xapp-asn/e2sm

# modified
TINYXMLSRC:=./xapp-tinyxml2
RICCONTROLSRC:=./xapp_ric_control
# end modification

####### Logging library and flags
CLOGFLAGS:= `pkg-config mdclog --cflags`
LOG_LIBS:= `pkg-config mdclog --libs`
CURL_LIBS:= `pkg-config libcurl --libs`
RNIB_LIBS:= -pthread /usr/local/include/rnib/rnibreader.a
######## Keep include dirs separate so we have transparency


BASEFLAGS=  -Wall -std=c++14 $(CLOGFLAGS) 
# original
C_BASEFLAGS= -Wall $(CLOGFLAGS) -DASN_DISABLE_OER_SUPPORT
# end original
# modified
# C_BASEFLAGS= -Wall $(CLOGFLAGS)
# end modification

XAPPFLAGS= -I./
HWFLAGS= -I./
UTILFLAGS= -I$(UTILSRC)
MSGFLAGS= -I$(MSGSRC) 

# original
ASNFLAGS=-I$(ASNSRC) -DASN_DISABLE_OER_SUPPORT
# end original
# modified
# ASNFLAGS=-I$(ASNSRC)
# end modification
E2APFLAGS = -I$(E2APSRC)
E2SMFLAGS = -I$(E2SMSRC)

# modified
TINYXMLFLAGS = -I$(TINYXMLSRC)

CONTROLMESSAGEFLAGS = -I$(RICCONTROLSRC)
# end modification

########libs

LIBS= -lsdl -lrmr_si  -lpthread -lm $(LOG_LIBS) $(CURL_LIBS) $(RNIB_LIBS)
COV_FLAGS= -fprofile-arcs -ftest-coverage

#######
HWXAPP_SRC= hw_xapp_main.cc
XAPP_SRC= xapp.cc
UTIL_SRC= $(wildcard $(UTILSRC)/*.cc)
MSG_SRC= $(wildcard $(MSGSRC)/*.cc)

E2AP_SRC= $(wildcard $(E2APSRC)/*.cc)
E2SM_SRC= $(wildcard $(E2SMSRC)/*.cc)
ASN1C_SRC= $(wildcard $(ASNSRC)/*.c)

# modified
TINYXML_SRC=$(wildcard $(TINYXMLSRC)/*.cpp)

# PYTHON_RIC_MESSAGE_ENCODER_SRC = control_message_encoder_decoder.cc
# HANDOVER_CONTROL_MESSAGE_SRC = handover_control_message.cc
# CONTROL_MESSAGE_SRC = $(PYTHON_RIC_MESSAGE_ENCODER_SRC) $(HANDOVER_CONTROL_MESSAGE_SRC)
#  $(RICCONTROLSRC)/E2SM-RC-ControlMessage.c
CONTROL_MESSAGE_SRC=$(wildcard $(RICCONTROLSRC)/*.cc)
# end modification

##############Objects
UTIL_OBJ=${UTIL_SRC:.cc=.o}
XAPP_OBJ=${XAPP_SRC:.cc=.o}
HWXAPP_OBJ=${HWXAPP_SRC:.cc=.o} 
MSG_OBJ=${MSG_SRC:.cc=.o}

# modified
TINYXML_OBJ=${TINYXML_SRC:.cpp=.o}

# PYTHON_RIC_MESSAGE_ENCODER_OBJ=${PYTHON_RIC_MESSAGE_ENCODER_SRC:.cc=.o} 
# HANDOVER_CONTROL_MESSAGE_OBJ=${HANDOVER_CONTROL_MESSAGE_SRC:.cc=.o} 
CONTROL_MESSAGE_OBJ = ${CONTROL_MESSAGE_SRC:.cc=.o}
# end modification

E2AP_OBJ = $(E2AP_SRC:.cc=.o)
E2SM_OBJ = $(E2SM_SRC:.cc=.o)
ASN1C_MODULES = $(ASN1C_SRC:.c=.o)

$(ASN1C_MODULES): export CFLAGS = $(C_BASEFLAGS) $(ASNFLAGS)
$(UTIL_OBJ):export CPPFLAGS=$(BASEFLAGS) $(UTILFLAGS) $(E2APFLAGS) $(E2SMFLAGS) $(ASNFLAGS) $(MSGFLAGS)

$(MSG_OBJ):export CPPFLAGS=$(BASEFLAGS) $(MSGFLAGS) $(ASNFLAGS) $(E2APFLAGS) $(E2SMFLAGS)
$(E2AP_OBJ): export CPPFLAGS = $(BASEFLAGS) $(ASNFLAGS) $(E2APFLAGS)
$(E2SM_OBJ): export CPPFLAGS = $(BASEFLAGS) $(ASNFLAGS) $(E2SMFLAGS)
$(XAPP_OBJ): export CPPFLAGS = $(BASEFLAGS) $(XAPPFLAGS) $(UTILFLAGS) $(MSGFLAGS) $(E2APFLAGS) $(E2SMFLAGS) $(ASNFLAGS)

$(HWXAPP_OBJ):export CPPFLAGS=$(BASEFLAGS) $(HWFLAGS) $(XAPPFLAGS) $(UTILFLAGS) $(MSGFLAGS) $(E2APFLAGS) $(E2SMFLAGS) $(ASNFLAGS)

# modified
$(TINYXML_OBJ):export CPPFLAGS= $(BASEFLAGS) $(TINYXMLFLAGS)

$(CONTROL_MESSAGE_OBJ):export CPPFLAGS= $(C_BASEFLAGS) $(BASEFLAGS) $(HWFLAGS) $(XAPPFLAGS) $(UTILFLAGS) $(MSGFLAGS) $(E2APFLAGS) $(E2SMFLAGS) $(ASNFLAGS)
# end modification

#  $(CONTROL_MESSAGE_OBJ)
OBJ= $(HWXAPP_OBJ) $(UTIL_OBJ) $(MSG_OBJ)  $(ASN1C_MODULES) $(E2AP_OBJ) $(E2SM_OBJ) $(XAPP_OBJ) $(TINYXML_OBJ)

print-%  : ; @echo $* = $($*)

hw_xapp_main: $(OBJ)
	$(CXX) -o $@  $(OBJ) $(LIBS) $(RNIBFLAGS) $(CPPFLAGS) $(CLOGFLAGS) agent_connector.cc

# test_msg_creation: $(OBJ)
# 	$(CXX) -o $@  $(OBJ) $(LIBS) $(RNIBFLAGS) $(CPPFLAGS) $(CLOGFLAGS) $(CONTROLMESSAGEFLAGS) test_msg_creation.cc


# install: hw_xapp_main test_msg_creation
# 	install  -D hw_xapp_main  /usr/local/bin/hw_xapp_main
# 	install  -D test_msg_creation  /usr/local/bin/test_msg_creation

install: hw_xapp_main
	install  -D hw_xapp_main  /usr/local/bin/hw_xapp_main

# $(RICCONTROLSRC)/*.o test_msg_creation
clean:
	-rm *.o $(ASNSRC)/*.o $(E2APSRC)/*.o $(UTILSRC)/*.o $(E2SMSRC)/*.o  $(MSGSRC)/*.o $(SRC)/*.o hw_xapp_main 
