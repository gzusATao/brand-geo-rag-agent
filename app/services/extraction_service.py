"""保守规则提取基线，不能代替人工标注或模型语义判断。"""

import re


def extract_brands(answer, project):
    results = []
    brands = [(project["brand"], [project["brand"], *project["aliases"]])]
    brands.extend((name, [name]) for name in project["competitors"])
    for brand, aliases in brands:
        evidence = []
        recommended = False
        ranks = []
        for line in re.split(r"[\n。！？!?；;]+", answer):
            for clause in re.split(r"[，,]+|(?:但是|但|不过)", line):
                if not any(matches_name(clause, name) for name in aliases):
                    continue
                snippet = clause.strip()
                if snippet and snippet not in evidence:
                    evidence.append(snippet)
                # 对否定、引述和条件语气不作明确推荐判断，宁可漏检也不制造推荐。
                positive = bool(re.search(r"推荐|首选|优先选择", clause))
                ambiguous = bool(re.search(r"不|未|无|避免|慎|是否|如果|假如|声称|自称|有人说|据说", clause))
                if positive and not ambiguous:
                    recommended = True
                    match = re.match(r"\s*(\d{1,2})[.、)）]\s*", line)
                    if match and int(match[1]) >= 1:
                        ranks.append(int(match[1]))
        results.append(
            {
                "brand": brand,
                "mentioned": bool(evidence),
                "recommended": recommended,
                "rank": min(ranks) if ranks else None,
                "evidence": evidence,
            }
        )
    return results


def matches_name(text, name):
    if re.fullmatch(r"[A-Za-z0-9 _.-]+", name):
        return bool(re.search(r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])", text, re.I))
    return name.casefold() in text.casefold()
