from itertools import cycle

dot = cycle(r'. ')
dots = cycle(r'.: ')
pipe = cycle(r'|/-\\')
pipe = cycle(r'|/-\\')
line = cycle([
    '[  ]',
    '[- ]',
    '[ -]',
])


def show(loop=dots):
    print(' ' + next(loop), end='\r')
