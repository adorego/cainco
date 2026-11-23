# Pendientes de Cainco

Lo que falta que Cainco confirme o envíe para terminar el sitio. Cada punto tiene un `TODO_CAINCO` en `index.html`; con `grep -n TODO_CAINCO index.html` se ven todos.

## Fotos a pedir

Conviene pedir los **originales sin comprimir**, enviados por WhatsApp como *Documento* (no como foto) o por Google Drive, o una **foto nueva** cuando el original no alcanza. El detalle técnico de cada foto está en `tools/reporte-fotos.md`.

### Foto nueva (no se puede usar la actual)

- [ ] `comercial-04` — **mesa exhibidora y atril**. Se descartó: es nocturna, con dominante verde fuerte, está borrada y tiene objetos ajenos (una silla y un balde). Está **fuera de la galería** y comentada en `index.html` con `TODO_CAINCO`. Cuando llegue la foto nueva:
  1. Sacar `"decision": "descartar"` de `tools/fotos-ajustes.json`.
  2. Correr `bash tools/hd.sh --ids comercial-04`.
  3. Descomentar su línea en la galería.
- [ ] `comercial-05` — la obra está sin terminar y la foto muy comprimida.
- [ ] `comercial-06` — el piso salió quemado a blanco y no se recupera.

### Original sin comprimir (calidad de origen baja)

- [ ] `cocina-03`
- [ ] `cocina-04` — la guarda de venecitas no admite super-resolución.
- [ ] `cocina-05` — la guarda de venecitas no admite super-resolución.
- [ ] `cocina-06`
- [ ] `cocina-07` — el original mide solo 581 px de ancho.
- [ ] `placard-02`
- [ ] `placard-05`
- [ ] `oficina-06`
- [ ] `oficina-03` — blanda, sacada a través de un vidrio.

### Se usan, pero convendría repetirlas

- [ ] `placard-04` — tiene cables sueltos cruzando el frente.
- [ ] `locker-02` — tiene una silla en primer plano.

**Para las fotos nuevas:**
- Luz de día, con las lámparas apagadas.
- Celular a la altura del pecho y derecho, sin inclinar.
- Ambiente ordenado.
- Una toma general y algunos detalles de herrajes y terminaciones.

## Ya confirmado (en `CAINCO_CONFIG`, estado "confirmado")

- WhatsApp y teléfono: 0984 301 230. Los enlaces usan `wa.me/595984301230` y `tel:+595984301230`.
- Dirección: Av. Sacramento 2844 esq. Espíritu Santo, Asunción. Está en el footer, en el JSON-LD y en el enlace «Cómo llegar».
- Trayectoria: +20 años. No se usa `foundingDate` porque falta el año exacto.

## Datos a confirmar

- **Email:** ¿la dirección es `info@cainco.com.py`? ¿Ya funciona? El dominio todavía no resuelve. Mientras no se confirme, está en estado "propuesto" y no se muestra ni va al JSON-LD.
- **Año de fundación** (opcional): si nos lo pasan, se agrega `foundingDate` al JSON-LD.
- **Redes:** URLs de Instagram, Facebook y LinkedIn (`sameAs` y footer), y el usuario de X.
- **Medición:** ID de GA4 e ID de Meta Pixel.
- **Promesas comerciales:**
  - Presupuesto sin cargo y tiempo real de respuesta.
  - Instalación incluida.
  - Plazo de entrega por escrito o por contrato.
  - Responsable de proyecto único y postventa: qué cubre y por cuánto tiempo.
  - Factura legal.
- **Proceso:**
  - Tiempo de respuesta.
  - Duración y costo de la visita.
  - Días hasta el presupuesto.
  - ¿Entregan plano o render 3D?
  - Plazo típico de una cocina.
- **Prueba social:**
  - Cifras reales: proyectos entregados y empresas clientes.
  - 3 testimonios reales, con permiso.
  - Datos de los 2 casos destacados (lockers y local comercial).
- **Preguntas frecuentes:** zonas de trabajo, formas de pago, garantía, factura y plazo típico.
- **Formulario:** los rangos de inversión en guaraníes.
- **Galería:**
  - Material del listonado (`oficina-03`).
  - Terminación (`comercial-01`).
  - Tipo de puertas (`placard-04`).
  - ¿OSB o melamina símil OSB? (`locker-02`).

Para ver el estado actualizado: `bash tools/check-publicacion.sh`.

## Mensaje de WhatsApp para el cliente

> Hola! Ya tenemos casi lista la web nueva de Cainco 🙌 Ya cargamos el WhatsApp, el teléfono, la dirección de Av. Sacramento y los +20 años. Para terminar nos faltan algunas cosas:
>
> *1. Email:* ¿el correo es info@cainco.com.py? ¿Ya funciona? Hasta que nos confirmen no lo publicamos.
>
> *2. Fotos:* necesitamos las fotos originales, sin pasar por WhatsApp porque las comprime. Mandalas como *Documento* (clip → Documento) o subilas a una carpeta de Google Drive. Las que más necesitamos:
> • Cocinas: las 5 de cocinas con bajo mesada y granito (cocina-03 a 07)
> • Placares: el pasillo vestidor y el vestidor esquinero (placard-02 y 05)
> • Oficina: el archivo bajo con puertas corredizas y la recepción listonada
> • Locales: la mesa exhibidora con atril (esa hay que sacarla de nuevo) y el mueble de pared con nichos gris grafito
>
> Si hay que sacar fotos nuevas: con luz de día y las lámparas apagadas, el celular a la altura del pecho y derecho, el lugar ordenado. Una foto general y algunas de detalle de herrajes y terminaciones.
>
> *3. Datos para la web* (con lo que sepan alcanza, el resto lo completamos después):
> • ¿El presupuesto y la visita de medición son sin cargo? ¿En cuánto tiempo responden?
> • ¿La instalación está incluida? ¿El plazo de entrega va por escrito o por contrato?
> • Garantía y postventa: qué cubre y por cuánto tiempo. ¿Emiten factura legal?
> • Formas de pago y zonas donde trabajan (¿viajan al interior?)
> • Plazo típico de una cocina y cuántos días tarda el presupuesto
> • Links de Instagram, Facebook y LinkedIn
> • 2 o 3 clientes contentos que nos dejen usar una frase con su nombre
> • ¿Cuántos proyectos entregaron aprox.? ¿Para cuántas empresas trabajaron?
>
> ¡Gracias!
