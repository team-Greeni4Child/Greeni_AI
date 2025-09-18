def reply(sid: str, user_text: str, with_memory: bool, top_k: int, recent_days: int | None, style: str | None):
    return {"reply": f"알겠어! 너는 이렇게 말했지: {user_text}"}
