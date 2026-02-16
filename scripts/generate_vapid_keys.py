"""Generate VAPID keys for web push notifications.

Usage:
  python scripts/generate_vapid_keys.py
"""

from py_vapid import Vapid01

vapid = Vapid01()
private_key = vapid.generate_keys()
public_key = vapid.public_key

print("VAPID_PUBLIC_KEY=", public_key)
print("VAPID_PRIVATE_KEY=", private_key)
print("VAPID_SUBJECT=mailto:admin@metabolicos.app")
