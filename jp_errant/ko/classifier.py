# Input: An Edit object
# Output: The same Edit object with an updated error type

def has_same_elements(s, t):
    """Check if two strings have the same characters regardless of order"""
    return sorted(s) == sorted(t)

def get_pos_change_type(o_toks, c_toks):
    """Get a more detailed POS change description with both UPOS and XPOS"""
    o_upos = [tok.upos for tok in o_toks]
    c_upos = [tok.upos for tok in c_toks]
    o_xpos = [tok.xpos if hasattr(tok, 'xpos') else '_' for tok in o_toks]
    c_xpos = [tok.xpos if hasattr(tok, 'xpos') else '_' for tok in c_toks]
    
    # Default formatting for POS tags
    o_pos_full = [f"{u}({x})" for u, x in zip(o_upos, o_xpos)]
    c_pos_full = [f"{u}({x})" for u, x in zip(c_upos, c_xpos)]
    
    # Check for common POS patterns
    if 'NOUN' in o_upos and 'VERB' in c_upos:
        return "R:NOUN->VERB"
    elif 'VERB' in o_upos and 'NOUN' in c_upos:
        return "R:VERB->NOUN"
    elif 'ADJ' in o_upos and 'ADV' in c_upos:
        return "R:ADJ->ADV"
    elif 'ADV' in o_upos and 'ADJ' in c_upos:
        return "R:ADV->ADJ"
    else:
        # Check for particle addition or removal - REMOVE THIS PART
        if len(o_toks) == 1 and len(c_toks) == 1:
            o_xpos_str = o_xpos[0] if o_xpos[0] != '_' else ''
            c_xpos_str = c_xpos[0] if c_xpos[0] != '_' else ''
            
            # First try to detect it as a proper ADP error
            adp_error, adp_type, adp_detail = is_adp_part_error(o_toks, c_toks)
            if adp_error:
                return adp_detail
                
            # Only if that fails, check for other patterns
            # Check if corrected token has added particle
            if '+' in c_xpos_str and ('+' not in o_xpos_str or 
                                     len(c_xpos_str.split('+')) > len(o_xpos_str.split('+'))):
                return "M:ADP"
            
            # Check if original token had particle that was removed
            elif '+' in o_xpos_str and ('+' not in c_xpos_str or 
                                       len(o_xpos_str.split('+')) > len(c_xpos_str.split('+'))):
                return "U:ADP"
                
        # Default to simple UPOS format without XPOS details
        return "R:" + " ".join(o_upos) + " -> " + " ".join(c_upos)

def is_adp_part_error(o_toks, c_toks):
    """Checks if this is a Korean particle error with the updated format"""
    # Skip if no tokens
    if len(o_toks) == 0 or len(c_toks) == 0:
        return False, "", ""
    
    # Check each token pair
    if len(o_toks) == 1 and len(c_toks) == 1:
        o_base, o_particle, o_pos = extract_parts(o_toks[0])
        c_base, c_particle, c_pos = extract_parts(c_toks[0])
        
        # Print extraction results for debugging
        print(f"ADP check: Original={o_toks[0].text} -> base={o_base}, particle={o_particle}")
        print(f"ADP check: Corrected={c_toks[0].text} -> base={c_base}, particle={c_particle}")
        
        # Base comparison - normalized for Korean
        o_base_norm = ''.join(o_base.split()).lower() if o_base else ""
        c_base_norm = ''.join(c_base.split()).lower() if c_base else ""
        
        # Check if base forms are the same
        if o_base_norm == c_base_norm:
            print(f"Base forms match: {o_base_norm} == {c_base_norm}")
            
            # Case 1: Particle removed (Unnecessary)
            if o_particle and not c_particle:
                # Format with updated format: R:POS+ADP -> POS
                error_type = f"R:{o_pos}+ADP -> {c_pos}"
                return True, "U", error_type
                
            # Case 2: Particle added (Missing)
            elif not o_particle and c_particle:
                # Format with updated format: R:POS -> POS+ADP
                error_type = f"R:{o_pos} -> {c_pos}+ADP"
                return True, "M", error_type
                
            # Case 3: Particle changed (Replace)
            elif o_particle and c_particle and o_particle != c_particle:
                print(f"Detected particle change: {o_particle} → {c_particle}")
                # Format with updated format: R:POS+ADP -> POS+ADP
                error_type = f"R:{o_pos}+ADP -> {c_pos}+ADP"
                return True, "R", error_type
        else:
            print(f"Base forms don't match: {o_base_norm} != {c_base_norm}")
    
    return False, "", ""

# Extract base noun and particle information
def extract_parts(tok):
    """
    Extract base word and particle from a token
    Returns: (base_text, particle, pos)
    """
    # Add debug info
    debug_info = f"extract_parts for '{tok.text}': "
    
    if not hasattr(tok, 'xpos') or tok.xpos == '_' or '+' not in tok.xpos:
        print(debug_info + f"No XPOS information, returning whole token as base")
        return tok.text, None, tok.upos if hasattr(tok, 'upos') else "NOUN"
    
    # Split xpos at '+' character
    parts = tok.xpos.split('+')
    
    # Find the split point - first tag starting with 'e' or 'j' (Korean particles)
    split = -1
    for ii, part in enumerate(parts):
        if part.startswith('e') or part.startswith('j'):
            split = ii
            break
    
    # If no split point found, treat the whole token as content
    if split == -1:
        print(debug_info + "No particles detected")
        return tok.text, None, tok.upos
    
    # Get content and functional parts from xpos
    content_xpos = '+'.join(parts[:split])
    functional_xpos = '+'.join(parts[split:])
    
    # Get content and functional parts from lemma or text
    if hasattr(tok, 'lemma') and tok.lemma:
        # If we have lemma information, use it for precise splitting
        lemma_parts = tok.lemma.split('+') if '+' in tok.lemma else [tok.lemma]
        if len(lemma_parts) >= split:
            content_word = ''.join(lemma_parts[:split])
            functional_word = ''.join(lemma_parts[split:])
        else:
            # Fallback to approximation if lemma structure doesn't match xpos
            content_word = tok.text[:-len(functional_xpos)] if functional_xpos else tok.text
            functional_word = tok.text[-len(functional_xpos):] if functional_xpos else None
    else:
        # Approximate splitting based on text length and xpos structure
        content_ratio = len(content_xpos) / (len(content_xpos) + len(functional_xpos))
        split_pos = max(1, round(len(tok.text) * content_ratio))
        content_word = tok.text[:split_pos]
        functional_word = tok.text[split_pos:]
    
    print(debug_info + f"Split at {split}: content={content_word}, particle={functional_word}")
    return content_word, functional_word, tok.upos


def is_word_order_error(o_toks, c_toks):
    """
    Check if this is a word order error (words appear in different sequence)
    """
    if len(o_toks) <= 1 or len(c_toks) <= 1 or len(o_toks) != len(c_toks):
        return False
    
    # Get text from tokens
    o_words = [tok.text for tok in o_toks]
    c_words = [tok.text for tok in c_toks]
    
    # Check if the sets of words are the same but in different order
    return set(o_words) == set(c_words) and o_words != c_words

def is_word_boundary_error(s, t):
    """
    Check if this is a word boundary error in Korean
    Returns:
        tuple: (is_error, error_type)
            is_error: bool - True if this is a word boundary error
            error_type: str - "M:WB" or "U:WB" for missing or unnecessary boundary
    """
    # Join all characters without spaces
    s_joined = ''.join(s.split())
    t_joined = ''.join(t.split())
    
    # If the joined strings are the same but spaces are different, it's a boundary error
    if s_joined == t_joined and s != t:
        # More words in target than source (spaces were missing)
        if len(s.split()) < len(t.split()):
            return True, "M:WB"
        # More words in source than target (unnecessary spaces)
        elif len(s.split()) > len(t.split()):
            return True, "U:WB"
        # Same number of words but different boundaries
        else:
            # Default to M:WB - this is a simplification
            return True, "M:WB"
    
    return False, ""

def is_root_spelling_error(o_tok, c_tok):
    """
    Check if this is a spelling error in the root form of a word
    while maintaining the same grammatical particles/endings
    """
    if not hasattr(o_tok, 'xpos') or not hasattr(c_tok, 'xpos'):
        return False
    
    # Get morphological components if available
    o_parts = o_tok.xpos.split('+') if '+' in o_tok.xpos else [o_tok.xpos]
    c_parts = c_tok.xpos.split('+') if '+' in c_tok.xpos else [c_tok.xpos]
    
    # Check if the number of morphological parts is the same
    if len(o_parts) != len(c_parts):
        return False
    
    # Check if only the root form is different while particles/endings are the same
    if o_parts[0] != c_parts[0] and o_parts[1:] == c_parts[1:]:
        return True
    
    return False

def get_morphological_breakdown(text, xpos):
    """
    Attempt to break down a word into its morphological components
    based on the XPOS tag
    """
    if '+' not in xpos:
        return text
    
    parts = xpos.split('+')
    # This is a simplistic approach - in a real implementation,
    # you'd need morphological analysis to get the exact boundaries
    result = []
    remaining_text = text
    
    for part in parts:
        # For each morphological part, we estimate a portion of the text
        # This is very approximate and would need actual morphological analysis
        part_length = max(1, len(remaining_text) // len(parts))
        result.append(remaining_text[:part_length])
        remaining_text = remaining_text[part_length:]
    
    # Handle any remaining text
    if remaining_text:
        result[-1] += remaining_text
    
    return '+'.join(result)

def is_content_word_correct(o_toks, c_toks):
    """
    Checks if content words (non-particles) are correct between original and corrected text
    Returns True if content words match, False otherwise
    """
    # Add debugging for particle detection
    print("Checking content word correctness:")
    
    # For Korean, we need to extract base forms without particles
    if len(o_toks) == 1 and len(c_toks) == 1:
        # Use the same extract_parts function from is_adp_part_error
        o_base, o_particle, _ = extract_parts(o_toks[0])
        c_base, c_particle, _ = extract_parts(c_toks[0])
        
        # Print what was detected
        print(f"  Original token: {o_toks[0].text} → base={o_base}, particle={o_particle}")
        print(f"  Corrected token: {c_toks[0].text} → base={c_base}, particle={c_particle}")
        
        # Normalize and compare base forms only
        o_base_norm = ''.join(o_base.split()).lower() if o_base else ""
        c_base_norm = ''.join(c_base.split()).lower() if c_base else ""
        
        print(f"  Base comparison: '{o_base_norm}' == '{c_base_norm}'? {o_base_norm == c_base_norm}")
        
        return o_base_norm == c_base_norm
    
    # For multi-token cases, use the existing approach
    # Extract content words (non-ADP/PART)
    def get_content_words(toks):
        return [tok for tok in toks if hasattr(tok, 'upos') and tok.upos not in ['ADP', 'PART']]
    
    o_content = get_content_words(o_toks)
    c_content = get_content_words(c_toks)
    
    # Check if content word counts match
    if len(o_content) != len(c_content):
        return False
    
    # Compare content words
    for o, c in zip(o_content, c_content):
        o_text, _, _ = extract_parts(o) if hasattr(o, 'xpos') and '+' in o.xpos else (o.text, None, None)
        c_text, _, _ = extract_parts(c) if hasattr(c, 'xpos') and '+' in c.xpos else (c.text, None, None)
        
        # Direct comparison of normalized base forms
        o_norm = ''.join(o_text.split()).lower()
        c_norm = ''.join(c_text.split()).lower()
        
        if o_norm != c_norm:
            return False
    
    return True

def classify_all_errors(edit):
    """
    Identifies ALL possible error types for a given edit according to the algorithm:
    1. Check for word boundary errors
    2. Check for word order errors
    3. Check if content word is correct -> particle errors
    4. Check if content word is incorrect -> spelling errors
    
    Returns a list of all applicable error types
    """
    errors = []
    
    # Nothing to nothing is a detected but not corrected edit
    if not edit.o_toks and not edit.c_toks:
        return ["UNK"]
        
    # Create strings for comparison
    o_str = ''.join([tok.text for tok in edit.o_toks])
    c_str = ''.join([tok.text for tok in edit.c_toks])
    
    # Missing token
    if not edit.o_toks and edit.c_toks:
        pos_tags = []
        for tok in edit.c_toks:
            upos = tok.upos if hasattr(tok, 'upos') else '_'
            pos_tags.append(upos)
        
        errors.append("M:" + " ".join(pos_tags))
        return errors
    
    # Unnecessary token
    elif edit.o_toks and not edit.c_toks:
        pos_tags = []
        for tok in edit.o_toks:
            upos = tok.upos if hasattr(tok, 'upos') else '_'
            pos_tags.append(upos)
        
        errors.append("U:" + " ".join(pos_tags))
        return errors
    
    # Replacement and special cases
    elif edit.o_toks and edit.c_toks:
        # Same to same is a detected but not corrected edit
        if edit.o_str == edit.c_str:
            return ["UNK"]
        
        # =====================================================================
        # ALGORITHM PART 1: Check for Word Boundary Error (now first priority)
        # =====================================================================
        is_wb, wb_type = is_word_boundary_error(o_str, c_str)
        if is_wb:
            errors.append(wb_type)
            
        # =====================================================================
        # ALGORITHM PART 2: Check for Word Order Error (now second priority)
        # =====================================================================
        elif is_word_order_error(edit.o_toks, edit.c_toks):
            errors.append("R:WO")  # Word Order
            
        # =====================================================================
        # ALGORITHM PART 3: Check content word correctness and particle errors
        # =====================================================================
        else:
            # Check if content word is correct
            content_word_correct = is_content_word_correct(edit.o_toks, edit.c_toks)

            if content_word_correct:
                # If content word is correct, check for particle errors
                adp_error, adp_type, adp_detail = is_adp_part_error(edit.o_toks, edit.c_toks)
                if adp_error:
                    errors.append(adp_detail)
                    print(f"Detected particle error: {adp_detail} for {edit.o_str} → {edit.c_str}")
            else:
                # If content word is incorrect, it's a spelling error
                errors.append("R:SPELL")
                print(f"Detected spelling error: content words differ in {edit.o_str} → {edit.c_str}")
        
        # If no specific errors found through the algorithm, use POS change
        if not errors:
            errors.append(get_pos_change_type(edit.o_toks, edit.c_toks))
    
    return errors

def generate_m2(source_sent, corrected_sent, edits):
    """
    Generate M2 file contents with multiple annotations per edit when applicable
    
    Args:
        source_sent: Original source sentence
        corrected_sent: Target corrected sentence
        edits: List of Edit objects
    
    Returns:
        List of M2 format lines
    """
    m2_lines = [f"S {source_sent}"]
    
    for edit in edits:
        # Get all possible error types for this edit
        error_types = classify_all_errors(edit)
        
        # Generate one annotation line per error type
        for error_type in error_types:
            # 0-based annotator ID
            annotator_id = 0
            annotation = f"A {edit.start} {edit.end}|||{error_type}|||{edit.c_str}|||REQUIRED|||-NONE-|||{annotator_id}"
            m2_lines.append(annotation)
    
    return m2_lines

def classify(edit):
    """
    The main classification function that returns a combined error type.
    """
    # Get all possible error classifications for this edit
    all_errors = classify_all_errors(edit)
    o_base, c_base = None, None
    o_particle, c_particle = None, None
    if len(edit.o_toks) == 1 and len(edit.c_toks) == 1:
        o_base, o_particle, o_pos = extract_parts(edit.o_toks[0])
        c_base, c_particle, c_pos = extract_parts(edit.c_toks[0])
    o_xpos = [tok.xpos if hasattr(tok, 'xpos') else '_' for tok in edit.o_toks]
    c_xpos = [tok.xpos if hasattr(tok, 'xpos') else '_' for tok in edit.c_toks]
    o_lemma_info = f" [{o_base} + {o_particle}]"
    c_lemma_info = f" [{c_base} + {c_particle}]"
    # Create analysis message with enhanced lemma information
    analysis = "\n=== Error Analysis ===\n"
    analysis += f"Original: '{edit.o_str}' XPOS: '{o_xpos}' Lemma Info: '{o_lemma_info}'\n"
    analysis += f"Corrected: '{edit.c_str}' XPOS: '{c_xpos}' Lemma Info: '{c_lemma_info}'\n"

    
    # Add lemma breakdown for each token
    if edit.o_toks:
        o_lemmas = []
        for tok in edit.o_toks:
            base, particle, _ = extract_parts(tok)
            if particle:
                o_lemmas.append(f"{base}+{particle}")
            else:
                o_lemmas.append(base)
        analysis += f"Original lemmas: {o_lemmas}\n"
    
    if edit.c_toks:
        c_lemmas = []
        for tok in edit.c_toks:
            base, particle, _ = extract_parts(tok)
            if particle:
                c_lemmas.append(f"{base}+{particle}")
            else:
                c_lemmas.append(base)
        analysis += f"Corrected lemmas: {c_lemmas}\n"
    
    analysis += f"Detected error types: {all_errors}\n"
    
    # Combine all error types with + separator
    if all_errors:
        combined_type = " && ".join(all_errors)
        edit.type = combined_type
        analysis += f"Combined error type: {combined_type}\n"
    else:
        edit.type = "UNK"
    
    analysis += "===================\n"
    
    # Append the analysis to a text file
    with open("error_analysis_log.txt", "a", encoding="utf-8") as f:
        f.write(analysis)
    f.close()
    return edit