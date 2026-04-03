import json
from io import StringIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

from ..cache import CacheURL
from .rdf_parser import parse_multas_madrid_rdf

METADATA_OBSOLESCENCE = 1
# Ver: https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle
# El fichero rdf contiene la información de todas las multas de circulación que el Ayuntamiento de Madrid tramita cada mes
METADATA_URL = "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle.rdf"


class MadridError(Exception):
    """
    Excepción personalizada para errores relacionados con la clase MadridFines.
    """

    pass


class MadridFines:
    def __init__(self, app_name, obsolescence=10):
        self._cacheurl = CacheURL(app_name=app_name, obsolescence=obsolescence)
        self._data = pd.DataFrame()
        self._loaded = []
        self._metadata = {}
        self.update()

    @property
    def cacheurl(self) -> str:
        return str(self._cacheurl)

    @property
    def data(self) -> pd.DataFrame:
        return self._data.head()

    @property
    def loaded(self) -> list:
        return self._loaded

    @property
    def metadata(self) -> str:
        sort_metadata = sorted(
            self._metadata.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True
        )
        return json.dumps({f"{y}{m:02d}": v for (y, m), v in sort_metadata}, indent=4)

    def update(self) -> None:
        """
        Actualiza los metadatos de las multas de circulación y los carga en memoria.

        Raises:
            HTTPError: Si la petición a la URL de metadatos no es exitosa.
        """
        response = requests.get(METADATA_URL)
        response.raise_for_status()
        metadata = parse_multas_madrid_rdf(response.text)
        self._metadata = metadata

    def get_url(self, year: int, month: int) -> str:
        """
        Devuelve la URL de acceso al detalle de multas de circulación para un año y mes específicos.

        Args:
            year: Año de las multas de circulación.
            month: Mes de las multas de circulación.

        Returns:
            URL de acceso al detalle de multas de circulación.

        Raises:
            MadridError: Si no se encuentra la URL para el año y mes especificados.
        """
        url = self._metadata.get((year, month))
        if not url:
            raise MadridError(f"No se encontró la URL para {year}-{month:02d}.")
        return url

    def _load(self, year: int, month: int) -> pd.DataFrame:
        """
        Carga los datos de multas de circulación para un año y mes específicos usando un objeto CacheURL.

        Args:
            year: Año de las multas de circulación.
            month: Mes de las multas de circulación.

        Returns:
            DataFrame con los datos de multas de circulación.
        """
        url = self.get_url(year, month)
        df = pd.read_csv(StringIO(self._cacheurl.get(url)), sep=";", encoding="latin1")
        self._clean(df)
        return df

    @staticmethod
    def _clean(df: pd.DataFrame) -> None:
        """
        Limpia y preprocesa el DataFrame de multas de circulación.

        Args:
            df: DataFrame con los datos de multas de circulación.

        Returns:
            None
        """

        def normalize_columns(data):
            """
            Función auxiliar para normalizar los nombres de las columnas.
            """
            return data.strip().upper().replace("-", "_").replace(" ", "_")

        df.rename(columns=normalize_columns, inplace=True)

        # Eliminar espacios en blanco de las columnas de tipo string
        for col in df.columns:
            if df[col].dtype == "str":
                df[col] = df[col].str.strip()

        # Convertir columnas numéricas a tipo numérico:
        for col in ["VEL_LIMITE", "VEL_CIRCULA", "COORDENADA_X", "COORDENADA_Y"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Creación de un index de fecha
        df["FECHA"] = pd.to_datetime(
            df["ANIO"].astype(str)
            + "-"
            + df["MES"].astype(str)
            + "-01 "
            + df["HORA"].map(lambda x: f"{int(x):02d}:{int(round(x % 1 * 100)):02d}"),
            format="%Y-%m-%d %H:%M",
        )
        df.set_index("FECHA", drop=True, inplace=True)

    def add(self, year: int, month: int | None = None) -> None:
        """
        Añade información de multas de circulación de un año y mes específicos al DataFrame de datos `data`.
        Evita duplicar datos ya cargados, si el mes ya existe no hace nada. En caso de que el mes no exita lo carga
        y actualiza el atributo `loaded`. Si el mes es `None` se añaden todos los meses del año.

        Args:
            year: Año de las multas de circulación.
            month: Mes de las multas de circulación (opcional).

        Returns:
            None
        """
        if month is not None:
            if (year, month) in self._loaded:
                return
            df = self._load(year, month)
            self._clean(df)
            self._data = pd.concat([self._data, df])
            self._loaded.append((year, month))
        else:
            for m in range(1, 13):
                self.add(year, m)

    def fines_hour(self, fig_name: str = "evolucion_multas.jpg") -> None:
        """
        Genera un gráfico de líneas que muestra la evolución de las multas a lo largo de las horas del día.
        Si hay varios messes cargados, dibuja una linea por cada mes.

        Args:
            fig_name: Nombre del archivo de imagen donde se guardará el gráfico.

        Returns:
            None
        """
        if self._data.empty:
            raise MadridError("No hay datos cargados para generar el gráfico.")
        sanciones_yearmonth_hour = (
            self._data.groupby(
                [
                    self._data.index.hour.rename("Hour"),
                    self._data.index.to_period("M").rename("YearMonth"),
                ]
            )
            .size()
            .unstack(level=-1, fill_value=0)
        )

        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        for yearmonth in sanciones_yearmonth_hour.columns:
            ax.plot(
                sanciones_yearmonth_hour.index,
                sanciones_yearmonth_hour[yearmonth],
                marker="o",
                label=yearmonth,
            )

        ax.set_title("Sanciones por hora", fontsize=18, fontweight="bold", y=1.05)

        ax.set_xticks(sanciones_yearmonth_hour.index)
        ax.set_xlabel("Hora")
        ax.set_ylabel("Número de sanciones")

        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.8)

        ax.legend(title="Año-Mes")

        fig.savefig(fig_name, bbox_inches="tight")
        plt.close(fig)

    def fines_calification(self) -> pd.DataFrame:
        """
        Analiza la distribución de multas por calidicación mes y año.

        Returns:
            DataFrame con la distribución de multas por calificación, mes y año.
        """
        if self._data.empty:
            raise MadridError(
                "No hay datos cargados para analizar la calificación de las multas."
            )
        df = self._data.copy()
        return (
            df.groupby(
                [
                    df["MES"].rename("Mes"),
                    df["ANIO"].rename("Año"),
                    df["CALIFICACION"].rename("Calificación"),
                ]
            )
            .size()
            .unstack(-1)
        )

    def total_payment(self) -> pd.DataFrame:
        """
        Resumen con el importe total (mínimo y máximo) reacaudado por mes y año.

        NOTA: Una multa puede tener descuento por pronto pago del 50%, pero cabe la posibilidad de que
        el infractor no realice el pago en fecha para acojerse a dicho descuento.

        Returns:
            DataFrame con el importe total (mínimo y máximo) recaudado por mes y año.
        """
        if self._data.empty:
            raise MadridError(
                "No hay datos cargados para analizar el importe total de las multas."
            )
        df = self._data.copy()
        df["IMP_DESCUENTO"] = np.where(
            df["DESCUENTO"] == "SI", df["IMP_BOL"] / 2, df["IMP_BOL"]
        )

        return df.groupby(
            [
                df.index.month.rename("Mes"),
                df.index.year.rename("Año"),
            ]
        ).agg(
            minimo=pd.NamedAgg(column="IMP_DESCUENTO", aggfunc="sum"),
            maximo=pd.NamedAgg(column="IMP_BOL", aggfunc="sum"),
        )
