# scripts/get_session.py
# EK BAAR chala -> session.json ban jayega. Aage password ki zaroorat NAHI.
from instagrapi import Client

cl = Client()
cl.delay_range = [2, 5]   # requests ke beech 2-5 sec pause (ban se bachne ke liye)

user = input("IG burner username: ").strip()
pw   = input("IG burner password: ").strip()

try:
    cl.login(user, pw)
except Exception as e:
    # Instagram ne 2FA / verification manga toh yahan handle karenge
    print("Login challenge aaya:", e)
    code = input("2FA code (agar maanga ho, warna Enter): ").strip()
    if code:
        cl.two_factor_login(code)
    else:
        raise

cl.dump_settings("session.json")
print("✅ session.json ban gaya. Ab streamlit chala -> real comments aayenge.")