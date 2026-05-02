# delFuzz

Fuzzy matching optimized for Spanish names. It uses modified character and token-level Levenshtein Distances to compute a similarity score between two names (0-100). Custom character-level edit costs account for Spanish spelling conventions such as interchangeable letters and the use of diacritics. Custom token-level costs account for name usage conventions such as nicknames and the inclusion of "de".

## Requirements

- Python 3.9 or higher

## Installation
```bash
pip install delfuzz
```

## Usage

### Examples

```python
import delfuzz

# example with diacritic
>>> delfuzz.score("María del Carmen", "Maria del Carmen")
99.33

# example with diacritic and missing "del"
>>> delfuzz.score("María del Carmen", "Maria Carmen")
92.67

# example with nickname
>>> delfuzz.score("María del Carmen", "Maricarmen")
85.0

# example with English variant
>>> delfuzz.score("María del Carmen", "Mary del Carmen")
95.0
```

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| name1 | str |  | First name to be compared. |
| name2 | str |  | Second name to be compared. |
| char_cost_dict | dict | [CHAR_COSTS]([CHAR_COSTS](https://github.com/fbbgarcia/delfuzz/blob/main/src/delfuzz/defaults.py)) | Dictionary of custom character-level costs. |
| token_cost_dict | dict | [TOKEN_COSTS]([CHAR_COSTS](https://github.com/fbbgarcia/delfuzz/blob/main/src/delfuzz/defaults.py)) | Dictionary of custom token-level costs. |
| placeholders | list[tuple[str, str]] | [MULTIGRAPH_PLACEHOLDERS]([CHAR_COSTS](https://github.com/fbbgarcia/delfuzz/blob/main/src/delfuzz/defaults.py)) | List of multigraph-to-placeholder mappings used to treat common Spanish multigraphs as their own singular characters. |
| sim_threshold | float | 70.0 | Minimum similarity (0-100) required to soft match a token/token span to a key in token_cost_dict. Allows algorithm to tolerate minor spelling variations and errors. |
| max_char_span_len | int | 2 | Maximum length of character spans to consider. Allows algorithm to support operations on sequences of characters (e.g. multigraphs). |
| max_token_span_len | int | 3 | Maximum length of token spans to consider. Allows algorithm to support operations on sequences of tokens. |

### Custom Cost Dictionaries

`score` accepts custom cost dictionaries, allowing you to modify or replace the defaults ([CHAR_COSTS]([CHAR_COSTS](https://github.com/fbbgarcia/delfuzz/blob/main/src/delfuzz/defaults.py)) and/or [TOKEN_COSTS]([CHAR_COSTS](https://github.com/fbbgarcia/delfuzz/blob/main/src/delfuzz/defaults.py))).

Cost dictionaries have the following structure:

```python
ex_char_costs = {
    "sub": {
        ("i",): [(("í",), 0.10), (("y",), 0.50)],
        ("p", "h"): [(("f",), 0.50)],
    },
    "ins": {
        ("h",): 0.50
    },
    "del": {
        ("h",): 0.50
    },
}

ex_token_costs = {
    "sub": {
        ("juan",): [(("john",), 0.15)],
        ("mabel",): [(("maría", "isabel"), 0.15), (("mary", "isabelle"), 0.15)]
    },
    "ins": {
        ("de",):  0.20,
    },
    "del": {
        ("de",):  0.20,
    },
}
```

A few notes if you create your own custom cost dictionary:

1. Make sure the dictionary has the keys `"sub"`, `"ins"`, and `"del"` representing each type of edit operation (substitution, insertion, and deletion).

2. Make sure that each character or token is listed as a single element in a tuple. This means that even singular characters or tokens such as `"i"` and `"juan"` are stored as `("i",)` and `("juan",)`. Sequences of characters or tokens such as `"ph"` and `"maría isabel"` are stored as `("p", "h")` and `("maría", "isabel")`. This structure enables the lookup process that supports operations on sequences of characters and tokens.

3. Substitution costs only need to be defined in one direction. You can use `add_inverse_subs` to automatically add the reverse mappings:

```python
import delfuzz

ex_char_costs = delfuzz.add_inverse_subs(ex_char_costs)
ex_token_costs = delfuzz.add_inverse_subs(ex_token_costs)

delfuzz.score("Juan", "John", char_cost_dict = ex_char_costs, token_cost_dict = ex_token_costs)
```

4. If you add costs for operations on sequences longer than the default span length, make sure to pass the appropriate `max_char_span_len` or `max_token_span_len` argument to match the longest sequence in your cost dictionary. The defaults are 2 for character spans and 3 for token spans — any costs defined on longer sequences will not be found during lookup otherwise.

## Benchmark

General-purpose fuzzy or string matching libraries like RapidFuzz treat names as plain strings. Without context of Spanish spelling or name usage conventions, they tend to underestimate the similarity between Spanish names.

For example, here's how our scores compare to RapidFuzz's ratio scores:

| Name 1 | Name 2 | delFuzz | RapidFuzz Ratio |
| --- | --- | --- | --- |
| María del Carmen | Maria del Carmen | 99.33 | 93.75 |
| María del Carmen | Maria Carmen | 92.67 | 78.57 |
| María del Carmen | Maricarmen | 85.00 | 61.54 |
| María del Carmen | Mary del Carmen | 95.00 | 90.32 |

RapidFuzz scores computed using `rapidfuzz.fuzz.ratio`.


## Acknowledgements

This algorithm was developed as part of a Data Science capstone project at California Polytechnic State University, San Luis Obispo, in contribution to the [African Californios](https://www.africancalifornios.org/) research project.

The capstone project was conducted in collaboration with African Californios project directors Dr. Cameron D. Jones, Lecturer in History, and Dr. Foaad Khosmood, Professor of Computer Science. Additional collaboration was provided by Jack T. Martin, a Visiting Scholar in History. It was advised by Dr. Alex Dekhtyar, Professor of Computer Science, and Dr. Kelly N. Bodwin, Professor of Statistics.


## License

MIT License. See [LICENSE](LICENSE) for details.