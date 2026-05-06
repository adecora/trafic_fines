import re
import xml.etree.ElementTree as ET

# Xml namespaces
# Ver: https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DCAT_NS = "http://www.w3.org/ns/dcat#"
DCT_NS = "http://purl.org/dc/terms/"

# Exiten lo ficheros de tipo: 210104-82-multas-circulacion-detalle-txt que traen el dato en formato txt, separa por tabuladores
TITLE_RE = re.compile(r"^210104-\d+-multas-circulacion-detalle(?:-csv)?$", re.IGNORECASE)
DESCRIPTION_RE = re.compile(
    r"^Detalle. (?P<month>\w+) (?P<year>\d{4})$",
    re.IGNORECASE,
)

# Por definición de la práctica sólo vamos a considerar los datos desde junio de 2017
BOTTOM_DATE = (2017, 6)

MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def parse_multas_madrid_rdf(content: str) -> dict[tuple[int, int], str]:
    """
    Ver: https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle
    Parsea el contenido del fichero RDF con los metadatos de las multas de circulación del
    Ayuntamiento de Madrid y extrae la información de metadata de las multas de circulación.

    Args:
        content: Contenido del fichero RDF a parsear.

    Returns:
        Un diccionario con claves como tuplas (año, mes) y valores las URLs de acceso al detalle de multas de circulación.
    """
    root = ET.fromstring(content)
    metadata = {}

    for distribution in root.findall(f".//{{{DCAT_NS}}}Distribution"):
        title = distribution.find(f"{{{DCT_NS}}}title")
        if not TITLE_RE.match(title.text):
            continue
        description = distribution.find(f"{{{DCT_NS}}}description")
        m = DESCRIPTION_RE.match(description.text)
        if m:
            try:
                year = int(m.group("year"))
                month = MONTHS[m.group("month").lower()]

                # Ver: https://docs.python.org/3/library/stdtypes.html#common-sequence-operations
                if (year, month) < BOTTOM_DATE:
                    continue

                access_url = distribution.find(f"{{{DCAT_NS}}}accessURL")
                resource_url = access_url.get(f"{{{RDF_NS}}}resource")
                metadata[(year, month)] = resource_url
            except Exception as e:
                print(f"Error parseando la metadata en: {description.text}: {e}")
    return metadata
