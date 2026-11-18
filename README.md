# Star Wars Galaxies en castellano

Traducción no oficial al español de España del cliente de **Star Wars Galaxies** (versión clásica Pre-CU, compatible con SWGEmu).

> Solo contiene la traducción. **No incluye ningún archivo del juego**: necesitas tu copia original de Star Wars Galaxies.

## Estado

- Interfaz completa (menús, ventanas, opciones, chat, bazar, fabricación…): traducida y revisada a mano.
- Resto de textos (habilidades, comandos, objetos, criaturas, misiones, diálogos, combate): traducción automática con un modelo local, pendiente de revisión.

## Instalación en el cliente

1. Copia `castellano.tre` en la carpeta del cliente (donde está `SWGEmu.exe`).
2. Edita `swgemu_live.cfg` y, justo debajo de `[SharedFile]`, añade la línea `searchTree_00_26=castellano.tre`. Cambia `maxSearchPriority=26` por `maxSearchPriority=27`.
3. Abre el juego.

Para volver al inglés, borra esa línea (o el archivo).

## Cómo se genera

Las traducciones están en `es/`, un JSON por cada archivo de texto del juego (`string/en/<ruta>.stf`, con `/` sustituido por `__`). Las claves que faltan se quedan en inglés.

```bash
# 1. Extraer los textos originales del cliente a orig/string/en (no se incluyen aquí)
# 2. Generar el .tre
python3 hacer_tre.py orig es castellano.tre
```

- `treutil.py`: lee archivos `.tre` y `.stf`.
- `trecrc.py`: CRC de nombres de archivo de SWG (comprobado con los `.tre` originales).
- `hacer_tre.py`: genera el `.stf` traducido de cada archivo y los empaqueta en un `.tre`.
- `traducir.py`: traduce lo pendiente con un modelo local por la API de Ollama, con glosario fijo y comprobación de las variables del juego (`%TU`, `%DI`, `\#...`).
- `aplicar_lote.py`: valida un lote traducido a mano (claves y variables) y lo incorpora a `es/`.

## Aviso

Proyecto de aficionados sin ánimo de lucro. Star Wars Galaxies es propiedad de sus respectivos titulares; este repositorio no distribuye contenido del juego.
