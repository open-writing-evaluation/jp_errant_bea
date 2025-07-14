import json
import math
import bisect
import numpy as np
from functools import cache, cached_property
from tqdm import tqdm
from contextlib import ExitStack
from jp_errant.reindex import *
import re
from collections import Counter

WORD = re.compile(r"\w+")

def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)

class MatchProb:
    MAX_MATCH = 11
    def __init__(self):
        v_size = (MatchProb.MAX_MATCH + 1)*MatchProb.MAX_MATCH//2 + 1
        with open("jp_errant/match_probs.json", encoding='utf-8') as json_file:
            self.prob = json.load(json_file)
        self.total = sum([val for val in self.prob.values()]) + v_size
        for key in self.prob:
            self.prob[key] = math.log(self.prob[key] + 1/self.total)
        self.prob["-1"] = math.log(1/self.total)

    def __getitem__(self, key):
        len1 = min(key)
        len2 = max(key)
        if str((len1, len2)) in self.prob:
            return self.prob[str((len1, len2))]
        else:
            #Laplace smoothing
            return self.prob["-1"]


def pnorm(z):
    t = 1 / (1 + 0.2316419 * z)
    return 1 - 0.3989423 * math.exp(-z**2 / 2) * \
        ((((1.330274429 * t - 1.821255978) * t + 1.781477937) * t - 0.356563782) * t + 0.319381530) * t

@cache
def match(len1, len2):
    c = 1
    s2 = 6.8

    if len1 == 0 and len2 == 0:
        return 0
    mean = (len1 + len2 / c) / 2
    z = (c * len1 - len2) / math.sqrt(s2 * mean)
    if z < 0:
        z = -z
    pd = 2 * (1 - pnorm(z))
    if pd > 0:
        return -math.log(pd)
    return 25

def match_sent(P1, P2):
    match_pair = {}
    multi_match = set()
    for idx, s in enumerate(P1):
        if s not in match_pair and s not in multi_match:
            match_pair[s] = [idx, -1]
        else:
            multi_match.add(s)
            if s in match_pair:
                match_pair.pop(s)

    for idx, s in enumerate(P2):
        if s in match_pair:
            if match_pair[s][1] == -1 and s not in multi_match:
                match_pair[s][1] = idx
            else:
                multi_match.add(s)
                match_pair[s][1] = -1

    match_ids = list()
    for s, idx in match_pair.items():
        if idx[0] != -1 and idx[1] != -1:
            match_ids.append([idx[0], idx[1]])
    match_ids = sorted(match_ids)
    
    return match_ids


def get_paragraphs(sys_sent, gold_sent):
    sys_sent = [s.strip() for s in sys_sent]
    gold_sent = [s.strip() for s in gold_sent]
    match_ids = match_sent(sys_sent, gold_sent)

    i = 0
    j = 0
    sys_paragraphs = []
    gold_paragraphs = []
    for pair in match_ids:
        temp_sys = []
        temp_gold = []
        while i < pair[0]:
            temp_sys.append(sys_sent[i])
            i += 1
        while j < pair[1]:
            temp_gold.append(gold_sent[j])
            j += 1
        if len(temp_sys) > 0 or len(temp_gold) > 0:
            sys_paragraphs.append(temp_sys)
            gold_paragraphs.append(temp_gold)
        
        sys_paragraphs.append([sys_sent[pair[0]]])
        gold_paragraphs.append([gold_sent[pair[1]]])
        i += 1
        j += 1

    return sys_paragraphs, gold_paragraphs


def paragraph_align(sys_sent, gold_sent):
    
    match_prob = MatchProb()
    
    sys_len = [0]
    for _, line in enumerate(sys_sent):
        line = line.replace(" ", "").replace("\n", "")
        sys_len.append(sys_len[-1] + len(line))

    gold_len = [0]
    for _, line in enumerate(gold_sent):
        line = line.replace(" ", "").replace("\n", "")
        gold_len.append(gold_len[-1] + len(line))

    cost = np.full((len(sys_sent)+1, len(gold_sent)+1), float('inf'))
    back = np.empty((len(sys_sent)+1, len(gold_sent)+1), dtype=object)

    cost[0][0] = 0
    for i in range(len(sys_sent)+1):
        for j in range(0, len(gold_sent) + 1):
            if i + j == 0:
                continue

            prev_i = 0
            prev_j = 0
            temp_cost = cost[prev_i][prev_j] - match_prob[i-prev_i, j-prev_j] + match(sys_len[i] - sys_len[prev_i], gold_len[j] - gold_len[prev_j])
            temp_prev = (prev_i, prev_j)

            for x in range(i, prev_i - 1, -1):
                for y in range(j, prev_j - 1, -1):
                    if (x==i and y==j) or (x==prev_i and y==prev_j):
                        continue
                    temp_cost2 = cost[x][y] - match_prob[i-x, j-y] + match(sys_len[i] - sys_len[x], gold_len[j] - gold_len[y])
                    if temp_cost2 < temp_cost:
                        temp_cost = temp_cost2
                        temp_prev = (x, y)

            cost[i][j] = temp_cost
            back[i][j] = temp_prev

    align_sys = []
    align_gold = []
    
    # backtracking alignment
    i = len(sys_sent)
    j = len(gold_sent)
    while i > 0 and j > 0:
        (prev_i, prev_j) = back[i][j]

        sys = []
        gold = []
        for x in range(prev_i, i):
            sys.append(sys_sent[x])
        for y in range(prev_j, j):
            gold.append(gold_sent[y])

        sys_str = " ".join(sys)
        gold_str = " ".join(gold)

        gold_edits = update_align_edits(gold)
        sys_edits = update_align_edits(sys)

        sys_edits = remove_dummy_edits(sys_edits)
        gold_edits = remove_dummy_edits(gold_edits)

        sys_str = M2_sent(sys_str, sys_edits)
        gold_str = M2_sent(gold_str, gold_edits)

        align_sys.append(sys_str)
        align_gold.append(gold_str)

        i = prev_i
        j = prev_j

    align_sys.reverse()
    align_gold.reverse()

    return align_sys, align_gold

def GC_align(sys_sent, gold_sent):
    sys_align = []
    gold_align = []
    sys_paragraphs, gold_paragraphs = get_paragraphs(sys_sent, gold_sent)
    for sys_para, gold_para in zip(sys_paragraphs, gold_paragraphs):
        if len(sys_para) == 1 and len(gold_para) == 1:
            sys_align.append(sys_para[0])
            gold_align.append(gold_para[0])
            continue

        align_sys, align_gold = paragraph_align(sys_para, gold_para)

        sys_align.extend(align_sys)
        gold_align.extend(align_gold)

    return sys_align, gold_align

def edit_dis_ratio(token_list1, token_list2):
    str1 = "".join(token_list1)
    str2 = "".join(token_list2)
    
    m, n = len(str1), len(str2)

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0:
                dp[i][j] = j
            elif j == 0:
                dp[i][j] = i
            elif str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i][j - 1],
                                   dp[i - 1][j],
                                   dp[i - 1][j - 1])

    dis_ratio = dp[m][n]/len(str2)

    return dis_ratio

def JP_align(sys_sent, gold_sent):
    sys_aligned = []
    gold_aligned = []
    ii = 0
    jj = 0
    
    def check(i, j):
        sys_tokens = sys_sent[i].split()
        gold_tokens = gold_sent[j].split()
        if "".join(sys_tokens) == "".join(gold_tokens):
            return True
        else:
            return False
    
    for i in range(0, len(sys_sent)+1):
        i = ii
        for j in range(i, len(gold_sent)+1):
            j = jj
            
            if check(i, j):
                sys_aligned.append(sys_sent[i])
                gold_aligned.append(gold_sent[j])
                
                ii = i+1
                jj = j+1
                break
            else:
                sys_temp = []
                gold_temp = []
                sys_temp.append(sys_sent[i])
                gold_temp.append(gold_sent[j])

                if len(sys_sent) == i+1 and len(gold_sent) == j+1:
                    sys_aligned.append(sys_sent[i])
                    gold_aligned.append(gold_sent[j])
                    ii = i+1
                    jj = j+1
                    break
                else:
                    # checking if a_i+1 and b_j+1 are same <-- stop condition
                    while not check(i+1, j+1):
                        sys_temp_len = len(" ".join(sys_temp).split())
                        gold_temp_len = len(" ".join(gold_temp).split())
                        if sys_temp_len < gold_temp_len:
                            i += 1
                            sys_temp.append(sys_sent[i])
                        elif sys_temp_len > gold_temp_len:
                            j += 1
                            gold_temp.append(gold_sent[j])
                        else:
                            break

                    sys_temp_str = " ".join(sys_temp)
                    gold_temp_str = " ".join(gold_temp)
                    sys_temp = update_align_edits(sys_temp)
                    gold_temp = update_align_edits(gold_temp)
                    sys_temp = remove_dummy_edits(sys_temp)
                    gold_temp = remove_dummy_edits(gold_temp)
                    sys_temp_M2 = M2_sent(sys_temp_str, sys_temp)
                    gold_temp_M2 = M2_sent(gold_temp_str, gold_temp)

                    sys_aligned.append(sys_temp_M2)
                    gold_aligned.append(gold_temp_M2)

                    ii = i+1
                    jj = j+1
                    break
            
        if ii == len(sys_sent) and jj == len(gold_sent):
            break
    
    return sys_aligned, gold_aligned

def sent_align(sys_sent, gold_sent, algorithm="JP"):
    if algorithm == "JP":
        return JP_align(sys_sent, gold_sent)
    elif algorithm == "GC":
        return GC_align(sys_sent, gold_sent)
    else:
        raise ValueError("Invalid algorithm")

    

def test():
    sys_m2 = open("/home/junrui/RA/errant/Sentence-Boundary/C.dev.bea19.stanza.m2").read().strip().split("\n\n")
    sys_m2_sents = get_m2_sents(sys_m2)
    gold_m2  = open("/home/junrui/RA/prompting-gec/coling2024-results/gold_m2/C.dev.gold.bea19.m2").read().strip().split("\n\n")
    gold_m2_sents = get_m2_sents(gold_m2)
    sys_align, gold_align = sent_align(sys_m2_sents, gold_m2_sents, "GC")
    sys_align_m2 = revert_m2_sents(sys_align)
    gold_align_m2 = revert_m2_sents(gold_align)
    
    consine_sim = []
    cnt = 0
    for sys, gold in zip(sys_align, gold_align):
        vector1 = text_to_vector(sys)
        vector2 = text_to_vector(gold)
        cosine = get_cosine(vector1, vector2)
        consine_sim.append(cosine)
        if cosine > 0.99999 : 
            cnt += 1
        else:
            print(sys)
            print(gold)
            print(cosine)
            print()
    print(cnt, len(sys_align), np.mean(consine_sim))


def main():
    test()


if __name__ == "__main__":
    main()
