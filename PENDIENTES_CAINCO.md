# Pendientes de Cainco

Lo que falta que Cainco confirme o nos envíe para publicar el sitio. Los datos viven en `CAINCO_CONFIG` (dentro de `index.html`), cada uno con un estado:

- **confirmado:** se publica tal cual.
- **propuesto:** lo redactamos nosotros y ya se ve en la página, pero el sitio no se publica hasta que Cainco lo confirme.
- **falta:** es un dato real que todavía no tenemos. Lo que depende de él está oculto y no se inventa nada.

Para ver el estado del sitio: `bash tools/check-publicacion.sh`. Para que Cainco revise en pantalla los textos propuestos: abrir la página con `?revision=1`. Así cada texto propuesto aparece subrayado y muestra la clave al tocarlo.

## Ya confirmado

- **WhatsApp y teléfono:** 0984 301 230, con `wa.me/595984301230` y `tel:+595984301230`.
- **Dirección:** Av. Sacramento 2844 esq. Espíritu Santo, Asunción. Aparece en el footer, en el JSON-LD y en el enlace «Cómo llegar».
- **Trayectoria:** +20 años. No va `foundingDate` porque falta el año exacto. Si nos lo pasan, se agrega.

## Para confirmar (sí / no)

Cada propuesta ya está escrita en la web. Alcanza con un «sí» o con la corrección.

1. **respuesta:** «Te respondemos dentro de las 24 h hábiles». ¿Sí?
2. **horario:** «Lunes a viernes de 8:00 a 17:00 · Sábados de 8:00 a 12:00». ¿Sí?
3. **cobertura:** «Asunción y Gran Asunción (Central). Otras zonas, a consultar». ¿Sí?
4. **medicion:** «Visita de medición sin cargo en Asunción y Gran Asunción». ¿Sí? Por eso los botones dicen «Pedir presupuesto sin cargo».
5. **presupuesto_plazo:** «Presupuesto en 3 a 5 días hábiles después de la medición». ¿Sí?
6. **diseno_previo:** «Te mostramos un plano o render del mueble para aprobar antes de fabricar». ¿Sí?
7. **fabricacion_plazo:** «Entre 20 y 30 días hábiles desde la aprobación y la seña, según el proyecto». ¿Sí?
8. **pagos:** «50% de seña y 50% contra entrega. Transferencia, efectivo o QR». ¿Sí?
9. **factura:** «Emitimos factura legal». ¿Sí?
10. **garantia:** «1 año de garantía en fabricación y herrajes». ¿Sí?
11. **postventa:** «Si algo necesita ajuste después de la instalación, volvemos a revisarlo». ¿Sí?
12. **instalacion:** «Instalación incluida en Asunción y Gran Asunción». ¿Sí?
13. **arquitectos:** «Trabajamos con planos de tu arquitecto o interiorista». ¿Sí?
14. **rangos_inversion** (opciones del formulario): «Hasta Gs. 5 millones / Gs. 5 a 15 millones / Gs. 15 a 40 millones / Más de Gs. 40 millones / Prefiero no decir». ¿Sí?

## Para enviarnos

Mientras estos datos falten, lo que depende de ellos queda oculto en la web.

- **Email:** proponemos `info@cainco.com.py`. Hay que confirmar la dirección exacta y que el correo funcione, porque hoy el dominio no resuelve. Hasta entonces no aparece en el código publicado.
- **Testimonios:** 2 o 3 clientes reales, con permiso, con una frase, el nombre (y la empresa, si corresponde) y el tipo de proyecto. Mientras falten, la sección «Clientes» completa está oculta.
- **Cifras** (solo si las quieren mostrar): cantidad de proyectos entregados y de empresas clientes. Mientras falten, en Empresas se ve solo «+20 años».
- **Redes:** links de Instagram, Facebook y LinkedIn, y de X si tienen. Mientras falten, la columna «Redes» del footer está oculta.
- **Los 2 casos destacados:** para cada uno, fotos y una línea sobre el desafío (qué necesitaba el cliente) y la solución (qué se fabricó y en cuánto tiempo). Mientras falten, están ocultos.
  - **Lockers para una empresa:** fotos `taller-02` (durante) y `locker-01` (terminado). ¿Son del mismo proyecto? ¿Podemos nombrar al cliente o el rubro?
  - **Local comercial:** fotos `comercial-01` y `comercial-03`. ¿Son del mismo local? ¿Podemos nombrarlo?
- **Medición** (lo configuramos nosotros cuando esté la cuenta): ID de Google Analytics 4 e ID de Meta Pixel.

### Fotos a reemplazar (11), por prioridad

Lo ideal es el **original del celular, mandado por WhatsApp como *Documento*** (clip → Documento), para que no se comprima, o por Google Drive. Si hay que sacarla de nuevo:
- Con luz de día y las lámparas apagadas.
- Con el celular a la altura del pecho y derecho.
- Con el lugar ordenado.
- Una toma general y algunas de detalle de herrajes y terminaciones.

El detalle técnico de cada foto está en `tools/reporte-fotos.md`.

1. **Cocinas:**
   - `cocina-03`: con columna de horno y mesada oscura.
   - `cocina-04`: con isla y granito.
   - `cocina-05`: bajo mesada y alacena blanca.
   - `cocina-06`: bajo mesada con cajonera.
   - `cocina-07`: bajo mesada y alacena compacta.
   - En las cinco, la versión actual llegó muy comprimida. Las que tienen guarda de venecitas no se pueden mejorar más sin deformarla.
2. **Comerciales:**
   - `comercial-04`: mesa exhibidora y atril. **Hay que sacarla de nuevo**: es nocturna, está borrosa y tiene objetos ajenos. Hoy está fuera de la galería (comentada en `index.html`). Cuando llegue:
     1. Sacar `"decision": "descartar"` de `tools/fotos-ajustes.json`.
     2. Correr `bash tools/hd.sh --ids comercial-04`.
     3. Descomentar su línea.
   - `comercial-05`: mueble de pared con nichos gris grafito. La obra estaba sin terminar.
   - `comercial-06`: el mismo mueble de frente. El piso salió quemado a blanco.
3. **Placares y oficina:**
   - `placard-02`: pasillo vestidor.
   - `placard-05`: vestidor esquinero.
   - `oficina-06`: archivo bajo con puertas corredizas.

Opcional, si se puede repetir:
- `oficina-03`: recepción listonada; salió blanda, a través de un vidrio.
- `placard-04`: tiene cables cruzando el frente.
- `locker-02`: tiene una silla delante.

## Mensaje de WhatsApp para Cainco (versión corta)

> ¡Hola! 👋 La web nueva de Cainco ya está casi lista. Ya cargamos el WhatsApp, el teléfono, la dirección de Av. Sacramento y los +20 años.
>
> Para publicarla necesitamos que nos confirmes estas propuestas. Contestá con el número y *sí*, o con la corrección (ej.: «7: 30 a 45 días»):
>
> 1. Te respondemos dentro de las 24 h hábiles
> 2. Horario: lunes a viernes de 8 a 17 y sábados de 8 a 12
> 3. Zona: Asunción y Gran Asunción (Central). Otras zonas, a consultar
> 4. Visita de medición sin cargo en Asunción y Gran Asunción
> 5. Presupuesto en 3 a 5 días hábiles después de medir
> 6. Antes de fabricar mostramos un plano o render para aprobar
> 7. Fabricación: 20 a 30 días hábiles desde la aprobación y la seña
> 8. Pago: 50% de seña y 50% contra entrega. Transferencia, efectivo o QR
> 9. Emitimos factura legal
> 10. 1 año de garantía en fabricación y herrajes
> 11. Si algo necesita ajuste después de instalar, volvemos a revisarlo
> 12. Instalación incluida en Asunción y Gran Asunción
> 13. Trabajamos con planos de tu arquitecto o interiorista
> 14. Rangos de inversión del formulario: hasta Gs. 5 millones / 5 a 15 / 15 a 40 / más de 40 / prefiero no decir
>
> Y cuando puedas, mandanos:
>
> 15. *Email:* ¿es info@cainco.com.py? ¿Ya funciona? Hasta confirmarlo no lo publicamos
> 16. *Testimonios:* 2 o 3 clientes que nos dejen usar una frase con su nombre
> 17. *Cifras* (si las quieren mostrar): ¿cuántos proyectos entregados y cuántas empresas clientes, más o menos?
> 18. *Redes:* links de Instagram, Facebook y LinkedIn
> 19. *2 trabajos para destacar:* el muro de lockers y el local con las mesas exhibidoras. Una línea de cada uno: qué necesitaba el cliente y qué hicieron
> 20. *Fotos originales:* mandalas por acá como *Documento* (clip → Documento), así no se comprimen. Si las sacás de nuevo, con luz de día, el celular derecho y el lugar ordenado. Por orden de importancia:
>    • las 5 cocinas con mesada de granito
>    • la mesa exhibidora con atril (esa hay que sacarla de nuevo) y el mueble de pared gris grafito
>    • el pasillo vestidor, el vestidor esquinero y el archivo bajo con puertas corredizas
>
> ¡Gracias! 🙌
