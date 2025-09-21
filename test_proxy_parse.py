#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理解析测试脚本
"""

def test_proxy_parse(proxy_str):
    """测试代理字符串解析"""
    print(f"原始代理字符串: {proxy_str}")
    
    try:
        parts = proxy_str.split(':')
        
        if len(parts) < 2:
            print("❌ 格式错误: 至少需要 host:port")
            return False
            
        host = parts[0]
        port = parts[1]
        username = ""
        password = ""
        
        if len(parts) >= 3:
            username = parts[2]
            if len(parts) >= 4:
                password = parts[3]
                
        print(f"✅ 解析成功:")
        print(f"   主机: {host}")
        print(f"   端口: {port}")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return False

if __name__ == "__main__":
    # 测试你提供的代理格式
    test_cases = [
        "na.proxys5.net:6200:15782341-zone-custom-sessid-OgL2jBhC-sessTime-15:Rk3dOqxE",
        "127.0.0.1:1080",
        "proxy.example.com:8080:user:pass",
        "invalid_format"
    ]
    
    print("🧪 代理解析测试")
    print("=" * 50)
    
    for i, proxy in enumerate(test_cases, 1):
        print(f"测试 {i}:")
        test_proxy_parse(proxy)
        print("-" * 30)