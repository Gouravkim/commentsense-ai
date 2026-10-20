# scripts/inspect_api.py
# Guess nahi karta. Library khud batati hai uske paas kya methods hain.
import instagrapi
from instagrapi import Client

print(f"instagrapi version: {getattr(instagrapi, '__version__', 'unknown')}")
print("=" * 60)

cl = Client()
attrs = dir(cl)

KEYWORDS = ("media", "comment", "shortcode", "pk", "user", "self", "account", "info", "by_", "id")

hits = []
for a in attrs:
    low = a.lower()
    if any(k in low for k in KEYWORDS):
        obj = getattr(cl, a, None)
        kind = "method" if callable(obj) else "attr/property"
        hits.append((a, kind))

hits.sort()
print(f"\n[{len(hits)} matching members on Client]\n")
for name, kind in hits:
    print(f"  {kind:14s}  {name}")

# Specifically: media + comment wale alag se highlight
print("\n" + "=" * 60)
print("MEDIA-related methods:")
for name, kind in hits:
    if "media" in name.lower() and kind == "method":
        print(f"   -> {name}")

print("\nCOMMENT-related methods:")
for name, kind in hits:
    if "comment" in name.lower() and kind == "method":
        print(f"   -> {name}")

print("\nUSER/SELF-related methods:")
for name, kind in hits:
    if ("user" in name.lower() or "self" in name.lower() or "account" in name.lower()) and kind == "method":
        print(f"   -> {name}")