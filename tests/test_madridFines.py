import shutil
from pathlib import Path

import pytest
import responses

# Ver: https://github.com/omarkohl/pytest-datafiles/blob/main/examples/example_3.py
TEST_DIR = Path(__file__).parent.resolve() / "test_files"


APP_NAME = "test_madrid_fines"
OBSOLESCENCE = 1
TEST_CASES = [
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle.rdf",
        Path(TEST_DIR / "metadata.rdf"),
        id="metadata.rdf",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv",
        Path(TEST_DIR / "multas_diciembre_2024.csv"),
        id="multas-diciembre-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-16-multas-circulacion-detalle-csv/download/210104-16-multas-circulacion-detalle-csv",
        Path(TEST_DIR / "multas_noviembre_2024.csv"),
        id="multas-noviembre-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-18-multas-circulacion-detalle-csv/download/210104-18-multas-circulacion-detalle-csv",
        Path(TEST_DIR / "multas_octubre_2024.csv"),
        id="multas-octubre-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-344-multas-circulacion-detalle-csv/download/210104-344-multas-circulacion-detalle-csv",
        Path(TEST_DIR / "multas_septiembre_2024.csv"),
        id="multas-septiembre-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-343-multas-circulacion-detalle-csv/download/210104-343-multas-circulacion-detalle-csv",
        Path(TEST_DIR / "multas_agosto_2024.csv"),
        id="multas-agosto-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-21-multas-circulacion-detalle-csv/download/210104-21-multas-circulacion-detalle-csv.csv",
        Path(TEST_DIR / "multas_julio_2024.csv"),
        id="multas-julio-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-341-multas-circulacion-detalle-csv/download/210104-341-multas-circulacion-detalle-csv.csv",
        Path(TEST_DIR / "multas_junio_2024.csv"),
        id="multas-junio-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-339-multas-circulacion-detalle-csv/download/210104-339-multas-circulacion-detalle-csv.csv",
        Path(TEST_DIR / "multas_mayo_2024.csv"),
        id="multas-mayo-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-23-multas-circulacion-detalle-csv/download/210104-23-multas-circulacion-detalle-csv.csv",
        Path(TEST_DIR / "multas_abril_2024.csv"),
        id="multas-abril-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-24-multas-circulacion-detalle-csv/download/210104-24-multas-circulacion-detalle-csv",
        Path(TEST_DIR / "multas_marzo_2024.csv"),
        id="multas-marzo-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-337-multas-circulacion-detalle-csv/download/210104-337-multas-circulacion-detalle-csv.csv",
        Path(TEST_DIR / "multas_febrero_2024.csv"),
        id="multas-febrero-2024.csv",
    ),
    pytest.param(
        "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-26-multas-circulacion-detalle-csv/download/210104-26-multas-circulacion-detalle-csv.csv",
        Path(TEST_DIR / "multas_enero_2024.csv"),
        id="multas-enero-2024.csv",
    ),
]


from traficFines import MadridFines
from traficFines.madridFines import MadridError


@pytest.fixture
def clean_cache(tmp_path, monkeypatch):
    CACHE_DIR = tmp_path / ".my_cache"
    # Usamos tmp_path para evitar utlizar el file-system real y garantizar un entorno limpio para cada test
    monkeypatch.setattr("traficFines.cache.cache.CACHE_DIR", CACHE_DIR)

    app_dir = CACHE_DIR / APP_NAME
    if app_dir.exists():
        shutil.rmtree(app_dir)

    yield {"cache_dir": CACHE_DIR}


@pytest.fixture
def madrid_fines_factory():
    def _make_madrid_fines(app_name=APP_NAME, obsolescence=OBSOLESCENCE):
        return MadridFines(app_name=app_name, obsolescence=obsolescence)

    return _make_madrid_fines


@pytest.fixture
def mock_responses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        for test_case in TEST_CASES:
            url, content_file = test_case.values
            with content_file.open("r", encoding="utf-8") as f:
                content = f.read()
            rsps.add(responses.GET, url, body=content, status=200)
        yield rsps


def test_madrid_fines_properties(clean_cache, madrid_fines_factory, mock_responses):
    madrid_fines = madrid_fines_factory()
    assert (
        repr(madrid_fines)
        == f"MadridFines(app_name='{APP_NAME}', obsolescence={OBSOLESCENCE})"
    )
    assert (
        str(madrid_fines)
        == f"MadridFines(app_name='{APP_NAME}', obsolescence={OBSOLESCENCE})"
    )

    assert madrid_fines.cacheurl == f"La caché de '{APP_NAME}' contiene 0 archivos."
    assert madrid_fines.data.empty is True
    assert len(madrid_fines.loaded) == 0
    assert isinstance(madrid_fines.metadata, str)
    for i in range(1, 13):
        assert f"{2024}{i:02d}" in madrid_fines.metadata


@pytest.mark.parametrize(
    "url, content_file",
    [
        pytest.param(
            "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle.rdf",
            Path(TEST_DIR / "metadata_fake.rdf"),
            id="metadata_fake.rdf",
        )
    ],
)
@responses.activate
def test_madrid_fines_rdf_parser_fake_mes(
    clean_cache, madrid_fines_factory, url, content_file
):
    with responses.RequestsMock() as rsps:
        # Mock para la petición de los metadatos usando un fichero con un mes no válido para evaluar el menejo de error en el parser
        # el fichero también contiene metadatos correctos de diciembre de 2024
        with content_file.open("r", encoding="utf-8") as f:
            content = f.read()
        rsps.add(responses.GET, url, body=content, status=200)

        madrid_fines = madrid_fines_factory()

        assert "202412" in madrid_fines.metadata
        assert len(rsps.calls) == 1


def test_madrid_fines_get_url(clean_cache, madrid_fines_factory, mock_responses):
    madrid_fines = madrid_fines_factory()
    url = madrid_fines.get_url(2024, 12)
    assert (
        url
        == "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv"
    )

    with pytest.raises(MadridError, match="No se encontró la URL para 2023-11."):
        madrid_fines.get_url(2023, 11)


def test_madrid_fines_add(clean_cache, madrid_fines_factory, mock_responses):
    madrid_fines = madrid_fines_factory()

    madrid_fines.add(2024, 12)
    # Volver a cargar los mismos datos no debería hacer una nueva petición
    madrid_fines.add(2024, 12)

    assert not madrid_fines.data.empty
    assert len(madrid_fines.loaded) == 1
    assert (2024, 12) in madrid_fines.loaded
    # Tiene que hacer dos llamadas: una para los metadatos y otra para los datos de diciembre 2024
    # La segunda llamada a add no hace nada
    assert len(mock_responses.calls) == 2

    # Cargamos el año completo
    madrid_fines.add(2024)

    # En la carga de un año completo si los meses no existen en los metadatos no se lanza un error
    # se deja lanza un mensaje y se continua con el siguiente mes
    madrid_fines.add(2025)

    assert len(madrid_fines.loaded) == 12
    for month in range(1, 13):
        assert (2024, month) in madrid_fines.loaded
    # Solo se hacen 11 llamadas (+ las 2 anteriores) más para cargar los meses restantes, no se repite
    assert len(mock_responses.calls) == 13


# Ver: https://docs.pytest.org/en/stable/how-to/tmp_path.html
def test_madrid_fines_hour(clean_cache, madrid_fines_factory, mock_responses, tmp_path):
    madrid_fines = madrid_fines_factory()
    with pytest.raises(
        MadridError,
        match="No hay datos cargados para generar el gráfico.",
    ):
        madrid_fines.fines_hour()

    dirname = tmp_path / "home"
    dirname.mkdir()
    filename = dirname / "evolucion_multas.jpg"
    madrid_fines.add(2024)

    assert len(list(dirname.iterdir())) == 0

    # Crea la imagen en el directorio temporal
    madrid_fines.fines_hour(fig_name=filename)

    assert len(list(dirname.iterdir())) == 1
    assert filename.exists()
    assert filename.stat().st_size > 0
    with filename.open("rb") as f:
        # Comprobamos el magic header del fichero jpg generado
        # Ver: https://en.wikipedia.org/wiki/List_of_file_signatures
        magic_header = f.read(12)
        assert magic_header == b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"


def test_madrid_fines_calification(clean_cache, madrid_fines_factory, mock_responses):
    madrid_fines = madrid_fines_factory()
    with pytest.raises(
        MadridError,
        match="No hay datos cargados para analizar la calificación de las multas.",
    ):
        madrid_fines.fines_calification()

    madrid_fines.add(2024)
    df = madrid_fines.fines_calification()

    assert not df.empty
    assert df.shape == (12, 3)
    for month in range(1, 13):
        assert (month, 2024) in df.index
    assert df.columns.to_list() == ["GRAVE", "LEVE", "MUY GRAVE"]
    assert df.loc[(1, 2024)].to_list() == [1175, 6813, 11]


def test_madrid_fines_total_payment(clean_cache, madrid_fines_factory, mock_responses):
    madrid_fines = madrid_fines_factory()
    with pytest.raises(
        MadridError,
        match="No hay datos cargados para analizar el importe total de las multas.",
    ):
        madrid_fines.total_payment()

    madrid_fines.add(2024)
    df = madrid_fines.total_payment()

    assert not df.empty
    assert df.shape == (12, 2)
    for month in range(1, 13):
        assert (month, 2024) in df.index
    assert df.columns.to_list() == ["minimo", "maximo"]
    assert df.loc[(1, 2024)].to_list() == [386405.0, 772810.0]
