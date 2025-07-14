class M2_sent(str):
    def __new__(cls, sent, edits):
        obj = str.__new__(cls, sent)
        obj.edits = edits
        return obj

    def split(self, *args, **kwargs):
        split_result = super().split(*args, **kwargs)
        return [self.__class__(part, self.edits) for part in split_result]

    def strip(self, *args, **kwargs):
        stripped_result = super().strip(*args, **kwargs)
        return self.__class__(stripped_result, self.edits)

    def replace(self, *args, **kwargs):
        replaced_result = super().replace(*args, **kwargs)
        return self.__class__(replaced_result, self.edits)

def get_m2_sents(m2_chunks):
    m2_sents = []
    for chunk in m2_chunks:
        chunk = chunk.strip().split("\n")
        # remove "S "
        sent = chunk[0][2:]
        edits = chunk[1:]
        m2_sents.append(M2_sent(sent, edits))
    return m2_sents


def revert_m2_sents(m2_sents):
    m2_chunks = []
    for sent in m2_sents:
        chunk = "S " + sent + "\n"
        for edit in sent.edits:
            # if type(edit) != M2_sent:
            #     print(edit)
            chunk += edit + "\n"
        chunk = chunk.strip()
        m2_chunks.append(chunk)
    return m2_chunks


def update_edits(edits, offset):
    res = []
    for edit in edits:
        edit = edit[2:].split("|||")
        span = edit[0].split()
        if span[0] != "-1" and span[1] != "-1":
            span[0] = str(int(span[0]) + offset)
            span[1] = str(int(span[1]) + offset)
        
        edit[0] = " ".join(["A "] + span)
        edit = "|||".join(edit)
        res.append(edit)
    return res

def update_align_edits(m2_sents, offset = 0):
    ret_edits = []
    for m2 in m2_sents:
        temp = update_edits(m2.edits, offset)
        ret_edits.extend(temp)
        offset += len(m2.split())

    if len(ret_edits) == 0:
        print(m2_sents[0].edits)
    return ret_edits

def remove_dummy_edits(edits):
    full_dummy_edit = True
    for edit in edits:
        edit = edit[2:].split("|||")
        span = edit[0].split()
        if span[0] != "-1" and span[1] != "-1":
            full_dummy_edit = False
            break

    if full_dummy_edit:
        edits = edits[:1]
    else:
        temp = []
        for edit in edits:
            edit_detail = edit[2:].split("|||")
            span = edit_detail[0].split()
            if span[0] != "-1" and span[1] != "-1":
                temp.append(edit)
        edits = temp

    return edits


# def main():
#     hyp_m2 = open("/home/junrui/RA/prompting-gec/coling2024-results/gold_m2/A.dev.gold.bea19.m2").read().strip().split("\n\n")
#     m2_sents = get_m2_sents(hyp_m2)
#     revert_m2 = revert_m2_sents(m2_sents)
#     for origal, revert in zip(hyp_m2, revert_m2):
#         assert origal == revert
#     print(m2_sents[0].edits == update_edits(m2_sents[0].edits, 0))

# if __name__ == "__main__":
#     main()