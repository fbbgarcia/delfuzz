import math
from .costs import CHAR_COSTS, MULTIGRAPH_PLACEHOLDERS


def _get_char_sub_cost(
    char1: tuple,
    char2: tuple,
    cost_dict: dict = CHAR_COSTS,
):
    """
    Returns the substitution cost for two character units.
    Defaults to 1.0 if no custom cost is defined.
    """
    candidates = cost_dict["sub"].get(char1)
    if candidates is None:
        return 1.0
    for candidate, cost in candidates:
        if candidate == char2:
            return cost
    return 1.0


def _get_char_ins_cost(
    char: tuple,
    cost_dict: dict = CHAR_COSTS,
):
    """
    Returns the insertion cost for a character unit.
    Defaults to 1.0 per character if no custom cost is defined.
    """
    if len(char) == 1:
        return cost_dict["ins"].get(char, 1.0)
    return sum(_get_char_ins_cost((c,), cost_dict) for c in char)


def _get_char_del_cost(
    char: tuple,
    cost_dict: dict = CHAR_COSTS,
):
    """
    Returns the deletion cost for a character unit.
    Defaults to 1.0 per character if no custom cost is defined.
    """
    if len(char) == 1:
        return cost_dict["del"].get(char, 1.0)
    return sum(_get_char_del_cost((c,), cost_dict) for c in char)


def char_distance(
    token1: str,
    token2: str,
    cost_dict: dict = CHAR_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    max_span_len: int = 2,
):
    """
    Computes a modified character-level Levenshtein distance between two tokens with 
    custom costs.

    Multigraphs are collapsed to placeholder characters to be treated as 
    single character units. Spans of up to max_span_len characters are supported.

    Args:
        token1 (str): First token.
        token2 (str): Second token.
        cost_dict (dict): Dictionary of custom costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        max_span_len (int): Maximum length ofcharacter spans to consider.

    Returns:
        tuple[float, int, int]: A (distance, units1, units2) tuple where distance is
        the modified Levenshtein distance between the two tokens, and units1 and units2 
        are the number of character units consumed from each token along the optimal path.
    """

    for digraph, placeholder in placeholders:
        token1 = token1.replace(digraph, placeholder)
        token2 = token2.replace(digraph, placeholder)

    if len(token1) < len(token2):
        token1, token2 = token2, token1

    if not token2:
        return float(len(token1)), len(token1), 0

    len1 = len(token1)
    len2 = len(token2)
    INF = math.inf

    rows = [[(INF, 0, 0)] * (len2 + 1) for _ in range(max_span_len + 1)]
    rows[1][0] = (0.0, 0, 0)
    for j in range(1, len2 + 1):
        prev_cost, prev_u1, prev_u2 = rows[1][j - 1]
        del_cost = _get_char_del_cost((token2[j - 1],), cost_dict)
        rows[1][j] = (prev_cost + del_cost, prev_u1, prev_u2 + 1)

    for i in range(1, len1 + 1):
        curr = [(INF, 0, 0)] * (len2 + 1)
        prev_cost, prev_u1, prev_u2 = rows[1][0]
        ins_cost = _get_char_ins_cost((token1[i - 1],), cost_dict)
        curr[0] = (prev_cost + ins_cost, prev_u1 + 1, prev_u2)

        for j in range(1, len2 + 1):
            best = (INF, 0, 0)

            # insertion
            for n in range(1, max_span_len + 1):
                if n > i:
                    break
                span = tuple(token1[i - n:i])
                prev_cost, prev_u1, prev_u2 = rows[n][j]
                cost = (prev_cost + _get_char_ins_cost(span, cost_dict), prev_u1 + 1, prev_u2)
                if cost[0] < best[0]:
                    best = cost

            # deletion
            for m in range(1, max_span_len + 1):
                if m > j:
                    break
                span = tuple(token2[j - m:j])
                prev_cost, prev_u1, prev_u2 = curr[j - m]
                cost = (prev_cost + _get_char_del_cost(span, cost_dict), prev_u1, prev_u2 + 1)
                if cost[0] < best[0]:
                    best = cost

            # substitution
            for n in range(1, max_span_len + 1):
                if n > i:
                    break
                span1 = tuple(token1[i - n:i])
                for m in range(1, max_span_len + 1):
                    if m > j:
                        break
                    span2 = tuple(token2[j - m:j])
                    if n == 1 and m == 1:
                        sub_cost = 0.0 if span1[0] == span2[0] else _get_char_sub_cost(span1, span2, cost_dict)
                    else:
                        sub_cost = _get_char_sub_cost(span1, span2, cost_dict)
                        if sub_cost == 1.0:
                            continue
                    prev_cost, prev_u1, prev_u2 = rows[n][j - m]
                    cost = (prev_cost + sub_cost, prev_u1 + 1, prev_u2 + 1)
                    if cost[0] < best[0]:
                        best = cost

            curr[j] = best

        rows = [rows[0], curr] + rows[1:-1]

    return rows[1][len2]


def char_ratio(
    token1: str,
    token2: str,
    cost_dict: dict = CHAR_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    max_span_len: int = 2,
):
    """
    Computes a similarity score between two tokens based on a 
    modified character-level Levenshtein distance with custom costs.

    Args:
        token1 (str): First token.
        token2 (str): Second token.
        cost_dict (dict): Dictionary of custom costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        max_span_len (int): Maximum length ofcharacter spans to consider.

    Returns:
        float: Similarity score between the two tokens (0.0-100.0).
    """
    distance, u1, u2 = char_distance(token1, 
                                     token2, 
                                     cost_dict, 
                                     placeholders, 
                                     max_span_len)
    return (1 - distance / max(u1, u2)) * 100