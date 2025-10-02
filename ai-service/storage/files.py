# storage/files.py
# 예시: S3 혹은 NCP Object Storage 업로드 후 공개 URL 리턴
def save_bytes(path: str, data: bytes, content_type: str) -> str:
    # 업로드 구현 …
    return f"https://cdn.example.com/{path}"