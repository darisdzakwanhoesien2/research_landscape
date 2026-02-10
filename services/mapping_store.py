# import json
# from pathlib import Path
# from datetime import datetime

# def save_mapping(mapping, output_dir: Path):
#     output_dir.mkdir(parents=True, exist_ok=True)

#     fname = f"mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#     path = output_dir / fname

#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(mapping, f, indent=2)

#     return path

import json
from pathlib import Path
from datetime import datetime

def save_mapping(mapping, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = output_dir / fname

    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    return path


def load_all_mappings(output_dir: Path):
    if not output_dir.exists():
        return []
    return list(output_dir.glob("*.json"))


# import json
# from pathlib import Path
# from datetime import datetime

# def save_mapping(mapping, output_dir: Path):
#     output_dir.mkdir(parents=True, exist_ok=True)
#     fname = f"mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#     path = output_dir / fname
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(mapping, f, indent=2)
#     return path

# def load_all_mappings(output_dir: Path):
#     if not output_dir.exists():
#         return []
#     return list(output_dir.glob("*.json"))