import math
from .costs import CHAR_COSTS, TOKEN_COSTS, MULTIGRAPH_PLACEHOLDERS
from .char import char_ratio


def _get_avg_sim(
    token1: tuple,
    token2: tuple,
    char_cost_dict: dict = CHAR_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    max_span_len: int = 2,
):
    """
    Computes the average char_ratio across paired elements of two same-length tuples.
    Used to find the closest matching key in a cost dictionary.

    Args:
        token1 (tuple): First token unit.
        token2 (tuple): Second token unit.
        char_cost_dict (dict): Dictionary of custom character-level costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        max_span_len (int): Maximum length of character spans to consider.

    Returns:
        float: Average similarity between paired elements (0.0-100.0),
        or 0.0 if the token units differ in length.
    """
    if len(token1) != len(token2):
        return 0.0
    scores = [
        100.0 if t == c else char_ratio(t, c, char_cost_dict, placeholders, max_span_len)
        for t, c in zip(token1, token2)
    ]
    return sum(scores) / len(scores)


def _get_token_sub_cost(
    token1: tuple,
    token2: tuple,
    char_cost_dict: dict = CHAR_COSTS,
    token_cost_dict: dict = TOKEN_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    sim_threshold: float = 70.0,
    max_span_len: int = 2,
):
    """
    Returns the substitution cost for two token units.

    For pairs of single tokens, the default cost is their character-level similarity. 
    For multi-token spans, the default cost is infinity. A fuzziness penalty is added 
    when token units are similar but not identical to dictionary keys.

    Args:
        token1 (tuple): First token unit.
        token2 (tuple): Second token unit.
        char_cost_dict (dict): Dictionary of custom character-level costs.
        token_cost_dict (dict): Dictionary of custom token-level costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        sim_threshold (float): Minimum similarity (0-100) to soft match a token unit to a key.
        max_span_len (int): Maximum length of character spans to consider.

    Returns:
        float: Substitution cost for the two token units.
    """
    if len(token1) == 1 and len(token2) == 1:
        sim = char_ratio(token1[0], token2[0], char_cost_dict, placeholders, max_span_len)
        default_cost = 1 - sim / 100
    else:
        default_cost = math.inf

    best_key, best_key_sim = max(
        (
            (candidate, get_avg_sim(token1, candidate, char_cost_dict, placeholders, max_span_len))
            for candidate in token_cost_dict["sub"]
            if len(candidate) == len(token1)
        ),
        key=lambda x: x[1],
        default=(None, 0.0),
    )
    if best_key is None or best_key_sim < sim_threshold:
        return default_cost

    candidates = token_cost_dict["sub"].get(best_key, [])
    if not candidates:
        return default_cost

    best_val_key, base_cost = max(
        candidates,
        key=lambda x: (
            get_avg_sim(token2, x[0], char_cost_dict, placeholders, max_span_len)
            if len(token2) == len(x[0]) else 0.0
        ),
    )

    best_val_sim = (
        get_avg_sim(token2, best_val_key, char_cost_dict, placeholders, max_span_len)
        if len(token2) == len(best_val_key) else 0.0
    )

    if best_val_sim < sim_threshold:
        return default_cost

    fuzziness = (100 - best_key_sim) / 100 + (100 - best_val_sim) / 100
    return min(base_cost + fuzziness, default_cost)


def _get_token_ins_cost(
    token: tuple,
    char_cost_dict: dict = CHAR_COSTS,
    token_cost_dict: dict = TOKEN_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    sim_threshold: float = 70.0,
    max_span_len: int = 2,
):
    """
    Returns the insertion cost for a token unit.

    Args:
        token (tuple): The token unit.
        char_cost_dict (dict): Dictionary of custom character-level costs.
        token_cost_dict (dict): Dictionary of custom token-level costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        sim_threshold (float): Minimum similarity (0-100) to soft match a token unit to a key.
        max_span_len (int): Maximum length of character spans to consider.

    Returns:
        float: Insertion cost for the token unit. Defaults to 0.25.
    """
    best_key, best_key_sim = max(
        (
            (candidate, get_avg_sim(token, candidate, char_cost_dict, placeholders, max_span_len))
            for candidate in token_cost_dict["ins"]
            if len(candidate) == len(token)
        ),
        key=lambda x: x[1],
        default=(None, 0.0),
    )
    if best_key is None or best_key_sim < sim_threshold:
        return 0.25
    base_cost = token_cost_dict["ins"][best_key]
    fuzziness = (100 - best_key_sim) / 100
    return min(base_cost + fuzziness, 0.25)


def _get_token_del_cost(
    token: tuple,
    char_cost_dict: dict = CHAR_COSTS,
    token_cost_dict: dict = TOKEN_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    sim_threshold: float = 70.0,
    max_span_len: int = 2,
):
    """
    Returns the deletion cost for a token unit.

    Args:
        token (tuple): The token unit.
        char_cost_dict (dict): Dictionary of custom character-level costs.
        token_cost_dict (dict): Dictionary of custom token-level costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        sim_threshold (float): Minimum similarity (0-100) to soft match a token unit to a key.
        max_span_len (int): Maximum length of character spans to consider.

    Returns:
        float: Deletion cost for the token unit. Defaults to 1.0.
    """
    best_key, best_key_sim = max(
        (
            (candidate, get_avg_sim(token, candidate, char_cost_dict, placeholders, max_span_len))
            for candidate in token_cost_dict["del"]
            if len(candidate) == len(token)
        ),
        key=lambda x: x[1],
        default=(None, 0.0),
    )
    if best_key is None or best_key_sim < sim_threshold:
        return 1.0
    base_cost = token_cost_dict["del"][best_key]
    fuzziness = (100 - best_key_sim) / 100
    return min(base_cost + fuzziness, 1.0)


def token_distance(
    name1: str,
    name2: str,
    char_cost_dict: dict = CHAR_COSTS,
    token_cost_dict: dict = TOKEN_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    sim_threshold: float = 70.0,
    max_char_span_len: int = 2,
    max_token_span_len: int = 3,
):
    """
    Computes a modified token-level Levenshtein distance between two names with
    custom costs.

    Names are lowercased and split on whitespace before comparison. Spans of up
    to max_token_span_len tokens are supported.

    Args:
        name1 (str): First name.
        name2 (str): Second name.
        char_cost_dict (dict): Dictionary of custom character-level costs.
        token_cost_dict (dict): Dictionary of custom token-level costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        sim_threshold (float): Minimum similarity (0-100) to soft match a token unit to a key.
        max_char_span_len (int): Maximum length of character spans to consider.
        max_token_span_len (int): Maximum length of token spans to consider.

    Returns:
        tuple[float, int, int]: A (distance, units1, units2) tuple where distance is
        the modified Levenshtein distance between the two names, and units1 and units2
        are the number of token units consumed from each name along the optimal path.
    """
    tokens1 = tuple(name1.lower().split())
    tokens2 = tuple(name2.lower().split())

    if len(tokens1) < len(tokens2):
        tokens1, tokens2 = tokens2, tokens1

    if not tokens2:
        return float(len(tokens1)), len(tokens1), 0

    len1 = len(tokens1)
    len2 = len(tokens2)
    INF = math.inf

    rows = [[(INF, 0, 0)] * (len2 + 1) for _ in range(max_token_span_len + 1)]
    rows[1][0] = (0.0, 0, 0)
    for j in range(1, len2 + 1):
        prev_cost, prev_u1, prev_u2 = rows[1][j - 1]
        del_cost = _get_token_del_cost(
            (tokens2[j - 1],), char_cost_dict, token_cost_dict,
            placeholders, sim_threshold, max_char_span_len,
        )
        rows[1][j] = (prev_cost + del_cost, prev_u1, prev_u2 + 1)

    for i in range(1, len1 + 1):
        t1 = tokens1[i - 1]
        curr = [(INF, 0, 0)] * (len2 + 1)
        prev_cost, prev_u1, prev_u2 = rows[1][0]
        curr[0] = (
            prev_cost + _get_token_ins_cost(
                (t1,), char_cost_dict, token_cost_dict,
                placeholders, sim_threshold, max_char_span_len,
            ),
            prev_u1 + 1,
            prev_u2,
        )

        for j in range(1, len2 + 1):
            best = (INF, 0, 0)

            # insertion
            for n in range(1, max_token_span_len + 1):
                if n > i:
                    break
                span = tuple(tokens1[i - n:i])
                prev_cost, prev_u1, prev_u2 = rows[n][j]
                ins_cost = _get_token_ins_cost(
                    span, char_cost_dict, token_cost_dict,
                    placeholders, sim_threshold, max_char_span_len,
                )
                cost = (prev_cost + ins_cost, prev_u1 + 1, prev_u2)
                if cost[0] < best[0]:
                    best = cost

            # deletion
            for m in range(1, max_token_span_len + 1):
                if m > j:
                    break
                span = tuple(tokens2[j - m:j])
                prev_cost, prev_u1, prev_u2 = curr[j - m]
                del_cost = _get_token_del_cost(
                    span, char_cost_dict, token_cost_dict,
                    placeholders, sim_threshold, max_char_span_len,
                )
                cost = (prev_cost + del_cost, prev_u1, prev_u2 + 1)
                if cost[0] < best[0]:
                    best = cost

            # substitution
            for n in range(1, max_token_span_len + 1):
                if n > i:
                    break
                span1 = tuple(tokens1[i - n:i])
                for m in range(1, max_token_span_len + 1):
                    if m > j:
                        break
                    span2 = tuple(tokens2[j - m:j])
                    sub_cost = _get_token_sub_cost(
                        span1, span2, char_cost_dict, token_cost_dict,
                        placeholders, sim_threshold, max_char_span_len,
                    )
                    if n == 1 and m == 1:
                        # On the diagonal of equal-length names, suppress partial
                        # credit for tokens that are too dissimilar.
                        if len1 == len2 and i == j and sub_cost >= sim_threshold / 100:
                            sub_cost = 1.0
                    else:
                        if sub_cost == math.inf:
                            continue
                    prev_cost, prev_u1, prev_u2 = rows[n][j - m]
                    cost = (prev_cost + sub_cost, prev_u1 + 1, prev_u2 + 1)
                    if cost[0] < best[0]:
                        best = cost

            curr[j] = best

        rows = [rows[0], curr] + rows[1:-1]

    dist, u1, u2 = rows[1][len2]
    return dist, u1, u2


def token_ratio(
    name1: str,
    name2: str,
    char_cost_dict: dict = CHAR_COSTS,
    token_cost_dict: dict = TOKEN_COSTS,
    placeholders: list[tuple[str, str]] = MULTIGRAPH_PLACEHOLDERS,
    sim_threshold: float = 70.0,
    max_char_span_len: int = 2,
    max_token_span_len: int = 3,
):
    """
    Computes a similarity score between two names based on a modified token-level
    Levenshtein distance with custom costs.

    Args:
        name1 (str): First name.
        name2 (str): Second name.
        char_cost_dict (dict): Dictionary of custom character-level costs.
        token_cost_dict (dict): Dictionary of custom token-level costs.
        placeholders (list[tuple[str, str]]): Multigraph-to-placeholder mappings.
        sim_threshold (float): Minimum similarity (0-100) to soft match a token unit to a key.
            dictionary key. Inputs below this threshold fall back to the default cost.
        max_char_span_len (int): Maximum length of character spans to consider.
        max_token_span_len (int): Maximum length of token spans to consider.

    Returns:
        float: Similarity score between the two names (0.0-100.0).
    """
    distance, u1, u2 = token_distance(
        name1, name2, char_cost_dict, token_cost_dict,
        placeholders, sim_threshold, max_char_span_len, max_token_span_len,
    )
    return (1 - distance / max(u1, u2)) * 100