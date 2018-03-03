import openlcb_cmri_cfg as cmri

"""This file defines a basic openlcb node (the gateway will handle several of these
You derive your "real node class" from it and add the handling specific to your hardware
Also contains the memory space management (as in CDI config), you also need to provide a callback to sync the node memory with the config of your hardware
"""

class buf_cb:
    def __init__(self,buf,callback=None):
        self.buf = buf
        self.write_cback=callback
        
"""mem_space is a segment of memory you read from /write to using addresses
It is made of triples: beginning address(offset), size and a write_callback function
This function is called when the memory cell is written to with the following parameters:
write_callback(offset,buf)
where offset is the beginnon of the cell and buf is the buf which has just been written
"""
class mem_space:
    def __init__(self,list=None):
        self.mem = {}
        self.mem_chunks={}
        if list is not None:
            for (offset,size,write_callback) in list:
                self.create_mem(offset,size,write_callback)
                print("created: ",offset,"-->",offset+size-1," size=",size)

    def create_mem(self,offset,size,write_callback):
        self.mem[(offset,size)]=buf_cb(None,write_callback)
        
    def set_mem_partial(self,add,buf):
        """returns the memory space (offset,size) if memory has been updated
        or None if the write is incomplete: some writes are still expected for this memory space
        """
        
        for (offset,size) in self.mem.keys():
            if add>=offset and add <offset+size:
                print("set_mem_partial:",add," in ",offset,size,"=",buf)
                if offset in self.mem_chunks:
                    self.mem_chunks[offset]+=buf
                    print("chunk is now=",self.mem_chunks[offset])
                else:
                    self.mem_chunks[offset]=buf
                print("set_mem_partial:",offset,size,"=",buf)
                if len(self.mem_chunks[offset])==size:
                    self.mem[(offset,size)].buf=self.mem_chunks[offset]
                    del self.mem_chunks[offset]
                    print("set_mem_partial done",self.mem_chunks)
                    if self.mem[(offset,size)].write_cback is not None:
                        self.mem[(offset,size)].write_cback(offset,self.mem[(offset,size)].buf)
                    return (offset,size)
                elif len(self.mem_chunks[offset])>size:
                    print("memory write error in set_mem_partial, chunk size is bigger than memory size at",offset)

        return None

    def set_mem(self,offset,buf):
        if (offset,len(buf)) in self.mem:
            print("set_mem(",offset,")=",buf)
            self.mem[(offset,len(buf))].buf=buf
            self.mem[(offset,len(buf))].write_cback(offset,self.mem[(offset,len(buf))].buf)
            return True
        
        print("set_mem failed, off=",offset,"buf=",buf," fo length=",len(buf))
        return False


    def read_mem(self,add):
        for (offset,size) in self.mem.keys():
            if add>=offset and add <offset+size:
                return self.mem[(offset,size)].buf[add-offset:]
        return None

    def mem_valid(self,offset):
        return offset not in self.mem_chunks
    
    def __str__(self):
        return str(self.mem)
    def dump(self):
        for (off,size) in self.mem:
            print("off=",off,"size=",size,"content=",self.mem[(off,size)].buf)

class node:
    def __init__(self,ID,permitted=False,aliasID=None):
        self.ID = ID
        self.aliasID = aliasID
        self.permitted=permitted
        self.produced_ev=[]
        self.consumed_ev=[]
        self.simple_info = []
        self.mem_space = None

    def add_consumed_ev(self,ev):
        self.consumed_ev.append(ev)

    def add_produced_ev(self,ev):
        self.produced_ev.append(ev)

    def set_simple_info(self,list):
        self.simple_info = list  #byte arrays

    def build_simple_info_dgram(self): # return datagrams holding the simple info
        print("build_simple_info not implemented!") #fixme
    