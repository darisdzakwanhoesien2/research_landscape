from utils.text_normalizer import normalize_text
from utils.similarity import similarity

def entry_to_text(e):
    fields = [
        e.get("title", ""),
        e.get("author", ""),
        e.get("journal", ""),
        e.get("booktitle", ""),
        e.get("year", "")
    ]
    return normalize_text(" ".join(fields))

def match_entries(generated, groundtruth):
    gt_texts = [(g, entry_to_text(g)) for g in groundtruth]
    results = []

    for gen in generated:
        gen_text = entry_to_text(gen)

        best = None
        best_score = 0

        for gt, gt_text in gt_texts:
            score = similarity(gen_text, gt_text)
            if score > best_score:
                best = gt
                best_score = score

        results.append({
            "generated_id": gen.get("ID"),
            "groundtruth_id": best.get("ID") if best else None,
            "score": round(best_score, 3),
            "generated_title": gen.get("title"),
            "groundtruth_title": best.get("title") if best else None
        })

    return results


# from utils.text_normalizer import normalize_text
# from utils.similarity import similarity

# def entry_to_text(e):
#     fields = [
#         e.get("title", ""),
#         e.get("author", ""),
#         e.get("journal", ""),
#         e.get("booktitle", ""),
#         e.get("year", "")
#     ]
#     return normalize_text(" ".join(fields))

# def match_entries(generated, groundtruth):
#     gt_texts = [(g, entry_to_text(g)) for g in groundtruth]
#     results = []

#     for gen in generated:
#         gen_text = entry_to_text(gen)

#         best = None
#         best_score = 0

#         for gt, gt_text in gt_texts:
#             score = similarity(gen_text, gt_text)
#             if score > best_score:
#                 best = gt
#                 best_score = score

#         results.append({
#             "generated_id": gen.get("ID"),
#             "groundtruth_id": best.get("ID") if best else None,
#             "score": round(best_score, 3),
#             "generated_title": gen.get("title"),
#             "groundtruth_title": best.get("title") if best else None
#         })

#     return results


# from utils.text_normalizer import normalize_text
# from utils.similarity import similarity

# def entry_to_text(e):
#     fields = [
#         e.get("title", ""),
#         e.get("author", ""),
#         e.get("journal", ""),
#         e.get("booktitle", ""),
#         e.get("year", "")
#     ]
#     return normalize_text(" ".join(fields))

# def match_entries(generated, groundtruth, threshold=0.75):
#     results = []

#     gt_texts = [(g, entry_to_text(g)) for g in groundtruth]

#     for gen in generated:
#         gen_text = entry_to_text(gen)

#         best = None
#         best_score = 0

#         for gt, gt_text in gt_texts:
#             score = similarity(gen_text, gt_text)
#             if score > best_score:
#                 best = gt
#                 best_score = score

#         results.append({
#             "generated_id": gen.get("ID"),
#             "groundtruth_id": best.get("ID") if best else None,
#             "score": round(best_score, 3),
#             "generated_title": gen.get("title"),
#             "groundtruth_title": best.get("title") if best else None
#         })

#     return results