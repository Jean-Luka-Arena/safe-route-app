// Estado en memoria: ubicaciones cargadas desde la API, indexadas por id,
// y las capas de Leaflet que hay que ir reemplazando en cada cálculo.
let ubicacionesPorId = {};
let marcadores = [];
let lineaRuta = null;

// Cache simple de direcciones ya resueltas, para no volver a pedirlas
// si se recarga la lista de ubicaciones en la misma sesión.
const cacheDirecciones = {};

const mapa = L.map("mapa").setView([-34.615, -58.38], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  maxZoom: 19,
}).addTo(mapa);

const selectOrigen = document.getElementById("origen");
const selectDestino = document.getElementById("destino");
const selectCriterio = document.getElementById("criterio");
const divPesos = document.getElementById("pesos");
const inputAlpha = document.getElementById("alpha");
const inputBeta = document.getElementById("beta");
const botonCalcular = document.getElementById("calcular");
const divResultado = document.getElementById("resultado");
const divError = document.getElementById("error");

selectCriterio.addEventListener("change", () => {
  divPesos.hidden = selectCriterio.value !== "balanceada";
});

/**
 * Le pregunta a Nominatim (geocodificación inversa de OpenStreetMap) qué
 * dirección hay en una lat/long. Devuelve null si falla o no encuentra
 * nada legible, para que quien la llama pueda mostrar un texto de
 * respaldo (ej: "Ubicación 3") en vez de romper la página.
 */
async function obtenerDireccion(latitud, longitud) {
  const clave = `${latitud},${longitud}`;
  if (cacheDirecciones[clave]) {
    return cacheDirecciones[clave];
  }

  try {
    const url =
      `https://nominatim.openstreetmap.org/reverse?format=json` +
      `&lat=${latitud}&lon=${longitud}&zoom=17&addressdetails=1`;
    const respuesta = await fetch(url);
    if (!respuesta.ok) return null;

    const datos = await respuesta.json();
    const direccion = formatearDireccion(datos);
    if (direccion) {
      cacheDirecciones[clave] = direccion;
    }
    return direccion;
  } catch (error) {
    return null;
  }
}

function formatearDireccion(datos) {
  const direccion = datos && datos.address;
  if (!direccion) return null;

  const calle = direccion.road;
  if (calle) {
    return direccion.house_number ? `${calle} ${direccion.house_number}` : calle;
  }

  // sin nombre de calle (ej: en medio de una plaza o un parque),
  // usamos el primer tramo del nombre completo que arma Nominatim.
  return datos.display_name ? datos.display_name.split(",")[0] : null;
}

/**
 * Va pidiendo, de a una y con una pausa entre cada pedido, la dirección
 * real de cada ubicación, y actualiza su marcador y sus <option> a
 * medida que van llegando las respuestas.
 *
 * La pausa de ~1.1s respeta la política de uso de Nominatim (máximo
 * 1 pedido por segundo en el servidor público gratuito).
 */
async function cargarDirecciones(ubicaciones) {
  for (const ubicacion of ubicaciones) {
    const direccion = await obtenerDireccion(
      ubicacion.latitud,
      ubicacion.longitud
    );
    const texto = direccion || `Ubicación ${ubicacion.id}`;

    ubicacion.marcador.setPopupContent(texto);
    document
      .querySelectorAll(`option[value="${ubicacion.id}"]`)
      .forEach((opcion) => {
        opcion.textContent = texto;
      });

    await new Promise((resolve) => setTimeout(resolve, 1100));
  }
}

async function cargarUbicaciones() {
  const respuesta = await fetch(`${API_BASE_URL}/locations`);
  const ubicaciones = await respuesta.json();

  ubicacionesPorId = {};
  selectOrigen.innerHTML = "";
  selectDestino.innerHTML = "";

  for (const ubicacion of ubicaciones) {
    const textoProvisorio = `Ubicación ${ubicacion.id} (buscando dirección…)`;

    const marcador = L.marker([ubicacion.latitud, ubicacion.longitud])
      .addTo(mapa)
      .bindPopup(textoProvisorio);
    marcadores.push(marcador);

    ubicacion.marcador = marcador;
    ubicacionesPorId[ubicacion.id] = ubicacion;

    for (const select of [selectOrigen, selectDestino]) {
      const opcion = document.createElement("option");
      opcion.value = ubicacion.id;
      opcion.textContent = textoProvisorio;
      select.appendChild(opcion);
    }
  }

  // por defecto, que origen y destino no arranquen iguales
  if (selectDestino.options.length > 1) {
    selectDestino.selectedIndex = 1;
  }

  if (ubicaciones.length > 0) {
    const grupo = L.featureGroup(marcadores);
    mapa.fitBounds(grupo.getBounds(), { padding: [30, 30] });
  }

  // no bloqueamos la carga de la página esperando las direcciones:
  // se van completando solas en segundo plano.
  cargarDirecciones(ubicaciones);
}

function limpiarResultadoAnterior() {
  divError.textContent = "";
  divResultado.textContent = "";
  if (lineaRuta) {
    mapa.removeLayer(lineaRuta);
    lineaRuta = null;
  }
}

// Servidor público de demo de OSRM (Open Source Routing Machine), perfil
// peatonal. Se usa SOLO para la parte visual: qué calles dibujar entre dos
// puntos consecutivos de la ruta. La ruta en sí (qué secuencia de
// ubicaciones conviene tomar) la sigue decidiendo nuestro propio Dijkstra,
// con sus propios criterios de distancia/seguridad.
const OSRM_BASE_URL = "https://routing.openstreetmap.de/routed-foot/route/v1/foot";

/**
 * Le pide a OSRM la geometría real (por calles) entre dos ubicaciones.
 * Devuelve un array de puntos [lat, lon] listos para Leaflet, o null si
 * el servicio falla, para que quien la llama pueda usar una línea recta
 * como respaldo en vez de romper el dibujo de la ruta.
 */
async function obtenerTramoPorCalles(origen, destino) {
  try {
    const url =
      `${OSRM_BASE_URL}/${origen.longitud},${origen.latitud};` +
      `${destino.longitud},${destino.latitud}?overview=full&geometries=geojson`;
    const respuesta = await fetch(url);
    if (!respuesta.ok) return null;

    const datos = await respuesta.json();
    if (!datos.routes || datos.routes.length === 0) return null;

    // GeoJSON trae las coordenadas como [lon, lat]; Leaflet las espera
    // como [lat, lon].
    return datos.routes[0].geometry.coordinates.map(([lon, lat]) => [
      lat,
      lon,
    ]);
  } catch (error) {
    return null;
  }
}

async function dibujarRuta(idsDeLaRuta) {
  let puntos = [];

  for (let i = 0; i < idsDeLaRuta.length - 1; i++) {
    const origen = ubicacionesPorId[idsDeLaRuta[i]];
    const destino = ubicacionesPorId[idsDeLaRuta[i + 1]];

    const tramoPorCalles = await obtenerTramoPorCalles(origen, destino);
    const tramo = tramoPorCalles || [
      [origen.latitud, origen.longitud],
      [destino.latitud, destino.longitud],
    ];

    // el último punto de un tramo es el primero del siguiente: evitamos
    // duplicarlo para que la línea no tenga un "salto" ahí.
    if (puntos.length > 0) {
      puntos.pop();
    }
    puntos = puntos.concat(tramo);
  }

  lineaRuta = L.polyline(puntos, { color: "#16324f", weight: 5 }).addTo(mapa);
  mapa.fitBounds(lineaRuta.getBounds(), { padding: [40, 40] });
}

function nombreLegible(id) {
  const ubicacion = ubicacionesPorId[id];
  const marcador = ubicacion && ubicacion.marcador;
  if (marcador) {
    const contenidoPopup = marcador.getPopup().getContent();
    if (contenidoPopup && !contenidoPopup.includes("buscando dirección")) {
      return contenidoPopup;
    }
  }
  return `Ubicación ${id}`;
}

function mostrarResultado(resultado) {
  const ruta = resultado.ruta.map(nombreLegible).join(" → ");
  divResultado.innerHTML = `
    <strong>Ruta:</strong> ${ruta}<br>
    <strong>Distancia total:</strong> ${resultado.distancia_total} m<br>
    <strong>Seguridad promedio:</strong> ${resultado.seguridad_promedio}/10<br>
    <strong>Costo total:</strong> ${resultado.costo_total.toFixed(2)}
  `;
}

async function calcularRuta() {
  limpiarResultadoAnterior();

  const origin = selectOrigen.value;
  const destination = selectDestino.value;
  const criteria = selectCriterio.value;

  if (!origin || !destination) {
    divError.textContent = "Elegí un origen y un destino.";
    return;
  }

  const parametros = new URLSearchParams({ origin, destination, criteria });

  if (criteria === "balanceada") {
    parametros.set("alpha", inputAlpha.value);
    parametros.set("beta", inputBeta.value);
  }

  try {
    const respuesta = await fetch(`${API_BASE_URL}/route?${parametros}`);
    const datos = await respuesta.json();

    if (!respuesta.ok) {
      divError.textContent = datos.detail || "No se pudo calcular la ruta.";
      return;
    }

    await dibujarRuta(datos.ruta);
    mostrarResultado(datos);
  } catch (error) {
    divError.textContent =
      "No se pudo conectar con la API. ¿Está corriendo el backend?";
  }
}

botonCalcular.addEventListener("click", calcularRuta);

cargarUbicaciones().catch(() => {
  divError.textContent =
    "No se pudieron cargar las ubicaciones. ¿Está corriendo el backend?";
});