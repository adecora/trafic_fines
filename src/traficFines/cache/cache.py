"""
Implementación de la clase Cache para guardar y recuperar datos en disco, de forma que estén disponnibles incluso al cerrar el programa.
"""

import datetime as dt
from pathlib import Path
from time import time
from typing import TextIO

CACHE_DIR = Path.home() / ".my_cache"


class CacheError(Exception):
    """
    Excepción personalizada para errores relacionados con la caché.
    """

    pass


class Cache:
    def __init__(self, app_name: str, obsolescence: int = 10):
        """
        Inicializa la caché para una aplicación específica.

        Args:
            app_name: Nombre de la aplicación para la que se crea la caché.
            obsolescence: Tiempo en días para considerar los datos como obsoletos.
        """
        if obsolescence < 1:
            raise CacheError("El tiempo de obsolescencia debe ser al menos 1 día.")
        self._app_name = app_name
        self._obsolescence = obsolescence
        self._cache_dir = CACHE_DIR / app_name
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def app_name(self) -> str:
        return self._app_name

    @property
    def obsolescence(self) -> int:
        return self._obsolescence

    @property
    def cache_dir(self) -> str:
        return str(self._cache_dir)

    def __str__(self) -> str:
        cache_files = [x for x in self._cache_dir.iterdir() if x.is_file()]
        size = len(cache_files)
        return f"La caché de '{self._app_name}' contiene {size} archivo{'s' if size != 1 else ''}."

    def __repr__(self) -> str:
        return f"Cache(app_name='{self._app_name}', obsolescence={self._obsolescence})"

    def set(self, name: str, data: str) -> None:
        """
        Almacena los datos en la caché con el nombre especificado.

        Args:
            name: Nombre del archivo de caché.
            data: Datos a guardar en la caché.

        Returns:
            None
        """
        cache_file = self._cache_dir / name
        with cache_file.open("w", encoding="utf-8") as f:
            f.write(data)

    def set_fromfile(self, name: str, data: TextIO | str | Path) -> None:
        """
        Almacena los datos de un archivo en la caché con el nombre especificado.

        Args:
            name: Nombre del archivo de caché.
            data: File-like object con los datos a guardar en la caché, o una ruta a un archivo.

        Returns:
            None
        """
        close_source = False
        if not hasattr(data, "read"):
            data = open(data, "r")
            close_source = True
        cache_file = self._cache_dir / name

        with cache_file.open("w", encoding="utf-8") as f_out:
            for line in data:
                f_out.write(line)

        if close_source:
            data.close()

    def exists(self, name: str) -> bool:
        """
        Comprueba si ya existe un fichero con el nombre especificado en la caché.

        Args:
            name: Nombre del archivo de caché.

        Returns:
            True si el archivo existe, False en caso contrario.
        """
        return (self._cache_dir / name).exists()

    def _get_file_age(self, name: str) -> dt.timedelta:
        """
        Devuelve la edad del fichero almacenado en la caché con el nombre indicado.

        Args:
            name: Nombre del archivo de caché.

        Returns:
            Edad del archivo como un objeto timedelta.

        Raises:
            CacheError: Si el archivo de caché no existe.
        """
        cache_file = self._cache_dir / name
        if not cache_file.exists():
            raise CacheError(f"El archivo de caché '{name}' no existe.")

        stats = cache_file.stat()
        # Ver: https://docs.python.org/3.12/library/os.html#os.stat_result.st_birthtime
        # Desde la versión 3.12 de Python se puede usar st_birthtime, pero este atributo no está siempre expuesto por el sistema operativo
        # si no existe se usa st_mtime que es tiempo desde la última modificación
        if hasattr(stats, "st_birthtime"):
            birth = stats.st_birthtime
        else:
            birth = stats.st_mtime
        return dt.timedelta(seconds=(time() - birth))

    def how_old(self, name: str) -> float:
        """
        Devuelve la edad en milisegundos del fichero almacenado en la caché con el nombre indicado.

        Args:
            name: Nombre del archivo de caché.

        Returns:
            Edad del archivo en milisegundos.

        Raises:
            CacheError: Si el archivo de caché no existe.
        """
        return self._get_file_age(name).total_seconds() * 1000

    def load(self, name: str) -> str:
        """
        Recupera los datos almacenados en la caché con el nombre especificado.

        Args:
            name: Nombre del archivo de caché.

        Returns:
            Datos cargados desde la caché.

        Raises:
            CacheError: Si el archivo de caché no existe o está obsoleto.
        """
        cache_file = self._cache_dir / name
        if not cache_file.exists():
            raise CacheError(f"El archivo de caché '{name}' no existe.")

        file_age = self._get_file_age(name)
        obsolescence = dt.timedelta(days=self._obsolescence)
        if file_age > obsolescence:
            raise CacheError(
                f"El archivo de caché '{name}' está obsoleto (edad: {file_age})."
            )

        with cache_file.open("r") as f:
            return f.read()

    def delete(self, name: str) -> None:
        """
        Borra de la caché el fichero con el nombre especificado.

        Args:
            name: Nombre del archivo de caché a eliminar.

        Returns:
            None
        """
        cache_file = self._cache_dir / name
        if not cache_file.exists():
            return
        cache_file.unlink()

    def clear(self) -> None:
        """
        Borra todos los archivos de la caché.

        Returns:
            None
        """
        for cache_file in self._cache_dir.iterdir():
            if cache_file.is_file():
                cache_file.unlink()
