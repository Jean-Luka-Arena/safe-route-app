// Estado en memoria: ubicaciones cargadas desde la API, indexadas por id,
// y las capas de Leaflet que hay que ir reemplazando en cada cálculo.
let ubicacionesPorId = {};
let marcadores = [];
let lineaRuta = null;

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

async function cargarUbicaciones() {
  const respuesta = await fetch(`${API_BASE_URL}/locations`);
  const ubicaciones = await respuesta.json();

  ubicacionesPorId = {};
  selectOrigen.innerHTML = "";
  selectDestino.innerHTML = "";

  for (const ubicacion of ubicaciones) {
    ubicacionesPorId[ubicacion.id] = ubicacion;

    const marcador = L.marker([ubicacion.latitud, ubicacion.longitud])
      .addTo(mapa)
      .bindPopup(`Ubicación ${ubicacion.id}`);
    marcadores.push(marcador);

    for (const select of [selectOrigen, selectDestino]) {
      const opcion = document.createElement("option");
      opcion.value = ubicacion.id;
      opcion.textContent = `Ubicación ${ubicacion.id}`;
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
}

function limpiarResultadoAnterior() {
  divError.textContent = "";
  divResultado.textContent = "";
  if (lineaRuta) {
    mapa.removeLayer(lineaRuta);
    lineaRuta = null;
  }
}

function dibujarRuta(idsDeLaRuta) {
  const puntos = idsDeLaRuta.map((id) => {
    const ubicacion = ubicacionesPorId[id];
    return [ubicacion.latitud, ubicacion.longitud];
  });

  lineaRuta = L.polyline(puntos, { color: "#16324f", weight: 5 }).addTo(mapa);
  mapa.fitBounds(lineaRuta.getBounds(), { padding: [40, 40] });
}

function mostrarResultado(resultado) {
  divResultado.innerHTML = `
    <strong>Ruta:</strong> ${resultado.ruta.join(" → ")}<br>
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

    dibujarRuta(datos.ruta);
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