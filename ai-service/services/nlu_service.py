def check_animal(utterance: str, answer: str):
    ok = answer in utterance
    return {"correct": ok, "matched": answer if ok else None, "note": None}

def check_twentyq(utterance: str, answer: str):
    return {"correct": answer in utterance}
