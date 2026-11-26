#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Small, deterministic Matroska file; actual extractor, no transcoding tool."""
import struct

def size(n):
    for k in range(1,9):
        if n < (1<<(7*k))-1:
            return (n | (1<<(7*k))).to_bytes(k,"big")
    raise ValueError("EBML size")

def e(tag,b):
    return bytes.fromhex(tag)+size(len(b))+b

def u(tag,n):
    return e(tag,n.to_bytes(max(1,(n.bit_length()+7)//8),"big"))

def t(tag,s):
    return e(tag,s.encode("utf-8"))

HEADER=("[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    "Style: Default,DejaVu Sans,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,10,10,10,1\n"
    "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n").encode()

def track(n,codec,language):
    return e("AE",u("D7",n)+u("73C5",n)+u("83",17)+u("9C",0)+t("86",codec)+t("22B59C",language)
        +(e("63A2",HEADER) if codec=="S_TEXT/ASS" else b""))

def block(n,at,duration,payload):
    return e("A0",e("A1",bytes([0x80|n])+struct.pack(">hB",at,0)+payload)
        +(u("9B",duration) if duration is not None else b""))

def build(font):
    header=e("1A45DFA3",u("4286",1)+u("42F7",1)+u("42F2",4)+u("42F3",8)+t("4282","matroska")+u("4287",4)+u("4285",2))
    info=e("1549A966",u("2AD7B1",1000000)+e("4489",struct.pack(">d",5500.0))+t("4D80","FingMi fixture")+t("5741","FingMi fixture"))
    attach=e("1941A469",e("61A7",t("466E","DejaVuSans.ttf")+t("4660","application/x-truetype-font")+e("465C",font)+u("46AE",1)))
    tracks=e("1654AE6B",track(1,"S_TEXT/ASS","eng")+track(2,"S_TEXT/ASS","jpn")+track(3,"S_TEXT/UTF8","eng"))
    cluster=e("1F43B675",u("E7",0)+
        block(1,1230,570,b"0,0,Default,,0,0,0,,First actual subtitle")+
        block(2,2000,600,b"0,0,Default,,0,0,0,,Independent other subtitle")+
        block(1,3000,500,b"1,0,Default,,0,0,0,,Second actual subtitle")+
        block(3,4000,500,b"Ordinary SRT")+
        block(1,4500,None,b"2,0,Default,,0,0,0,,Never publish missing duration"))
    return header+e("18538067",info+attach+tracks+cluster)
