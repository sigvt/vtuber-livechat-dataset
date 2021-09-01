superchatColors = {
    '4279592384': 'blue',
    '4278237396': 'lightblue',
    '4278239141': 'green',
    '4294947584': 'yellow',
    '4293284096': 'orange',
    '4290910299': 'magenta',
    '4291821568': 'red',
}

superchatSignificance = {
    'blue': 1,
    'lightblue': 2,
    'green': 3,
    'yellow': 4,
    'orange': 5,
    'magenta': 6,
    'red': 7,
}


def convertHeaderBackgroundColorToColorAndSignificance(hbc: str):
    color = superchatColors[hbc]
    sig = superchatSignificance[color]
    return [color, sig]
