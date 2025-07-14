from pypinyin import pinyin, Style
import difflib
from .char_similar import final_similarity_score

def sim_pinyin(s, t):
    s_pinyin = pinyin(s, style=Style.NORMAL)
    t_pinyin = pinyin(t, style=Style.NORMAL)
    s_pinyin_str = ''.join([item[0] for item in s_pinyin])
    t_pinyin_str = ''.join([item[0] for item in t_pinyin])
    return difflib.SequenceMatcher(None, s_pinyin_str, t_pinyin_str).ratio()

def sim_shape(s, t):
    return final_similarity_score(s, t)

def is_de_error(s, t):
    """Check if this is a '的/地/得' (DE) error"""
    de_chars = ['的', '地', '得']
    # Only consider DE error if both strings are single characters and both are in the DE set
    return len(s) == 1 and len(t) == 1 and s in de_chars and t in de_chars

def get_pos_change_type(o_toks, c_toks):
    """Get a more detailed POS change description"""
    o_pos = [tok.upos for tok in o_toks]
    c_pos = [tok.upos for tok in c_toks]
    
    # Check for common POS patterns
    if 'NOUN' in o_pos and 'VERB' in c_pos:
        return "R:NOUN->VERB"
    elif 'VERB' in o_pos and 'NOUN' in c_pos:
        return "R:VERB->NOUN"
    elif 'ADJ' in o_pos and 'ADV' in c_pos:
        return "R:ADJ->ADV"
    elif 'ADV' in o_pos and 'ADJ' in c_pos:
        return "R:ADV->ADJ"
    else:
        # Default to the original format
        return "R:" + " ".join(o_pos) + " -> " + " ".join(c_pos)

def classify(edit):
    s = ''.join([tok.text for tok in edit.o_toks])
    t = ''.join([tok.text for tok in edit.c_toks])

    alpha1 = 0.8  # Threshold for pinyin similarity
    alpha2 = 0.86  # Threshold for shape similarity

    print("\n=== Error Analysis ===")
    
    # R: Replacement
    if edit.o_toks and edit.c_toks:
        print(f"Comparing tokens: '{s}' -> '{t}'")
        
        # Check for punctuation differences first
        punct_pairs = [
            ('，', ','), (',', '，'),
            ('。', '.'), ('.', '。'),
            ('；', ';'), (';', '；'),
            ('：', ':'), (':', '：'),
            ('！', '!'), ('!', '！'),
            ('？', '?'), ('?', '？')
        ]
        if len(s) == 1 and len(t) == 1:
            for pair in punct_pairs:
                if (s, t) == pair or (t, s) == pair:
                    edit.type = "R:SPELL:PUNCT"
                    print(f"Error Type: {edit.type}")
                    print("===================")
                    return edit
        
        # Check for DE errors early (after punctuation)
        if is_de_error(s, t):
            edit.type = "R:DE"
            print(f"Error Type: {edit.type}")
            print("===================")
            return edit

        # Calculate similarities independently
        shape_sim = sim_shape(s, t)
        pinyin_sim = sim_pinyin(s, t)  # Always calculate pinyin similarity independently
        print(f"Shape Similarity: {shape_sim:.3f}")
        print(f"Pinyin Similarity: {pinyin_sim:.3f}")
        
        # Handle different length cases
        if len(s) != len(t):
            # Check if it's just a character order issue
            if set(s) == set(t):
                if len(s) == 1 or len(t) == 1:
                    edit.type = "R:CO"  # Character Order
                else:
                    edit.type = "R:WO"  # Word Order
            else:
                # More detailed POS analysis for different length replacements
                edit.type = get_pos_change_type(edit.o_toks, edit.c_toks)
            print(f"Error Type: {edit.type} (Different lengths: {len(s)} vs {len(t)})")
            print("===================")
            return edit

        # For same length cases, classify based on similarities
        if pinyin_sim > alpha1 and shape_sim > alpha2:
            edit.type = "R:MULTI"
        elif pinyin_sim > alpha1:
            edit.type = "R:PINYIN"
        elif shape_sim > alpha2:
            edit.type = "R:SHAPE"
        elif set(s) == set(t):
            if len(t) == 1:
                edit.type = "R:CO"  # Character Order
            else:
                edit.type = "R:WO"  # Word Order
        else:
            edit.type = get_pos_change_type(edit.o_toks, edit.c_toks)
        
        print(f"Error Type: {edit.type}")
        print("===================")

    # M: Missing
    elif not edit.o_toks and edit.c_toks:
        print(f"Missing Token: '{t}'")
        if t in ['的', '地', '得'] and len(t) == 1:
            edit.type = "M:DE"
        else:
            edit.type = "M:" + " ".join([tok.upos for tok in edit.c_toks])
        print(f"Error Type: {edit.type}")
        print("===================")

    # U: Unnecessary
    elif edit.o_toks and not edit.c_toks:
        print(f"Unnecessary Token: '{s}'")
        if s in ['的', '地', '得'] and len(s) == 1:
            edit.type = "U:DE"
        else:
            edit.type = "U:" + " ".join([tok.upos for tok in edit.o_toks])
        print(f"Error Type: {edit.type}")
        print("===================")

    # UNK: Unknown or No Change
    else:
        print("Unknown Error Type")
        edit.type = "UNK"
        print("===================")

    return edit
