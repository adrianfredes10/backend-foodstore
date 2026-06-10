# tests del token bucket del rate limiter (logica pura, sin red)
from app.core.rate_limit import TokenBucket


def test_bucket_permite_hasta_capacidad():
    # capacidad 3, refill lento (no se rellena durante el test)
    bucket = TokenBucket(capacity=3, refill_rate=0.0001)
    assert bucket.try_consume()
    assert bucket.try_consume()
    assert bucket.try_consume()
    # al cuarto intento ya no hay tokens
    assert not bucket.try_consume()


def test_bucket_se_rellena_con_el_tiempo():
    # refill alto: 1000 tokens/seg -> tras consumir, se repone enseguida
    bucket = TokenBucket(capacity=1, refill_rate=1000)
    assert bucket.try_consume()
    assert not bucket.try_consume()
    import time

    time.sleep(0.01)
    assert bucket.try_consume()
