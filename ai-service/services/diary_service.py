_sessions: dict[str, list[dict]] = {}

def add_turn(sid: str, text: str, child: bool, audio_url: str | None):
    _sessions.setdefault(sid, []).append({"text": text, "child": child, "audio_url": audio_url})
    return {"turns": len(_sessions[sid])}

def compose(sid: str, with_memory: bool = True, top_k: int = 5, recent_days: int | None = 90):
    turns = _sessions.get(sid, [])
    child_turns = sum(1 for t in turns if t["child"])
    diary = " ".join(t["text"] for t in turns) or "오늘은 특별한 일이 없었어요."
    return {"diary": diary, "child_turns": child_turns, "memory_hits": None, "mood": None}
