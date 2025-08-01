import ssl
import urllib.request

try:
    response = urllib.request.urlopen("https://github.com", timeout=5)
    print("✅ 访问 GitHub 成功")
except Exception as e:
    print("❌ 无法访问 GitHub：", e)


