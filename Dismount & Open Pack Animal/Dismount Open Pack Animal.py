import API
import time

# 1. Dismount
API.Dismount()
time.sleep(0.35)

# 2. Open Mounts's backpack directly
API.UseObject(0x401f9475)