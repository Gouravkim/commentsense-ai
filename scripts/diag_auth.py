# scripts/diag_auth.py  ->  python scripts\diag_auth.py <shortcode>
import sys
from pathlib import Path
from instagrapi import Client

SHORTCODE = sys.argv[1] if len(sys.argv) > 1 else "DeRgykVzpzH"
sess = Path("session.json")
print(f"shortcode={SHORTCODE} | session_exists={sess.exists()}")

cl = Client(); cl.delay_range = [1, 2]
try:
    cl.load_settings(str(sess)); print("session loaded OK")
except Exception as e:
    print(f"FAIL load: {type(e).__name__}: {e}"); sys.exit(1)

print("-- login check --")
try:
    me = cl.account_info()
    print(f"LOGGED IN as {getattr(me, 'username', '?')}")
except Exception as e:
    print(f"LOGIN FAIL: {type(e).__name__}: {e}")
    print("=> SESSION DEAD. Fix: Remove-Item session.json; python scripts\\get_session.py")
    sys.exit(1)

print("-- media resolve --")
try:
    mid = cl.media_pk_from_code(SHORTCODE)
    print(f"media id = {mid}")
except Exception as e:
    print(f"RESOLVE FAIL: {type(e).__name__}: {e}")
    print("=> Ye post/reel deleted/private hai, ya session partially blocked.")
    sys.exit(1)

print("-- comments --")
try:
    res = cl.media_comments_chunk(mid, 50)
    print(f"chunk OK: {len(res[0])} comments, cursor={'yes' if res[1] else 'no'}")
except Exception as e:
    print(f"COMMENTS FAIL: {type(e).__name__}: {e}")
    sys.exit(1)

print("ALL GOOD -> app mein real comments aane chahiye.")