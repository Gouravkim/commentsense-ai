# scripts/probe_pagination.py
import sys
from pathlib import Path
from instagrapi import Client

SHORTCODE = "DeTtWmjtZia"   # tera 1.4k wala POST (reel nahi, /p/ wala)
AMOUNT = 300

sess = Path("session.json")
if not sess.exists():
    print("session.json nahi mila"); sys.exit(1)

cl = Client(); cl.delay_range = [1, 2]
cl.load_settings(str(sess))

# resolve id
mid = None
for nm, fn in [("media_pk_from_code", lambda: cl.media_pk_from_code(SHORTCODE)),
               ("media_id", lambda: cl.media_id(SHORTCODE))]:
    try:
        mid = fn()
        if mid: print(f"id via {nm} -> {mid}"); break
    except Exception as e:
        print(f"{nm} err: {type(e).__name__}: {e}")
if not mid:
    print("id resolve fail"); sys.exit(1)

def shape(label, res):
    t = type(res).__name__
    n = len(res) if hasattr(res, "__len__") else "?"
    cursors = {}
    for attr in ("next_max_id","max_id","cursor","next_cursor"):
        v = getattr(res, attr, None)
        if v is not None: cursors[attr] = repr(v)[:40]
    if isinstance(res, tuple):
        cursors["is_tuple_len"] = len(res)
        for i,part in enumerate(res):
            if hasattr(part,"__len__"): cursors[f"tuple[{i}]_len"] = len(part)
    print(f"  {label}: type={t} len={n} extra={cursors}")

print("\n--- candidate methods (amount=%d) ---" % AMOUNT)
for nm in ["media_comments","media_comments_gql","media_comments_v1",
           "media_comments_chunk","media_comments_gql_chunk","media_comments_v1_chunk",
           "media_comments_threaded_gql"]:
    fn = getattr(cl, nm, None)
    if not callable(fn):
        print(f"  {nm}: NOT callable"); continue
    for args, kw in [((mid, AMOUNT), {}), ((mid,), {"amount": AMOUNT}), ((mid,), {})]:
        try:
            res = fn(*args, **kw)
            shape(f"{nm}{args}{kw}", res)
            break
        except TypeError as e:
            print(f"  {nm}{args}{kw}: TypeError(sig) {e}")
        except Exception as e:
            print(f"  {nm}{args}{kw}: {type(e).__name__}: {str(e)[:90]}")

print("\n>>> In lines ko copy karke bhej de. Cursor ka naam + kaunsa method kitne deta hai, isi se exact pagination likhunga.")