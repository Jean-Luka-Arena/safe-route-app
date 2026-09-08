let ubicacionesPorId = {};
let seleccionOrigen = null;
let seleccionDestino = null;
let marcadorOrigen = null;
let marcadorDestino = null;
let lineaRuta = null;

const cacheDirecciones = {};

const mapa = L.map("mapa").setView([-34.525, -58.4775], 14);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  maxZoom: 19,
}).addTo(mapa);

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

function distanciaEnMetros(lat1, lon1, lat2, lon2) {
  const radioTierra = 6371000;
  const aRad = (grados) => (grados * Math.PI) / 180;
  const dLat = aRad(lat2 - lat1);
  const dLon = aRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(aRad(lat1)) * Math.cos(aRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * radioTierra * Math.asin(Math.sqrt(a));
}

function ubicacionMasCercana(lat, lon) {
  let mejor = null;
  let mejorDistancia = Infinity;

  for (const id in ubicacionesPorId) {
    const candidata = ubicacionesPorId[id];
    const distancia = distanciaEnMetros(
      lat,
      lon,
      candidata.latitud,
      candidata.longitud
    );
    if (distancia < mejorDistancia) {
      mejorDistancia = distancia;
      mejor = candidata;
    }
  }

  return mejor;
}

async function obtenerDireccion(latitud, longitud) {
  const clave = `${latitud},${longitud}`;
  if (cacheDirecciones[clave]) return cacheDirecciones[clave];

  try {
    const url =
      `https://nominatim.openstreetmap.org/reverse?format=json` +
      `&lat=${latitud}&lon=${longitud}&zoom=17&addressdetails=1`;
    const respuesta = await fetch(url);
    if (!respuesta.ok) return null;

    const datos = await respuesta.json();
    const direccion = formatearDireccion(datos);
    if (direccion) cacheDirecciones[clave] = direccion;
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
  return datos.display_name ? datos.display_name.split(",")[0] : null;
}

async function buscarDirecciones(texto) {
  if (texto.trim().length < 3) return [];

  const viewbox = `${ZONA.oeste},${ZONA.norte},${ZONA.este},${ZONA.sur}`;
  const params = new URLSearchParams({
    format: "json",
    q: texto,
    viewbox,
    bounded: "1",
    limit: "5",
  });

  try {
    const respuesta = await fetch(
      `https://nominatim.openstreetmap.org/search?${params}`
    );
    if (!respuesta.ok) return [];
    return await respuesta.json();
  } catch (error) {
    return [];
  }
}

function ubicarMarcadorSeleccion(marcadorActual, ubicacion, etiqueta, color) {
  if (marcadorActual) {
    mapa.removeLayer(marcadorActual);
  }
  const marcador = L.circleMarker([ubicacion.latitud, ubicacion.longitud], {
    radius: 9,
    color,
    fillColor: color,
    fillOpacity: 0.9,
  })
    .addTo(mapa)
    .bindPopup(etiqueta)
    .openPopup();

  return marcador;
}

function configurarBuscador(inputId, sugerenciasId, alElegir) {
  const input = document.getElementById(inputId);
  const listaSugerencias = document.getElementById(sugerenciasId);
  let temporizador = null;

  input.addEventListener("input", () => {
    clearTimeout(temporizador);
    const texto = input.value;

    temporizador = setTimeout(async () => {
      const resultados = await buscarDirecciones(texto);
      renderizarSugerencias(resultados);
    }, 600);
  });

  document.addEventListener("click", (evento) => {
    if (evento.target !== input) {
      listaSugerencias.hidden = true;
    }
  });

  function renderizarSugerencias(resultados) {
    listaSugerencias.innerHTML = "";

    if (resultados.length === 0) {
      listaSugerencias.hidden = true;
      return;
    }

    for (const resultado of resultados) {
      const item = document.createElement("div");
      item.className = "sugerencia";
      item.textContent = resultado.display_name;

      item.addEventListener("click", () => {
        const lat = parseFloat(resultado.lat);
        const lon = parseFloat(resultado.lon);
        const cercana = ubicacionMasCercana(lat, lon);

        input.value = resultado.display_name.split(",").slice(0, 2).join(",");
        listaSugerencias.hidden = true;
        listaSugerencias.innerHTML = "";

        alElegir(cercana);
      });

      listaSugerencias.appendChild(item);
    }

    listaSugerencias.hidden = false;
  }
}

configurarBuscador("origen-input", "origen-sugerencias", (cercana) => {
  seleccionOrigen = cercana;
  marcadorOrigen = ubicarMarcadorSeleccion(
    marcadorOrigen,
    cercana,
    "Origen",
    "#1a7d3c"
  );
  mapa.panTo([cercana.latitud, cercana.longitud]);
});

configurarBuscador("destino-input", "destino-sugerencias", (cercana) => {
  seleccionDestino = cercana;
  marcadorDestino = ubicarMarcadorSeleccion(
    marcadorDestino,
    cercana,
    "Destino",
    "#a12727"
  );
  mapa.panTo([cercana.latitud, cercana.longitud]);
});

async function cargarUbicaciones() {
  const respuesta = await fetch(`${API_BASE_URL}/locations`);
  const ubicaciones = await respuesta.json();

  ubicacionesPorId = {};
  for (const ubicacion of ubicaciones) {
    ubicacionesPorId[ubicacion.id] = ubicacion;
  }
}

function limpiarResultadoAnterior() {
  divError.textContent = "";
  divResultado.textContent = "";
  if (lineaRuta) {
    mapa.removeLayer(lineaRuta);
    lineaRuta = null;
  }
}

const OSRM_BASE_URL = "https://routing.openstreetmap.de/routed-foot/route/v1/foot";

async function obtenerRutaPorCalles(idsDeLaRuta) {
  try {
    const coordenadas = idsDeLaRuta
      .map((id) => {
        const u = ubicacionesPorId[id];
        return `${u.longitud},${u.latitud}`;
      })
      .join(";");

    const url = `${OSRM_BASE_URL}/${coordenadas}?overview=full&geometries=geojson`;
    const respuesta = await fetch(url);
    if (!respuesta.ok) return null;

    const datos = await respuesta.json();
    if (!datos.routes || datos.routes.length === 0) return null;

    return datos.routes[0].geometry.coordinates.map(([lon, lat]) => [
      lat,
      lon,
    ]);
  } catch (error) {
    return null;
  }
}

async function dibujarRuta(idsDeLaRuta) {
  const puntosPorCalles = await obtenerRutaPorCalles(idsDeLaRuta);

  const puntos =
    puntosPorCalles ||
    idsDeLaRuta.map((id) => {
      const u = ubicacionesPorId[id];
      return [u.latitud, u.longitud];
    });

  lineaRuta = L.polyline(puntos, { color: "#16324f", weight: 5 }).addTo(mapa);
  mapa.fitBounds(lineaRuta.getBounds(), { padding: [40, 40] });
}

function nombreLegible(id) {
  const ubicacion = ubicacionesPorId[id];
  if (!ubicacion) return `Ubicación ${id}`;

  const clave = `${ubicacion.latitud},${ubicacion.longitud}`;
  return cacheDirecciones[clave] || `Ubicación ${id}`;
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

  if (!seleccionOrigen || !seleccionDestino) {
    divError.textContent =
      "Buscá y elegí un origen y un destino de la lista de sugerencias.";
    return;
  }

  const origin = seleccionOrigen.id;
  const destination = seleccionDestino.id;
  const criteria = selectCriterio.value;

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