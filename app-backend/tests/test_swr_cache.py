import threading

from app.services.swr_cache import SWRCache


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_computes_once_then_serves_fresh_value():
    clock, calls = Clock(), []
    c = SWRCache(clock=clock, background=lambda f: f())
    assert c.get("k", 10, lambda: calls.append(1) or "v1") == "v1"
    clock.t = 5
    assert c.get("k", 10, lambda: calls.append(1) or "v2") == "v1"
    assert len(calls) == 1


def test_stale_value_is_served_while_refreshing_in_background():
    clock, jobs = Clock(), []
    c = SWRCache(clock=clock, background=jobs.append)  # refresh runs when we decide
    c.get("k", 10, lambda: "v1")
    clock.t = 11
    assert c.get("k", 10, lambda: "v2") == "v1"      # stale served immediately
    assert c.get("k", 10, lambda: "v3") == "v1"      # one refresh in flight only
    assert len(jobs) == 1
    jobs[0]()
    assert c.get("k", 10, lambda: "v4") == "v2"


def test_failed_refresh_keeps_the_stale_value_and_allows_a_retry():
    clock, jobs = Clock(), []
    c = SWRCache(clock=clock, background=jobs.append)
    c.get("k", 10, lambda: "v1")
    clock.t = 11

    def boom():
        raise RuntimeError("db down")

    assert c.get("k", 10, boom) == "v1"
    jobs[0]()                                          # refresh fails, logged, stale kept
    assert c.get("k", 10, lambda: "v2") == "v1"
    assert len(jobs) == 2                              # a new refresh was scheduled


def test_concurrent_cold_callers_share_one_computation():
    c = SWRCache()
    started, release, calls = threading.Event(), threading.Event(), []

    def slow():
        calls.append(1)
        started.set()
        release.wait(2)
        return "v"

    out = []
    t1 = threading.Thread(target=lambda: out.append(c.get("k", 10, slow)))
    t1.start()
    started.wait(2)
    t2 = threading.Thread(target=lambda: out.append(c.get("k", 10, slow)))
    t2.start()
    release.set()
    t1.join(2)
    t2.join(2)
    assert out == ["v", "v"] and len(calls) == 1
