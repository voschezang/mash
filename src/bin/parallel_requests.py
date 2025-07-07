
if __name__ == '__main__':
    import _extend_path  # noqa

import time
from mash.webtools.pipeline import PushPull, Strategy
from mash.webtools.parallel_requests import compute


if __name__ == '__main__':
    # test_compute_pipeline()

    # run_compute_pipeline()

    PushPull.n_processors = 2
    for s in Strategy:
        t1 = time.perf_counter()
        compute(100, s)
        t2 = time.perf_counter()

        print(f'{s:<20} {t2 - t1:.2f} s')
