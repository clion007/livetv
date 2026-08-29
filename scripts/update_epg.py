#!/usr/bin/env python3
"""
EPG 更新脚本 - 从 vip.erw.cc 获取节目单，将 tvg-id 从数字ID替换为频道名
"""

import xml.etree.ElementTree as ET
import urllib.request
import os
import sys
from datetime import datetime

# 配置
EPG_URL = "https://vip.erw.cc/all.xml"
OUTPUT_PATH = "epg/china.xml"  # 相对于仓库根目录

def download_epg(url):
    """下载 EPG XML 文件"""
    print(f"[{datetime.now()}] 正在下载: {url}")
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
            print(f"[{datetime.now()}] 下载成功，大小: {len(data)} 字节")
            return data
    except Exception as e:
        print(f"[{datetime.now()}] 下载失败: {e}")
        sys.exit(1)

def parse_and_replace(xml_data):
    """解析 XML，建立 ID->名称 映射，然后替换所有 tvg-id"""
    # 解析 XML（保留注释）
    tree = ET.ElementTree(ET.fromstring(xml_data))
    root = tree.getroot()

    # 第一步：建立 数字ID -> tvg-name 的映射
    id_to_name = {}
    channels = root.findall('channel')
    print(f"[{datetime.now()}] 找到 {len(channels)} 个频道")

    for channel in channels:
        channel_id = channel.get('id', '')
        tvg_name = channel.get('tvg-name', '')
        if channel_id and tvg_name:
            id_to_name[channel_id] = tvg_name

    print(f"[{datetime.now()}] 建立了 {len(id_to_name)} 个 ID->名称 映射")

    # 第二步：替换所有 channel 标签的 id 属性
    for channel in channels:
        old_id = channel.get('id', '')
        if old_id in id_to_name:
            new_id = id_to_name[old_id]
            channel.set('id', new_id)
            # 同时更新 tvg-id（如果有的话）
            if channel.get('tvg-id'):
                channel.set('tvg-id', new_id)

    # 第三步：替换所有 programme 标签的 channel 属性
    programmes = root.findall('programme')
    print(f"[{datetime.now()}] 找到 {len(programmes)} 个节目条目")

    replaced_count = 0
    for prog in programmes:
        old_channel = prog.get('channel', '')
        if old_channel in id_to_name:
            new_channel = id_to_name[old_channel]
            prog.set('channel', new_channel)
            replaced_count += 1

    print(f"[{datetime.now()}] 替换了 {replaced_count} 个节目条目的 channel 属性")

    return tree

def save_xml(tree, output_path):
    """保存 XML 文件"""
    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入文件（带 XML 声明和美化）
    with open(output_path, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        tree.write(f, encoding='utf-8', xml_declaration=False)

    print(f"[{datetime.now()}] 已保存到: {output_path}")

def main():
    print(f"[{datetime.now()}] === EPG 更新脚本开始 ===")

    # 下载
    xml_data = download_epg(EPG_URL)

    # 解析并替换
    tree = parse_and_replace(xml_data)

    # 保存
    save_xml(tree, OUTPUT_PATH)

    print(f"[{datetime.now()}] === EPG 更新脚本完成 ===")

if __name__ == "__main__":
    main()