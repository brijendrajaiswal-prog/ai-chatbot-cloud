from pathlib import Path

path = Path(r"C:\AIChatbot\hindi_text.txt")
text = path.read_text(encoding="utf-8")

print("Text:", text)
print("Unicode code points:", [hex(ord(char)) for char in text])
print("UTF-8 bytes:", text.encode("utf-8"))
print("Contains surrogate:", any(
    0xD800 <= ord(char) <= 0xDFFF for char in text
))