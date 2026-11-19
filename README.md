# Star Wars Galaxies en castellano

Traducción no oficial al español de España del cliente de **Star Wars Galaxies** (versión clásica Pre-CU, compatible con SWGEmu).

> Solo contiene la traducción. **No incluye ningún archivo del juego**: necesitas tu copia original de Star Wars Galaxies.

## Estado

- Todo el juego traducido: 155.240 textos en 2.338 archivos.
- Revisado a mano: interfaz (menús, ventanas, opciones, chat, bazar, fabricación…), profesiones y habilidades (incluido el camino Jedi), comandos y nombres de objetos más comunes.
- Términos unificados con un glosario fijo (ordenador, droide, deslizador, condensador, bláster, Holocrón…).
- Resto (misiones, diálogos, criaturas, combate): traducción automática con un modelo local, con comprobación de variables del juego. Pueden quedar frases mejorables.
- Los nombres propios (naves, personajes, lugares, marcas) se dejan en inglés a propósito.

## Generar `castellano.tre`

El `.tre` no se distribuye porque se construye a partir de los archivos de tu juego. Necesitas Python 3 y tu cliente **sin** el parche instalado:

```bash
git clone https://github.com/ElderArtemis/swg-spanish.git && cd swg-spanish
python3 treutil.py extract /ruta/al/cliente orig      # saca string/en/*.stf de tus .tre
python3 hacer_tre.py orig es castellano.tre
```

## Instalación en el cliente

1. Copia `castellano.tre` en la carpeta del cliente (donde está `SWGEmu.exe`).
2. Edita `swgemu_live.cfg` y, justo debajo de `[SharedFile]`, añade la línea `searchTree_00_26=castellano.tre`. Cambia `maxSearchPriority=26` por `maxSearchPriority=27`.
3. Abre el juego.

Para volver al inglés, borra esa línea (o el archivo).

## Cómo se genera

Las traducciones están en `es/`, un JSON por cada archivo de texto del juego (`string/en/<ruta>.stf`, con `/` sustituido por `__`). Las claves que faltan se quedan en inglés.

- `treutil.py`: lee archivos `.tre` y `.stf`; `extract` saca los textos originales de tu cliente.
- `trecrc.py`: CRC de nombres de archivo de SWG (comprobado con los `.tre` originales).
- `hacer_tre.py`: genera el `.stf` traducido de cada archivo y los empaqueta en un `.tre`.
- `traducir.py`: traduce lo pendiente con un modelo local por la API de Ollama, con glosario fijo y comprobación de las variables del juego (`%TU`, `%DI`, `\#...`).
- `aplicar_lote.py`: valida un lote traducido a mano (claves y variables) y lo incorpora a `es/`.

## Aviso

Proyecto de aficionados sin ánimo de lucro. Star Wars Galaxies es propiedad de sus respectivos titulares; este repositorio no distribuye contenido del juego.
