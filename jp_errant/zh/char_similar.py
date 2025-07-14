import numpy as np
import pandas as pd
from difflib import SequenceMatcher
import os
_cached_df = None

def load_similarity_table(path=None):
    """Load pre-calculated similarity scores from CSV file."""
    global _cached_df
    if _cached_df is not None:
        return _cached_df
    
    if path is None:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, 'triplet_no_dup_threshold.csv')
    
    df = pd.read_csv(path)
    _cached_df = df
    return df

def compare_characters(char1, char2):
    """Compare character similarity using pre-calculated table."""
    # Define number mapping
    num_map = {
        '1': '一', '一': '1',
        '2': '二', '二': '2',
        '3': '三', '三': '3',
        '4': '四', '四': '4',
        '5': '五', '五': '5',
        '6': '六', '六': '6',
        '7': '七', '七': '7',
        '8': '八', '八': '8',
        '9': '九', '九': '9',
        '10': '十', '十': '10',
        '100': '百', '百': '100',
        '1000': '千', '千': '1000',
        '10000': '万', '万': '10000'
    }
    
    # Check if the characters are equivalent numbers
    if char1 in num_map and num_map[char1] == char2:
        return 1.0
    if char2 in num_map and num_map[char2] == char1:
        return 1.0
        
    if char1 == char2:
        return 1.0
        
    df = load_similarity_table()
    row = df[((df['CharA'] == char1) & (df['CharB'] == char2)) | 
             ((df['CharA'] == char2) & (df['CharB'] == char1))]
    
    if len(row) > 0:
        return row.iloc[0]['similarity']
    return 0.0

def get_differing_chars(str1, str2):
    """Get pairs of differing characters between two strings."""
    # Use SequenceMatcher to find matching and differing sequences
    matcher = SequenceMatcher(None, str1, str2)
    diff_pairs = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            # Add pairs of different characters
            for k in range(min(i2-i1, j2-j1)):
                diff_pairs.append((str1[i1+k], str2[j1+k]))
        elif tag == 'delete':
            # Characters in str1 that don't exist in str2
            for k in range(i1, i2):
                diff_pairs.append((str1[k], ''))
        elif tag == 'insert':
            # Characters in str2 that don't exist in str1
            for k in range(j1, j2):
                diff_pairs.append(('', str2[k]))
    
    return diff_pairs

def char_similarity_score(str1, str2):
    """Calculate similarity score based on pre-calculated character similarities, completely ignoring order."""
    if str1 == str2:
        return {
            'average_score': 1.0,
            'total_score': len(str1),
            'detailed_comparison': [(c, c, 1.0) for c in str1]
        }

    # Convert strings to character lists and sort
    chars1 = sorted(str1)
    chars2 = sorted(str2)
    
    # Find matching characters first (ignoring position)
    matched_chars = set(chars1) & set(chars2)
    unmatched1 = [c for c in chars1 if c not in matched_chars]
    unmatched2 = [c for c in chars2 if c not in matched_chars]
    
    # Calculate total score for matched characters
    total_score = len(matched_chars)  # Each match contributes 1.0
    comparison_results = {}
    
    # For unmatched characters, find highest similarity scores
    if unmatched1 and unmatched2:
        # For each unmatched char in str1, find its highest similarity with any unmatched char in str2
        for char1 in unmatched1:
            max_score = 0
            best_match = unmatched2[0]
            for char2 in unmatched2:
                score = compare_characters(char1, char2)
                if score > max_score:
                    max_score = score
                    best_match = char2
            total_score += max_score
            comparison_results[(char1, best_match)] = max_score

    # Create final comparison results in original string order
    final_comparisons = []
    processed_chars2 = set()  # Track which chars from str2 have been used
    
    for c1 in str1:
        if c1 in matched_chars:
            # Find the first unused matching char in str2
            for c2 in str2:
                if c2 == c1 and c2 not in processed_chars2:
                    final_comparisons.append((c1, c2, 1.0))
                    processed_chars2.add(c2)
                    break
        else:
            # Find the best match from comparison_results
            best_match = None
            best_score = 0
            for (char1, char2), score in comparison_results.items():
                if char1 == c1 and char2 not in processed_chars2 and score > best_score:
                    best_match = char2
                    best_score = score
            if best_match:
                final_comparisons.append((c1, best_match, best_score))
                processed_chars2.add(best_match)
            else:
                final_comparisons.append((c1, '', 0.0))

    # Add any remaining chars from str2 that weren't matched
    for c2 in str2:
        if c2 not in processed_chars2:
            final_comparisons.append(('', c2, 0.0))

    # For different length strings, use max score among different characters
    if len(str1) != len(str2):
        max_diff_score = 0
        for _, _, score in final_comparisons:
            if score < 1.0:  # Not an exact match
                max_diff_score = max(max_diff_score, score)
        average_score = max_diff_score
    else:
        average_score = total_score / len(str1)

    return {
        'average_score': average_score,
        'total_score': total_score,
        'detailed_comparison': final_comparisons
    }

def final_similarity_score(str1, str2):
    """Get the final similarity score between two strings using pre-calculated character similarities."""
    result = char_similarity_score(str1, str2)
    return result['average_score']

if __name__ == '__main__':
    # Test cases including order and length variations
    test_cases = [
        ("欧洲", "欧州"),    # Same order, different character
        ("电脑", "申脑"),    # Same order, different character
        ("简体", "体简"),    # Different order, same characters
        ("文盲", "丈育"),    # Different characters
        ("大晴天", "晴"),    # Different length, with matching character
        ("学习机", "学习"),  # Different length, with common prefix
        ("体育棵", "体育课")   # Different length, with common base
    ]
    
    for str1, str2 in test_cases:
        result = char_similarity_score(str1, str2)
        print(f"\nComparing: {str1} vs {str2}")
        print(f"Average Score: {result['average_score']:.3f}")
        print("Character by character comparison:")
        for char1, char2, score in result['detailed_comparison']:
            print(f"  '{char1}' vs '{char2}': {score:.3f}")
