# Diseño de Sistema — Estilo Visual y Componentes UI

> Describe el sistema de diseño (design system) de activia-trace: paleta de colores, tipografía, layout, componentes y patrones de interfaz. Refleja el documento original `docs/DESIGN.md` como parte integral de la base de conocimiento del producto.

---

## Personalidad de Marca

El sistema de diseño está construido para la administración académica de alto nivel y la gestión académica. La personalidad de marca es **autoritativa pero accesible**, reflejando la confianza tranquila de una institución prestigiosa. Prioriza la claridad y el enfoque, eliminando distracciones ornamentales para centrar la atención del usuario en los datos y la investigación.

El estilo es una combinación de **Minimalismo** y **Corporativo Moderno**, utilizando abundante espacio en blanco para crear una sensación de "respiro intelectual". La estética es "Nuevo Académico": respeta los valores académicos tradicionales a través de la tipografía refinada mientras abraza la eficiencia moderna a través de una interfaz estructurada y utilitaria. La respuesta emocional buscada es calma, control y confiabilidad profesional.

---

## Colores

La paleta es estrictamente profesional, apoyándose en una gama sofisticada de grises fríos y azules profundos para establecer jerarquía sin necesidad de vibrance.

| Token | Color | Hex | Uso |
|-------|-------|-----|-----|
| `primary` | Navy | `#0F172A` | Navegación principal, encabezados de alto nivel, elementos de marca |
| `secondary` | Charcoal | `#334155` | Texto corporal y estados interactivos secundarios |
| `tertiary` | Slate Gray | `#64748B` | Información desenfatizada, subtítulos, bordes decorativos |
| `background` | Off-white | `#F8FAFC` | Fondo principal (reduce fatiga visual) |
| `surface` | White | `#FFFFFF` | Tarjetas, contenedores elevados |
| `error` | Red | `#BA1A1A` | Estados de error, validación |

**Regla**: Evitar cualquier uso de acentos de alta saturación. Los colores funcionales (success, error) deben ser apagados e integrados en este espectro de tonos fríos.

### Superficies y Elevación

| Token | Color | Uso |
|-------|-------|-----|
| `surface-dim` | `#D8DADC` | Superficies secundarias |
| `surface-bright` | `#F7F9FB` | Superficies brillantes |
| `surface-container` | `#ECEEF0` | Contenedores elevados |
| `surface-container-high` | `#E6E8EA` | Contenedores con más énfasis |
| `surface-container-highest` | `#E0E3E5` | Contenedores con máximo énfasis |

---

## Tipografía

Estrategia: **"Serif para Pensar, Sans para Actuar"**.

| Estilo | Fuente | Tamaño | Peso | Line-Height | Letter-Spacing | Uso |
|--------|--------|--------|------|-------------|----------------|-----|
| `headline-lg` | Source Serif 4 | 40px | 600 | 48px | -0.02em | Encabezados de página (desktop) |
| `headline-lg-mobile` | Source Serif 4 | 30px | 600 | 36px | -0.01em | Encabezados de página (mobile) |
| `headline-md` | Source Serif 4 | 28px | 500 | 36px | — | Encabezados de sección |
| `headline-sm` | Source Serif 4 | 20px | 500 | 28px | — | Encabezados de tarjeta |
| `body-lg` | Inter | 18px | 400 | 28px | — | Texto destacado |
| `body-md` | Inter | 16px | 400 | 24px | — | Texto corporal por defecto |
| `body-sm` | Inter | 14px | 400 | 20px | — | Texto secundario, metadatos |
| `label-md` | Inter | 14px | 600 | 16px | 0.02em | Etiquetas de formulario, breadcrumbs |
| `label-sm` | Inter | 12px | 500 | 16px | 0.04em | Categorías, badges, caps |

**Source Serif 4** se usa para todos los titulares y contenido editorial. Sus raíces académicas proveen una sensación inmediata de autoridad y tradición.

**Inter** se usa para todos los elementos funcionales de UI, tablas de datos y texto corporal. Su alto x-height y tono neutral aseguran que los datos académicos densos sigan siendo legibles y escaneables.

La alineación del texto debe ser generalmente a la izquierda para mantener un eje vertical fuerte. Para vistas con muchos datos, usar el estilo `label-sm` en mayúsculas para diferenciar categorías del contenido.

---

## Layout y Espaciado

### Grid
- **Desktop**: Grid fijo de 12 columnas, con preferencia por márgenes amplios (64px)
- **Tablet**: Márgenes de 32px
- **Mobile**: Márgenes de 16px
- **Gutter**: 24px
- **Ancho máximo de contenedor**: 1280px

### Ritmo vertical
- Baseline estricto de 4px
- Separación entre secciones: 48px o 64px para distinguir claramente entre módulos de información

### Filosofía
El contenido debe estar a menudo centrado con "espacio muerto" significativo en la periferia para minimizar la carga cognitiva.

---

## Elevación y Profundidad

La jerarquía se logra a través de **Capas Tonales** y **Sombras Ambientales** muy sutiles. Se evitan sombras pesadas, usando cambios de valor sútiles para indicar elevación.

| Capa | Fondo | Borde | Sombra |
|------|-------|-------|--------|
| Base | Off-white (#F8FAFC) | Ninguno | Ninguna |
| Card | White (#FFFFFF) | 1px #E2E8F0 | `0px 4px 20px rgba(15, 23, 42, 0.04)` |
| Active | White (#FFFFFF) | 1px Primary Navy | `0px 8px 30px rgba(15, 23, 42, 0.08)` |

**Regla**: No apilar más de dos capas de profundidad para mantener la estética minimalista.

---

## Formas (Border Radius)

| Token | Valor | Uso |
|-------|-------|-----|
| `rounded-sm` | 0.125rem (2px) | Casos mínimos |
| `rounded` | 0.25rem (4px) | Botones, inputs (por defecto) |
| `rounded-md` | 0.375rem (6px) | — |
| `rounded-lg` | 0.5rem (8px) | Tarjetas, contenedores grandes |
| `rounded-xl` | 0.75rem (12px) | — |
| `rounded-full` | 9999px | — |

Un redondeo **Soft (0.25rem)** se aplica a botones estándar y campos de entrada para evitar que la UI se sienta demasiado agresiva o "afilada", manteniendo una silueta profesional y cuadrada.

Las tarjetas y contenedores más grandes usan `rounded-lg` (0.5rem) para proporcionar una distinción suave del fondo.

**Regla**: Evitar formas "pill" o curvas de alto radio, ya que restan seriedad a la naturaleza académica de la aplicación.

---

## Componentes

### Botones
- **Primario**: Fondo sólido Navy (`#0F172A`), texto blanco. Padding generoso (`px-6 py-3` = 12px 24px). Border-radius `rounded`.
- **Secundario**: Contorno Slate Gray sin relleno. Hover con fondo sutil.
- **Ghost**: Sin borde ni fondo, cambia a hover sutil.
- **Variants de tamaño**: `sm` (px-4 py-2), `md` (px-6 py-3), `lg` (px-8 py-4).
- **Estados**: `isLoading` muestra spinner y deshabilita el botón.

### Tarjetas (Cards)
- Fondo blanco, borde muy sutil (1px #E2E8F0), sombra `card` difusa.
- Headers opcionales con separador inferior usando 10% de opacidad.
- Footers opcionales con separador superior.
- Padding interno: `p-6`.

### Tablas de Datos
- Sin bordes verticales.
- Divisores horizontales de 1px Slate Gray al 10% de opacidad.
- Altura de fila generosa: 56px (`py-4`).
- Cabeceras con opción de ordenamiento (sort).
- Estados: carga (skeleton rows), vacío (mensaje centrado), con datos.
- Responsive: scroll horizontal en mobile.

### Campos de Entrada (Inputs)
- Etiqueta (`label-md`) siempre arriba del campo.
- Borde de 4 lados: `1px solid` con opacidad 30%.
- Foco: anillo `2px` Primary Navy.
- Estado de error: borde rojo, mensaje de error debajo.

### Navegación Lateral (Sidebar)
- Fondo Primary Navy (`#0F172A`).
- Texto inactivo: Slate Gray (`tertiary`).
- Estado activo: indicador de 2px left-bar blanco + fondo sutil.
- Encabezados de sección: `label-sm` en mayúsculas con opacidad 60%.
- Título de marca: `headline-sm` en fuente serif.

### Chips
- Rectangulares con redondeo mínimo.
- Fondo de bajo contraste (`#F1F5F9` o `bg-tertiary/10`).
- Sin forma pill.
- Opcional: botón de cierre (X) para removibles.

### Badges
- Indicadores de estado con 5 variantes: success (verde), warning (amarillo), error (rojo), info (azul), neutral (slate).
- Pequeño punto indicador circular + texto descriptivo.
- Tamaño compacto: `text-label-sm`, `px-2 py-0.5`.

### Modales
- Cabecera con `headline-sm` en fuente serif.
- Fondo blanco con tarjeta (border, shadow).
- Overlay semitransparente (`bg-black/40`).

---

## Implementación Técnica

El sistema de diseño se implementa vía **Tailwind CSS v3** con los tokens definidos en `theme.extend` del archivo `frontend/tailwind.config.ts`.

Los tokens nombrados permiten usar clases como:
- `bg-primary`, `text-secondary`, `border-tertiary/20`
- `font-serif` (Source Serif 4), `font-sans` (Inter)
- `text-headline-lg`, `text-body-md`, `text-label-sm`
- `shadow-card`, `shadow-card-active`
- `rounded`, `rounded-lg`

### Archivos involucrados
- `frontend/tailwind.config.ts` — definición de tokens de diseño
- `frontend/src/index.css` — imports de Google Fonts + estilos base
- `frontend/index.html` — preconnect de Google Fonts
- `frontend/src/shared/components/` — componentes compartidos (Button, Card, DataTable, Input, Chip, Badge)

---

## Referencias

- `docs/DESIGN.md` — documento original del sistema de diseño (precursor de este archivo)
- `docs/ARQUITECTURA.md` — decisiones técnicas de implementación
- `frontend/tailwind.config.ts` — definición concreta de tokens de diseño
- `frontend/src/shared/components/` — catálogo de componentes de UI
