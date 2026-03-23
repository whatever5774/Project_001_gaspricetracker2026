"""
测试与调试辅助脚本：用于测试各个独立组件与流程的行为 (Test/Debug Script)
"""
import requests, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}
res = requests.get('https://www.costco.com/warehouse-locations?zipCode=91709', headers=headers, timeout=10)
text = res.text

# They usually embed an array or JSON somewhere, find anything looking like gas prices
# e.g., "regularPrice":"3.89"
matches = re.finditer(r'(.{0,60}3\.\d{2}.{0,60})', text)
for i, m in enumerate(matches):
    print(m.group(1))
    if i > 5: break
