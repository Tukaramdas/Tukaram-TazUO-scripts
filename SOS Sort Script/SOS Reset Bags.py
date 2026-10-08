import API

SECTOR_KEYS = ["N_W", "N_MID", "N_E", "MID_W", "MID_MID", "MID_E", "S_W", "S_MID", "S_E"]

for key in SECTOR_KEYS:
    API.RemovePersistentVar(f"SOS_POUCH_{key}", API.PersistentVar.Char)

API.SysMsg("SOS pouch memory cleared! Ready for new bags.", 68)