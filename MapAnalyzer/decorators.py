import contextlib
import functools
import sys
import threading
from functools import partial
from typing import Any, Callable, Dict, Optional, Tuple

# import tqdm
from loguru import logger
from tqdm import tqdm as std_tqdm
from tqdm.contrib import DummyTqdmFile

tqdm = partial(std_tqdm, dynamic_ncols=True)


def logger_wraps(*, entry=True, exit=True, level="INFO"):
    def wrapper(func):
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger_ = logger.opt(depth=1)
            if entry:
                logger_.log(
                    level, "Entering '{}' (args={}, kwargs={})", name, args, kwargs
                )
            result = func(*args, **kwargs)
            if exit:
                logger_.log(level, "Exiting '{}' (result={})", name, result)
            return result

        return wrapped

    return wrapper


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


def provide_progress_bar(
    function: Callable,
    estimated_time: int,
    tstep: float = 0.2,
    tqdm_kwargs: Optional[Dict[str, str]] = None,
    args: Optional[Tuple["MapData"]] = None,
    kwargs: Optional[Dict[Any, Any]] = None,
) -> None:
    """Tqdm wrapper for a long-running function
    args:
        function - function to run
        estimated_time - how long you expect the function to take
        tstep - time delta (seconds) for progress bar updates
        tqdm_kwargs - kwargs to construct the progress bar
        args - args to pass to the function
        kwargs - keyword args to pass to the function
    ret:
        function(*args, **kwargs)
    """
    if tqdm_kwargs is None:
        tqdm_kwargs = {}
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    ret = [None]  # Mutable var so the function can store its return value

    # with std_out_err_redirect_tqdm() as orig_stdout:

    def myrunner(func, ret_val, *r_args, **r_kwargs):
        ret_val[0] = func(*r_args, **r_kwargs)

    thread = threading.Thread(
        target=myrunner, args=(function, ret) + tuple(args), kwargs=kwargs
    )
    pbar = tqdm(total=estimated_time, **tqdm_kwargs)
    thread.start()
    while thread.is_alive():
        thread.join(timeout=tstep)
        pbar.update(tstep)
    pbar.close()
    return ret[0]


def progress_wrapped(
    estimated_time: int,
    desc: str = "Progress",
    tstep: float = 0.2,
    tqdm_kwargs: None = None,
) -> Callable:
    """Decorate a function to add a progress bar"""

    if tqdm_kwargs is None:
        # tqdm_kwargs = {"bar_format": '{desc}: {percentage:3.0f}%|{bar}| {n:.1f}/{total:.1f} [{elapsed}<{remaining}]'}
        tqdm_kwargs = {}

    def real_decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            tqdm_kwargs["desc"] = desc
            return provide_progress_bar(
                function,
                estimated_time=estimated_time,
                tstep=tstep,
                tqdm_kwargs=tqdm_kwargs,
                args=args,
                kwargs=kwargs,
            )

        return wrapper

    return real_decorator
