"""
Especialización de la clase Cache para trabajar con datos descargados de internet (URLs).
"""

from hashlib import md5
from time import sleep

import requests

from .cache import Cache, CacheError


class CacheURL(Cache):
    @staticmethod
    def _url_to_filename(url: str) -> str:
        """
        Convierte una URL en un nombre de fichero seguro utilizando un hash.

        Args:
            url: URL a convertir.

        Returns:
            Nombre de fichero seguro basado en el hash de la URL.
        """
        url_hashed = md5(url.encode("utf-8")).hexdigest()
        return url_hashed

    def get(self, url: str) -> str:
        """
        Recupera el contenido de un archivo de caché específico si existe y no está obsoleto, si no, realiza una
        petición a la URL y guarda el resultado en la caché.

        Args:
            url: URL del archivo de caché a recuperar.

        Returns:
            Contenido del archivo de caché como una cadena.

        Raises:
            CacheError: Si el archivo de caché no existe o está obsoleto.
            HTTPError: Si la petición a la URL no es exitosa.
        """
        name = self._url_to_filename(url)
        try:
            return super().load(name)
        except CacheError:
            # Si el archivo de caché existe pero está obsoleto, lo eliminamos y seguimos para obtener datos actualizados
            super().delete(name)

        response = requests.get(url)
        # Lanza una excepción si la respuesta no es exitosa
        response.raise_for_status()
        content = response.text
        super().set(name, content)
        return content

    def exists(self, url: str) -> bool:
        """
        Comprueba si ya existe un fichero con el nombre especificado en la caché.

        Args:
            url: URL del archivo de caché.

        Returns:
            True si el archivo existe, False en caso contrario.
        """
        name = self._url_to_filename(url)
        return super().exists(name)

    def how_old(self, url: str) -> float:
        """
        Devuelve la edad en milisegundos del fichero almacenado en la caché con el nombre indicado.

        Args:
            url: URL del archivo de caché.

        Returns:
            Edad del archivo en milisegundos.

        Raises:
            CacheError: Si el archivo de caché no existe.
        """
        name = self._url_to_filename(url)
        return super().how_old(name)

    def load(self, url: str) -> str:
        """
        Carga los datos de la caché con el nombre especificado.

        Args:
            url: URL del archivo de caché.

        Returns:
            Datos cargados desde la caché.

        Raises:
            CacheError: Si el archivo de caché no existe.
        """
        name = self._url_to_filename(url)
        return super().load(name)

    def delete(self, url: str) -> None:
        """
        Borra de la caché el fichero con el nombre especificado.

        Args:
            url: URL del archivo de caché a eliminar.
        Returns:
            None
        """
        name = self._url_to_filename(url)
        return super().delete(name)
