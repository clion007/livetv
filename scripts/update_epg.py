#!/usr/bin/env python3
"""
EPG 更新脚本
从 kuke31/xmlgz 获取7天回看EPG，将 tvg-id 从数字ID替换为频道名（取自display-name），
清理无效数据，并重排为【先频道列表、后节目列表】的标准格式。
"""

import xml.etree.ElementTree as ET
import urllib.request
import gzip
import io
import os
import sys
from datetime import datetime

EPG_URL = "https://raw.githubusercontent.com/kuke31/xmlgz/main/all.xml.gz"
OUTPUT_PATH = "epg/china.xml"

def download_and_decompress(url):
    print(f"[{datetime.now()}] 正在下载: {url}")
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            compressed_data = response.read()
            print(f"[{datetime.now()}] 下载成功，压缩包大小: {len(compressed_data)} 字节")
            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                xml_data = gz.read().decode('utf-8')
            print(f"[{datetime.now()}] 解压成功，XML 大小: {len(xml_data)} 字节")
            return xml_data
    except Exception as e:
        print(f"[{datetime.now()}] 下载或解压失败: {e}")
        sys.exit(1)

def parse_and_replace(xml_str):
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f"[{datetime.now()}] XML 解析失败: {e}")
        sys.exit(1)

    # ---- 第一步：建立 数字ID → 频道名 的映射 ----
    id_to_name = {}
    channels = root.findall('channel')
    print(f"[{datetime.now()}] 找到 {len(channels)} 个频道")

    for ch in channels:
        cid = ch.get('id', '')
        # 从 <display-name> 中提取频道名
        display_name_elem = ch.find('display-name')
        if display_name_elem is not None and display_name_elem.text:
            name = display_name_elem.text.strip()
        else:
            # 如果没有 display-name，尝试 tvg-name 属性（兼容）
            name = ch.get('tvg-name', '').strip()
        if cid and name:
            id_to_name[cid] = name

    print(f"[{datetime.now()}] 建立了 {len(id_to_name)} 个映射（数字ID → 频道名）")

    # ---- 第二步：替换所有 channel 标签自身的 id ----
    for ch in channels:
        old_id = ch.get('id', '')
        if old_id in id_to_name:
            new_id = id_to_name[old_id]
            ch.set('id', new_id)
            # 同时更新 tvg-id（如果有）
            if ch.get('tvg-id'):
                ch.set('tvg-id', new_id)

    # ---- 第三步：替换所有 programme 的 channel 属性 ----
    all_progs = root.findall('programme')
    print(f"[{datetime.now()}] 找到 {len(all_progs)} 个节目条目")
    replaced = 0
    for prog in all_progs:
        old_ch = prog.get('channel', '')
        if old_ch in id_to_name:
            prog.set('channel', id_to_name[old_ch])
            replaced += 1
    print(f"[{datetime.now()}] 替换了 {replaced} 个节目条目的 channel")

    # ---- 第四步：删除 channel="9999" 的无意义节目 ----
    to_remove = [p for p in root.findall('programme') if p.get('channel') == '9999']
    for p in to_remove:
        root.remove(p)
    print(f"[{datetime.now()}] 删除了 {len(to_remove)} 个无效节目 (channel=9999)")

    # ---- 第五步：重排为【先频道、后节目】的标准结构 ----
    # 注意：此时 channel 的 id 已经变成频道名，programme 的 channel 也变成了频道名
    ch_elems = [e for e in root if e.tag == 'channel']
    prog_elems = [e for e in root if e.tag == 'programme']
    root[:] = ch_elems + prog_elems
    print(f"[{datetime.now()}] 重排完成：{len(ch_elems)} 个频道在前，{len(prog_elems)} 个节目在后")

    return ET.ElementTree(root)

def save_xml(tree, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        tree.write(f, encoding='utf-8', xml_declaration=False)
    print(f"[{datetime.now()}] 已保存到: {path}")

def main():
    print(f"[{datetime.now()}] === EPG 更新脚本开始 ===")
    xml_str = download_and_decompress(EPG_URL)
    tree = parse_and_replace(xml_str)
    save_xml(tree, OUTPUT_PATH)
    print(f"[{datetime.now()}] === EPG 更新脚本完成 ===")

if __name__ == "__main__":
    main()