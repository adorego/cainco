# Reporte de fotos — Cainco

Generado por `tools/mejorar_fotos.py`. Ordenado de mejor a peor según el diagnóstico del original.

**Super-resolución usada:** Real-ESRGAN x4plus / x2plus (PyTorch, CPU), mezclado 70/30 con bicúbica para conservar textura

- **Nitidez**: varianza del Laplaciano con la imagen normalizada a 1024 px (más alto = más nítida; <100 es blanda).
- **Q JPEG**: calidad estimada a partir de la tabla de cuantización.
- **Bloques**: salto de gradiente en bordes 8×8 vs. interior (1.0 = sin artefactos; >1.15 = bloques visibles).
- **Recomprimida**: resolución típica de WhatsApp (lado mayor ≤1280/1600) y/o Q ≤ 85.

| # | Foto | Original | KB | Q JPEG | Bloques | Nitidez orig → final | Recompr. | Puntaje | Recomendación | Final | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `taller-02` | 960×1280 | 142 | 78 | 1.35 | 529 → 902 | sí | 0.95 | **usar** | 1920×2253 | foto de obra (persona trabajando y restos de material); se usa como 'durante'; sin enderezar; WB 1.00/1.01/0.99, gamma 0.80 |
| 2 | `oficina-04` | 960×1280 | 180 | 78 | 1.42 | 646 → 944 | sí | 0.94 | **usar** | 1920×2560 | foto de obra con nylon en el piso; se presenta como 'durante la instalación'; sin enderezar; WB 0.96/0.99/1.05, gamma 0.88 |
| 3 | `locker-01` | 960×1280 | 118 | 78 | 1.35 | 314 → 469 | sí | 0.87 | **usar** | 1828×2560 | balance de blancos suave para no enfriar el color de los lockers; rot -0.9°, verticales k=1.047; WB 1.02/1.00/0.98, gamma 0.90 |
| 4 | `placard-04` | 960×1280 | 100 | 78 | 1.26 | 211 → 386 | sí | 0.82 | **usar** | 1720×2560 | cables sueltos que cruzan el frente (no se pueden recortar sin perder el mueble); verticales corregidas; rot -3.0°, verticales k=1.080 (acotada); WB 0.95/0.99/1.06, gamma 0.88 |
| 5 | `oficina-02` | 1032×774 | 100 | 78 | 1.28 | 379 → 556 | sí | 0.80 | **usar** | 1905×1548 | rot +0.7°, verticales k=1.080 (acotada); WB 1.04/1.00/0.97, gamma 0.80 |
| 6 | `taller-01` | 960×1280 | 133 | 78 | 1.38 | 175 → 269 | sí | 0.77 | **usar** | 1920×2560 | sin enderezar; WB 1.00/0.99/1.02, gamma 0.80 |
| 7 | `oficina-05` | 960×1280 | 71 | 78 | 1.59 | 196 → 326 | sí | 0.75 | **usar** | 1772×2560 | rot +0.4°, verticales k=1.080 (acotada); WB 0.94/1.00/1.07 |
| 8 | `cocina-01` | 716×716 | 52 | 78 | 1.46 | 525 → 220 | sí | 0.73 | **usar** | 1611×1611 | sin líneas fiables; WB 0.99/1.00/1.01 |
| 9 | `comercial-01` | 963×1280 | 114 | 78 | 1.63 | 186 → 351 | sí | 0.73 | **usar** | 1926×2560 | nocturna con reflejos verdes de los vidrios; sin enderezar; WB 1.01/0.98/1.00, gamma 0.80 |
| 10 | `placard-03` | 960×1280 | 104 | 78 | 1.40 | 135 → 265 | sí | 0.72 | **usar** | 1768×2560 | rot +1.5°, verticales k=1.080 (acotada); WB 0.96/0.99/1.06, gamma 0.80 |
| 11 | `comercial-03` | 963×1280 | 90 | 78 | 1.54 | 146 → 292 | sí | 0.71 | **usar** | 1926×2560 | nocturna; cable en el piso en el centro que no se puede recortar; sin enderezar; WB 0.97/0.98/1.06, gamma 0.90 |
| 12 | `bano-07` | 1280×960 | 106 | 78 | 1.65 | 153 → 278 | sí | 0.70 | **mejorar** | 2560×1920 | sin líneas fiables; WB 0.94/1.00/1.07 |
| 13 | `bano-06` | 1280×960 | 63 | 78 | 1.30 | 93 → 162 | sí | 0.67 | **mejorar** | 2384×1920 | rot -1.3°, verticales k=1.070; WB 0.98/1.00/1.02 |
| 14 | `bano-05` | 960×1280 | 75 | 78 | 1.48 | 111 → 251 | sí | 0.67 | **mejorar** | 1764×2560 | rot -2.0°, verticales k=1.080 (acotada); WB 0.99/0.99/1.02 |
| 15 | `locker-02` | 963×1280 | 81 | 78 | 1.40 | 92 → 257 | sí | 0.66 | **mejorar** | 1733×2125 | silla en primer plano que no se puede recortar sin cortar los lockers; terminación a confirmar (OSB); sin líneas fiables; WB 0.95/0.98/1.08 |
| 16 | `bano-04` | 960×1280 | 63 | 78 | 1.49 | 88 → 199 | sí | 0.63 | **mejorar** | 1756×2560 | rot -2.2°, verticales k=1.080 (acotada); WB 0.99/0.99/1.02 |
| 17 | `comercial-02` | 963×1280 | 89 | 78 | 1.69 | 106 → 209 | sí | 0.63 | **mejorar** | 1926×2560 | nocturna, dominante verde; sin enderezar; gamma 0.86 |
| 18 | `bano-01` | 1280×960 | 87 | 78 | 1.79 | 117 → 211 | sí | 0.62 | **mejorar** | 2253×1920 | recorte a la izquierda para sacar el inodoro embolsado; sin líneas fiables; WB 1.00/1.00/1.01 |
| 19 | `bano-03` | 1280×960 | 93 | 78 | 1.60 | 76 → 143 | sí | 0.59 | **mejorar** | 2150×1920 | recorte a la izquierda para sacar el inodoro embolsado; sin líneas fiables; WB 1.00/0.99/1.01 |
| 20 | `placard-01` | 720×1280 | 54 | 78 | 1.84 | 129 → 263 | sí | 0.55 | **mejorar** | 1299×2560 | rot +2.1°, verticales k=1.080 (acotada); WB 0.95/1.00/1.06 |
| 21 | `oficina-03` | 963×1280 | 85 | 78 | 1.71 | 67 → 135 | sí | 0.54 | **mejorar** | 1926×2560 | sin líneas fiables; WB 0.97/0.98/1.05, gamma 0.80 |
| 22 | `bano-02` | 960×1280 | 85 | 78 | 1.90 | 79 → 148 | sí | 0.54 | **mejorar** | 1920×2560 | sin líneas fiables; WB 0.93/1.01/1.07, gamma 0.91 |
| 23 | `oficina-01` | 1032×774 | 59 | 78 | 1.57 | 73 → 149 | sí | 0.46 | **mejorar** | 1905×1548 | rot +0.5°, verticales k=1.080 (acotada); WB 1.02/1.00/0.98, gamma 0.89 |
| 24 | `placard-05` | 720×1280 | 46 | 78 | 1.89 | 48 → 111 | sí | 0.37 | **pedir original** | 1440×2560 | sin líneas fiables; WB 0.96/1.00/1.04 |
| 25 | `cocina-05` | 774×1032 | 36 | 78 | 1.85 | 50 → 60 | sí | 0.35 | **pedir original** | 1548×2064 | sin super-resolución: el modelo convertía la guarda de venecitas en formas parecidas a letras; sin líneas fiables; WB 1.01/1.00/0.99 |
| 26 | `placard-02` | 720×1280 | 54 | 78 | 1.57 | 29 → 100 | sí | 0.34 | **pedir original** | 1440×2560 | sin líneas fiables; WB 0.93/1.01/1.07 |
| 27 | `cocina-07` | 581×1032 | 32 | 78 | 1.72 | 51 → 66 | sí | 0.32 | **pedir original** | 1307×2322 | sin super-resolución: guarda de venecitas; original muy chico (581 px); sin líneas fiables; WB 0.97/1.01/1.02 |
| 28 | `oficina-06` | 1152×560 | 26 | 78 | 2.03 | 58 → 118 | sí | 0.30 | **pedir original** | 2128×1120 | rot +2.1°, verticales k=1.080 (acotada); WB 0.98/1.00/1.03 |
| 29 | `cocina-03` | 1152×864 | 34 | 78 | 2.27 | 40 → 96 | sí | 0.29 | **pedir original** | 2304×1728 | sin líneas fiables; WB 0.94/1.01/1.07 |
| 30 | `cocina-04` | 1032×774 | 37 | 78 | 2.00 | 34 → 44 | sí | 0.26 | **pedir original** | 2064×1548 | sin super-resolución: el modelo deformaba la guarda de venecitas; sin líneas fiables; WB 1.00/1.00/1.00 |
| 31 | `comercial-04` | 963×1280 | 59 | 78 | 2.31 | 22 | sí | 0.24 | **descartar** | — | nocturna con dominante verde fuerte, borrosa y con objetos ajenos (silla, balde): no se salva, pedir foto nueva |
| 32 | `cocina-06` | 1032×774 | 40 | 78 | 1.94 | 26 → 82 | sí | 0.22 | **pedir original** | 1902×1548 | rot +3.3°, verticales k=1.080 (acotada); WB 1.02/1.00/0.98 |
| 33 | `comercial-06` | 1152×648 | 34 | 78 | 1.96 | 21 → 53 | sí | 0.17 | **pedir original** | 2304×1296 | piso quemado a blanco en el original: no se recupera; sin enderezar; gamma 0.83 |
| 34 | `comercial-05` | 1152×648 | 34 | 78 | 2.04 | 20 → 77 | sí | 0.15 | **pedir original** | 2304×1296 | obra sin terminar, muy comprimida; sin enderezar; WB 0.94/1.00/1.07, gamma 0.81 |

## Para pedir a Cainco

Fotos que conviene reemplazar (original sin comprimir o foto nueva):

- `placard-05` — baja calidad de origen
- `cocina-05` — sin super-resolución: el modelo convertía la guarda de venecitas en formas parecidas a letras
- `placard-02` — baja calidad de origen
- `cocina-07` — sin super-resolución: guarda de venecitas; original muy chico (581 px)
- `oficina-06` — baja calidad de origen
- `cocina-03` — baja calidad de origen
- `cocina-04` — sin super-resolución: el modelo deformaba la guarda de venecitas
- `comercial-04` — nocturna con dominante verde fuerte, borrosa y con objetos ajenos (silla, balde): no se salva, pedir foto nueva
- `cocina-06` — baja calidad de origen
- `comercial-06` — piso quemado a blanco en el original: no se recupera
- `comercial-05` — obra sin terminar, muy comprimida
