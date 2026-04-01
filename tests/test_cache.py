import datetime as dt
import re
import shutil
import types
from pathlib import Path

import pytest

from traficFines.cache import Cache, CacheError

CACHE_DIR = Path.home() / ".my_cache"
APP_NAME = "test_cache"
OBSOLESCENCE = 1
TEST_CASES = [
    pytest.param(
        "trabaluengas",
        "Tres tristes tigres tragan trigo en un trigal",
        id="trabalenguas",
    ),
    pytest.param("refran", "Quién fue a Sevilla perdió su silla", id="refran"),
]


@pytest.fixture
def clean_cache():
    # Nos aseguramos que el directorio de caché está limipio antes y después de cada test
    cache_dir = CACHE_DIR / APP_NAME
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    yield

    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def cache_factory():
    def _make_cache(app_name=APP_NAME, obsolescence=OBSOLESCENCE):
        return Cache(app_name=app_name, obsolescence=obsolescence)

    return _make_cache


def test_cache_properties(clean_cache, cache_factory):
    cache = cache_factory()
    assert repr(cache) == f"Cache(app_name='{APP_NAME}', obsolescence={OBSOLESCENCE})"
    assert str(cache) == f"La caché de '{APP_NAME}' contiene 0 archivos."

    assert cache.app_name == APP_NAME
    assert cache.obsolescence == OBSOLESCENCE
    assert cache.cache_dir == str(CACHE_DIR / APP_NAME)


@pytest.mark.parametrize(
    "name, data",
    TEST_CASES,
)
def test_cache_set_and_load(clean_cache, cache_factory, name, data):
    cache = cache_factory()
    cache.set(name, data)
    assert str(cache) == f"La caché de '{APP_NAME}' contiene 1 archivo."
    assert cache.load(name) == data


@pytest.mark.parametrize(
    "name, data",
    TEST_CASES[:1],
)
def test_cache_exceptions(clean_cache, cache_factory, monkeypatch, name, data):
    cache = cache_factory()
    FILE = "no_existe"
    with pytest.raises(CacheError, match=f"El archivo de caché '{FILE}' no existe."):
        cache.load(FILE)

    with pytest.raises(CacheError, match=f"El archivo de caché '{FILE}' no existe."):
        cache.how_old(FILE)

    with pytest.raises(
        CacheError, match="El tiempo de obsolescencia debe ser al menos 1 día."
    ):
        cache_factory(obsolescence=0)

    cache.set(name, data)
    mtime = dt.datetime.now().timestamp()
    age = dt.timedelta(days=OBSOLESCENCE + 1).total_seconds()
    monkeypatch.setattr(
        Path,
        "stat",
        lambda self, *args, **kwargs: types.SimpleNamespace(st_mtime=mtime),
    )
    monkeypatch.setattr("traficFines.cache.cache.time", lambda: mtime + age)
    with pytest.raises(
        CacheError,
        match=re.escape(
            f"El archivo de caché '{name}' está obsoleto (edad: {dt.timedelta(seconds=age)})."
        ),
    ):
        cache.load(name)


@pytest.mark.parametrize(
    "name, data",
    TEST_CASES[:1],
)
def test_cache_exists(clean_cache, cache_factory, name, data):
    cache = cache_factory()
    assert not cache.exists(name)
    cache.set(name, data)
    assert cache.exists(name)


@pytest.mark.parametrize(
    "name, data",
    TEST_CASES[:1],
)
def test_cache_delete(clean_cache, cache_factory, name, data):
    cache = cache_factory()
    cache.set(name, data)
    assert str(cache) == f"La caché de '{APP_NAME}' contiene 1 archivo."

    cache.delete(name)
    assert str(cache) == f"La caché de '{APP_NAME}' contiene 0 archivos."

    # No lanza un error aunque la caché de la aplicación ya esté vacía
    cache.delete(name)


def test_cache_clear(clean_cache, cache_factory):
    cache = cache_factory()
    cache.set("trabaluengas", "Tres tristes tigres tragan trigo en un trigal")
    cache.set("refran", "Quién fue a Sevilla perdió su silla")
    assert str(cache) == f"La caché de '{APP_NAME}' contiene 2 archivos."

    cache.clear()
    assert str(cache) == f"La caché de '{APP_NAME}' contiene 0 archivos."

    # No lanza un error aunque la caché de la aplicación ya esté vacía
    cache.clear()


@pytest.mark.parametrize(
    "name, data",
    TEST_CASES[:1],
)
def test_cache_using_st_birthtime(clean_cache, cache_factory, monkeypatch, name, data):
    cache = cache_factory()
    birth = dt.datetime.now().timestamp()
    age = 60

    cache.set(name, data)
    monkeypatch.setattr(
        Path,
        "stat",
        lambda self, *args, **kwargs: types.SimpleNamespace(st_birthtime=birth),
    )
    monkeypatch.setattr("traficFines.cache.cache.time", lambda: birth + age)

    assert cache._get_file_age(name) == dt.timedelta(seconds=age)
