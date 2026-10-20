# scripts/test_auth_fetch.py  (v3 - sirf CONFIRMED 3.0.21 names)
import sys
from pathlib import Path
from instagrapi import Client

SHORTCODE = "DeRgykVzpzH"
URL = "https://www.instagram.com/reel/DeRgykVzpzH/"
AMOUNT = 50

sess = Path("session.json")
print(f"[1] session.json exists? {sess.exists()}")
if not sess.exists():
    print("FAIL: session.json nahi mila"); sys.exit(1)

cl = Client(); cl.delay_range = [2, 5]

print("[2] Loading session...")
try:
    cl.load_settings(str(sess)); print("    session loaded OK")
except Exception as e:
    print(f"    FAIL load_settings: {type(e).__name__}: {e}"); sys.exit(1)

# LOGIN CHECK -> account_info (3.x ka sahi method)
print("[3] Login check via account_info()...")
try:
    me = cl.account_info()
    print(f"    LOGGED IN as: {getattr(me,'username','?')} (pk={getattr(me,'pk','?')})")
except Exception as e:
    print(f"    NOT logged in: {type(e).__name__}: {e}")
    print("    -> session delete karke get_session.py dobara chala."); sys.exit(1)

# RESOLVE media id (multi-variant)
print(f"[4] Resolve media id for shortcode={SHORTCODE}")
media_id = None; errs = []
for name, fn in [
    ("media_pk_from_code", lambda: cl.media_pk_from_code(SHORTCODE)),
    ("media_id",           lambda: cl.media_id(SHORTCODE)),
    ("media_pk_from_url",  lambda: cl.media_pk_from_url(URL)),
]:
    try:
        media_id = fn()
        if media_id:
            print(f"    OK via {name} -> id={media_id}"); break
    except Exception as e:
        errs.append(f"{name}: {type(e).__name__}: {e}")
if not media_id:
    print("    FAIL resolve id -> " + " | ".join(errs)); sys.exit(1)

# FETCH comments (multi-variant)
print("[5] Fetch comments...")
raw = None; cerrs = []
for name, fn in [
    ("media_comments(pos)",  lambda: cl.media_comments(media_id, amount=AMOUNT)),
    ("media_comments_gql",   lambda: cl.media_comments_gql(media_id, amount=AMOUNT)),
    ("media_comments_v1",    lambda: cl.media_comments_v1(media_id, amount=AMOUNT)),
    ("media_comments(kw)",   lambda: cl.media_comments(media_id=media_id, amount=AMOUNT)),
]:
    try:
        raw = fn()
        if raw:
            print(f"    OK via {name} -> {len(raw)} raw comments"); break
        else:
            cerrs.append(f"{name}: empty")
    except Exception as e:
        cerrs.append(f"{name}: {type(e).__name__}: {e}")
if not raw:
    print("    FAIL comments -> " + " | ".join(cerrs[-4:])); sys.exit(1)

# PRINT first 5 with ROBUST user extraction
print("[6] Sample comments:")
for c in raw[:5]:
    text = (getattr(c, "text", "") or "").strip()
    u = getattr(c, "user", None)
    user = (getattr(u, "username", None) or getattr(u, "user_name", None)
            or getattr(c, "user_name", None) or getattr(c, "username", None))
    print(f"   - [{user}] {text[:90]}")

print("\nRESULT: [3][4][5][6] OK = session THEEK, REAL comments mil rahe hain.")
print("Ab streamlit chalane pe bhi real comments aane chahiye (providers.py same chain use karega).")