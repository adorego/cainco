# Reporte de fotos — Cainco

Generado por `tools/mejorar_fotos.py`. Ordenado de mejor a peor según el diagnóstico del original.

**Super-resolución usada:** Real-ESRGAN x4plus / x2plus (PyTorch, CPU), mezclado 70/30 con bicúbica para conservar textura

- **Nitidez**: varianza del Laplaciano con la imagen normalizada a 1024 px (más alto = más nítida; <100 es blanda).
- **Q JPEG**: calidad estimada a partir de la tabla de cuantización.
- **Bloques**: salto de gradiente en bordes 8×8 vs. interior (1.0 = sin artefactos; >1.15 = bloques visibles).
- **Recomprimida**: resolución típica de WhatsApp (lado mayor ≤1280/1600) y/o Q ≤ 85.

| # | Foto | Original | KB | Q JPEG | Bloques | Nitidez orig → final | Recompr. | Puntaje | Recomendación | Final | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `placard-04` | 960×1280 | 100 | 78 | 1.26 | 211 → 362 | sí | 0.82 | **usar** | 1720×2381 | recorte abajo para sacar cables del piso; verticales inclinadas; rot -3.0°, verticales k=1.080 (acotada); WB 0.95/0.99/1.06, gamma 0.88 |
| 2 | `cocina-01` | 716×716 | 52 | 78 | 1.46 | 525 → 176 | sí | 0.73 | **usar** | 1611×1611 | sin líneas fiables; WB 0.99/1.00/1.01 |
| 3 | `comercial-01` | 963×1280 | 114 | 78 | 1.63 | 186 → 292 | sí | 0.73 | **usar** | 1926×2560 | nocturna con reflejos verdes de los vidrios; sin enderezar; WB 1.01/0.98/1.00, gamma 0.72 |
| 4 | `bano-01` | 1280×960 | 87 | 78 | 1.79 | 117 → 213 | sí | 0.62 | **mejorar** | 2560×1920 | sin líneas fiables; WB 0.99/1.00/1.01 |
| 5 | `cocina-06` | 1032×774 | 40 | 78 | 1.94 | 26 → 67 | sí | 0.22 | **pedir original** | 1902×1548 | rot +3.3°, verticales k=1.080 (acotada); WB 1.02/1.00/0.98 |

## Para pedir a Cainco

Fotos que conviene reemplazar (original sin comprimir o foto nueva):

- `cocina-06` — baja calidad de origen
