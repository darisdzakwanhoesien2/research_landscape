from datetime import datetime
from pathlib import Path
import json

def write_audit_log(log_dir: Path, payload: dict):
    log_dir.mkdir(parents=True, exist_ok=True)
    fname = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = log_dir / fname

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return path


# from datetime import datetime
# import json
# from pathlib import Path

# def write_audit_log(log_dir: Path, payload: dict):
#     log_dir.mkdir(parents=True, exist_ok=True)

#     fname = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#     path = log_dir / fname

#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(payload, f, indent=2)

#     return path
