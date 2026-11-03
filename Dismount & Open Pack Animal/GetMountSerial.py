import API
API.SysMsg("Click directly inside Mount's open backpack window:", 88)
target = API.RequestTarget(timeout=10)
API.SysMsg(f"Backpack Container Serial: {hex(target)}", 68)