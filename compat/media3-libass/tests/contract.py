"""Read actual ELF JNINativeMethod records (ARM REL or arm64 RELA), no symbol-name guesses."""
import struct
class ELF:
 def __init__(self,data):
  self.data=data;assert data[:4]==b'\x7fELF' and data[5]==1
  self.bits=32 if data[4]==1 else 64;self.word=self.bits//8;self.ptr='<I' if self.bits==32 else '<Q'
  self.machine=struct.unpack_from('<H',data,18)[0]
  if self.bits==32:off=struct.unpack_from('<I',data,32)[0];size,count=struct.unpack_from('<HH',data,46);fmt='<IIIIIIIIII'
  else:off=struct.unpack_from('<Q',data,40)[0];size,count=struct.unpack_from('<HH',data,58);fmt='<IIQQQQIIQQ'
  self.sections=[struct.unpack_from(fmt,data,off+i*size) for i in range(count)]
  self.relocations={}
  for s in self.sections:
   if s[1]==4:
    for pos in range(s[4],s[4]+s[5],s[9]):
     target,info,addend=struct.unpack_from('<QQq',data,pos)
     if info&0xffffffff==1027:self.relocations[target]=addend # R_AARCH64_RELATIVE
 def offset(self,address):
  for s in self.sections:
   if s[1]!=8 and s[3]<=address<s[3]+s[5]:return s[4]+address-s[3]
  raise ValueError('unmapped address')
 def pointer(self,address):
  return self.relocations.get(address,struct.unpack_from(self.ptr,self.data,self.offset(address))[0])
 def string(self,address):
  p=self.offset(address);end=self.data.index(b'\0',p,p+256);return self.data[p:end].decode('ascii')
 def methods(self):
  rows=[]
  for s in self.sections:
   if not s[2]&2 or s[1]==8:continue
   for address in range(s[3],s[3]+s[5]-3*self.word+1,self.word):
    try:
     name=self.string(self.pointer(address));sig=self.string(self.pointer(address+self.word));fn=self.pointer(address+2*self.word)
     if not name.startswith('native') or not sig.startswith('('):continue
     if not any(sec[2]&4 and sec[3]<=(fn&~1)<sec[3]+sec[5] for sec in self.sections):continue
     rows.append(dict(name=name,descriptor=sig,function=hex(fn),table=hex(address)))
    except (ValueError,UnicodeDecodeError,struct.error):pass
  assert rows,'No JNINativeMethod records found'
  assert len({r['name'] for r in rows})==len(rows),'Duplicate native methods'
  return sorted(rows,key=lambda r:r['name'])
