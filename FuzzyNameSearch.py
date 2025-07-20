# Route Finder Mobile
# FuzzyNameSearch.py
# 29 January 2025 20:20

# Finds the best match of a text string in a list of names

# A points scoring system is used that scores +length^2 for each matched fragment of text,
#     starting with the longest possible matching fragment
# A match includes imperfect matches (similar letters or likely typos) but these are penalized -1 points
# Unmatched letters are penalized -5 points
# The highest scoring match is chosen
# A string fragment fails to match if its score is less than -length
# The total score for all fragments of the input text is added up for each target string and the best score is chosen

# def find_best_match(input_string, target_names)
# input_string: str
#      text string to be matched
# target_names: list of str
#      text strings to match against
# returns int | None
#      the index of the best match in the target list or None if no target string meets minimal matching conditions

# noinspection SpellCheckingInspection
allowed_letters = "0123456789abcdefghijklmnopqrstuvwxyz "
# noinspection SpellCheckingInspection
partial_allowed = {
    '0': '1o',
    '1': '02li',
    '2': '13',
    '3': '24',
    '4': '35',
    '5': '46',
    '6': '57',
    '7': '68',
    '8': '79',
    '9': '80',
    'a': 'sqiueo',
    'b': 'vn',
    'c': 'sxvdf',
    'd': 'sftercx',
    'e': 'aiouwr',
    'f': 'vdgr',
    'g': 'jfhb',
    'h': 'gje',
    'i': 'aeouyj',
    'j': 'hkig',
    'k': 'cjl',
    'l': 'i1k;',
    'm': 'n,',
    'n': 'mb',
    'o': 'aeiup0',
    'p': 'bolq',
    'q': 'w1pa',
    'r': 'etn',
    's': 'adzcx',
    't': 'dryg',
    'u': 'aeioyjvw',
    'v': 'fucbw',
    'w': 'uvq',
    'x': 'scz',
    'y': 'uitv',
    'z': 'sxc',
    ' ': "c"
}


def simplify_name(input_string):
    return ''.join([ch.lower() for ch in input_string if ch.lower() in allowed_letters])


def fuzzy_compare(target, match_string):
    score = 0
    current_length = 0
    for match_ch, target_ch in zip(match_string, target):
        if match_ch == target_ch:
            current_length += 1
        elif match_ch in partial_allowed[target_ch]:
            current_length += 1
            score -= 2
        else:
            score += current_length ** 2
            score -= 5
            current_length = 0
    score += current_length ** 2
    return score


def match(input_text, target):
    remaining_target = simplify_name(target)
    match_string = simplify_name(input_text)
    unmatched_string = ""
    total_score = 0
    if len(remaining_target) > 0 and len(match_string) > 0:
        if remaining_target[0] == match_string[0]:
           total_score += 3
        if remaining_target[-1] in partial_allowed[match_string[0]]:
            total_score += 1
    while len(match_string) > 0:
        best_index, best_score = None, 0
        target_score = len(match_string) * (len(match_string) - 1)
        for i in range(len(remaining_target) - len(match_string) + 1):
            match_score = fuzzy_compare(remaining_target[i:i+len(match_string)], match_string)
            if match_score >= target_score and match_score > best_score:
                best_index, best_score = i, match_score
        if best_index is not None:
            total_score += best_score
            remaining_target = remaining_target[:best_index] + remaining_target[best_index + len(match_string):]
            match_string = unmatched_string
            unmatched_string = ""
        elif len(match_string) == 1:
            total_score -= 5
            match_string = unmatched_string
            unmatched_string = ""
        else:
            match_string, unmatched_string = match_string[:-1], match_string[-1] + unmatched_string
    return total_score


def find_best_match(input_string, target_names, n=1):
    matches = [(target_name, match(input_string, target_name), i) for i, target_name in enumerate(target_names)]
    matches.sort(key=lambda x: x[1], reverse=True)
    best_match, best_score, best_index = matches[0]
    if best_score < -len(input_string):
        return []
    elif n == 1:
        return best_match
    else:
        return [x[0] for x in matches[:n] if x[1] >= len(input_string) * 2]
