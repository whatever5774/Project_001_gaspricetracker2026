with open('full_log.txt', 'r', encoding='utf-16le') as f:
    text = f.read()

with open('full_log_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(text)
