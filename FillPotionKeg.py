import API
import time

API.SysMsg("Click your Mortar & Pestle in your backpack...", 88)
mortar_serial = API.RequestTarget(timeout=10)

if not mortar_serial or mortar_serial == 0:
    API.SysMsg("No mortar targeted. Stopping.", 32)
    API.Stop()

API.SysMsg("Potion Keg Filling script running! Toggle hotkey to stop.", 68)

while not API.StopRequested:
    # 1. Double-click the mortar
    API.UseObject(mortar_serial)
    
    # 2. Short pause for menu packet to load
    time.sleep(0.5)

    # 3. Check if the menu notice says we need bottles or resources
    if API.GumpContains("bottle") or API.GumpContains("reagents") or API.GumpContains("resources"):
        API.SysMsg("Keg is full or out of supplies! Stopping script.", 68)
        break

    # 4. Click Make Last (Button 21)
    API.ReplyGump(21)

    # 5. Wait for alchemy brewing delay (~1.8s)
    time.sleep(1.8)

    # 6. Fallback journal check in case server sends text there too
    recent = " ".join([e.Text.lower() for e in list(API.JournalEntries)[-5:]])
    if "keg is now full" in recent or "will not hold any more" in recent:
        API.SysMsg("Keg is full! Stopping script.", 68)
        break

API.SysMsg("Potion script stopped.", 88)