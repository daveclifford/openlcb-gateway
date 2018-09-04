from openlcb_protocol import *
from openlcb_debug import *
import openlcb_config

"""This file defines a basic openlcb node (the gateway will handle several of these
You derive your "real node class" from it and add the handling specific to your hardware
Also contains the memory space management (as in CDI config)
"""
        
"""mem_space is a segment of memory you read from /write to using addresses
It is made of triples: beginning address(offset), size and a write_callback function
This function is called when the memory cell is written to with the following parameters:
write_callback(offset,buf)
where offset is the begining of the cell and buf is the buf which has just been written
"""
class Mem_space:
    def __init__(self,list=None):
        self.mem = {}
        self.mem_chunks={}
        if list is not None:
            for (offset,size) in list:
                self.create_mem(offset,size)

    def create_mem(self,offset,size):
        self.mem[(offset,size)]=None
        
    def set_mem_partial(self,add,buf):
        """returns the memory space (offset,size,buf) if memory must be updated
        or None if the write is incomplete: some writes are still expected for this memory space
        """
        
        for (offset,size) in self.mem.keys():
            if add>=offset and add <offset+size:
                if offset in self.mem_chunks:
                    self.mem_chunks[offset]+=buf
                else:
                    self.mem_chunks[offset]=buf
                if len(self.mem_chunks[offset])==size:
                    buf=self.mem_chunks[offset]
                    del self.mem_chunks[offset]
                    return (offset,size,buf)
                elif len(self.mem_chunks[offset])>size:
                    del self.mem_chunks[offset]

        return None

    def set_mem(self,offset,buf):
        if (offset,len(buf)) in self.mem:
            self.mem[(offset,len(buf))]=buf
            return True
        
        debug("set_mem failed, off=",offset,"buf=",buf," of length=",len(buf))
        return False


    def read_mem(self,add):
        for (offset,size) in self.mem.keys():
            if add>=offset and add <offset+size:
                if self.mem[(offset,size)] is not None:
                    return self.mem[(offset,size)][add-offset:]
                else:
                    return None
        return None

    def mem_valid(self,offset):
        return offset not in self.mem_chunks
    
    def __str__(self):
        return str(self.mem)
    
    def dump(self):
        for (off,size) in self.mem:
            print("off=",off,"size=",size,"content=",self.mem[(off,size)])

    def get_size(self,offset):
        for (off,size) in self.mem.keys():
            if off==offset:
                return size
        return None #offset not found

"""
Base class for all node types
You must implement get_cdi() so that the gateway can retrieve the CDI describing your node
You also most probably want to extend set_mem and maybe read_mem to sync the node's memory with the
real node's mem
"""
class Node:
    ID_PRO_CON_VALID=1
    ID_PRO_CON_INVAL=-1
    ID_PRO_CON_UNKNOWN=0
    
    def __init__(self,ID,permitted=False,aliasID=None):
        self.ID = ID
        self.aliasID = aliasID
        self.permitted=permitted
        self.advertised = False
        self.produced_ev=[]
        self.consumed_ev=[]
        self.simple_info = []
        self.memory = None    #this is the object representing the OpenLCB node memory
                              #you need to create the memory spaces (see the mem_space class)
        self.current_write = None  #this is a pair (memory space, address) that holds
                                   #the current writing process
        self.PRNG = None

    def set_mem(self,mem_sp,offset,buf): #extend this to sync the "real" node (cpNode or whatever)
                                         #with the openlcb memory
        return self.memory[mem_sp].set_mem(offset,buf)

    def create_alias_negotiation(self):
        """
        Set up a new alias negotiation (creates an alias also)
        """
        if self.PRNG is None:
            self.PRNG = self.ID
        else:
            self.PRNG += (self.PRNG << 9) + 0x1B0CA37A4BA9
        alias = ((self.PRNG >> 36)^(self.PRNG>> 24)^(self.PRNG >> 12)^self.PRNG) & 0xFFF
        
        self.aliasID = alias
        debug("new alias for ",self.ID," : ",self.aliasID)
        return Alias_negotiation(alias,self.ID)
        
    def set_mem_partial(self,mem_sp,add,buf):
        res = self.memory[mem_sp].set_mem_partial(add,buf)
        if res is not None:
            self.set_mem(mem_sp,res[0],res[2])
        
    def read_mem(self,mem_sp,add):
        return self.memory[mem_sp].read_mem(add)

    def get_mem_size(self,mem_sp,offset):
        return self.memory[mem_sp].get_size()
        
    def add_consumed_ev(self,ev):
        self.consumed_ev.append(ev)

    def add_produced_ev(self,ev):
        self.produced_ev.append(ev)

    def set_simple_info(self,list):
        self.simple_info = list  #byte arrays

    def build_simple_info_dgram(self): # return datagrams holding the simple info
        print("build_simple_info not implemented!") #fixme
    

def find_node(aliasID):
    for n in all_nodes:
        if n.aliasID == aliasID:
            return n
    return None


"""
append the new node if it was not known before (return True)
or does nothing if it was (return False)
"""
def new_node(new_n):
    for n in all_nodes:
        if n.ID == new_n.ID:
            return False
    all_nodes.append(new_n)
    return True
#globals
all_nodes = []       #list of all known nodes
