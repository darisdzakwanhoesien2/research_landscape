import re

def extract_citations(text: str):
    pattern = r"\\(cite|citep|citet)\{([^}]+)\}"
    matches = re.findall(pattern, text)

    keys = set()
    for _, block in matches:
        for k in block.split(","):
            keys.add(k.strip())

    return sorted(keys)

def patch_latex(text: str, mapping: dict):
    def repl(match):
        cmd = match.group(1)
        keys = match.group(2)

        new_keys = []
        for k in keys.split(","):
            k = k.strip()
            new_keys.append(mapping.get(k, k))

        return f"\\{cmd}{{{','.join(new_keys)}}}"

    pattern = r"\\(cite|citep|citet)\{([^}]+)\}"
    return re.sub(pattern, repl, text)


# import re

# def extract_citations(text: str):
#     pattern = r"\\(cite|citep|citet)\{([^}]+)\}"
#     matches = re.findall(pattern, text)

#     keys = set()
#     for _, block in matches:
#         for k in block.split(","):
#             keys.add(k.strip())

#     return sorted(keys)

# def patch_latex(text: str, mapping: dict):
#     """
#     mapping = {generated_key: groundtruth_key}
#     Supports multi-key citations.
#     """

#     def repl(match):
#         cmd = match.group(1)
#         keys = match.group(2)

#         new_keys = []
#         for k in keys.split(","):
#             k = k.strip()
#             new_keys.append(mapping.get(k, k))

#         return f"\\{cmd}{{{','.join(new_keys)}}}"

#     pattern = r"\\(cite|citep|citet)\{([^}]+)\}"
#     return re.sub(pattern, repl, text)


# import re

# def patch_latex(text: str, mapping: dict):
#     """
#     mapping = {generated_key: groundtruth_key}
#     """
#     def repl(match):
#         key = match.group(1)
#         return f"\\cite{{{mapping.get(key, key)}}}"

#     return re.sub(r"\\cite\{([^}]+)\}", repl, text)