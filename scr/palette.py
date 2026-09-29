"""Single source of truth for chart colors, shared by every matplotlib chart
and the generated HTML report so the whole project reads as one system.

Swap the hex values here to re-brand every chart and page at once. If you do,
re-validate the categorical order with the `dataviz` skill's
`scripts/validate_palette.js` before relying on it for colorblind-safety.
"""

# Fixed-order categorical hues (identity: use in this order, never cycled).
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

# Named roles used directly in code for clarity.
BLUE = CATEGORICAL[0]
ORANGE = CATEGORICAL[1]
AQUA = CATEGORICAL[2]
YELLOW = CATEGORICAL[3]
MAGENTA = CATEGORICAL[4]
GREEN = CATEGORICAL[5]
VIOLET = CATEGORICAL[6]
RED = CATEGORICAL[7]

# Diverging pair for polarity (positive/negative, real-vs-reference).
DIVERGING_POS = BLUE
DIVERGING_NEG = RED

# Chart/page chrome (light mode only - these are static report artifacts).
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"
