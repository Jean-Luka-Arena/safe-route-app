let ubicacionesPorId = {};
let conexionesPorId = {};
let seleccionOrigen = null;
let seleccionDestino = null;
let seleccionCalleIncidente = null;
let marcadorOrigen = null;
let marcadorDestino = null;
let lineaRuta = null;
let lineaCalleIncidente = null;

const cacheDirecciones = {};

const mapa = L.map("mapa").setView([-34.61, -58.43], 12);

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

function distanciaAConexion(lat, lon, origen, destino, muestras = 20) {
  let minima = Infinity;
  for (let i = 0; i <= muestras; i++) {
    const t = i / muestras;
    const latInterpolada = origen.latitud + t * (destino.latitud - origen.latitud);
    const lonInterpolada =
      origen.longitud + t * (destino.longitud - origen.longitud);
    const distancia = distanciaEnMetros(lat, lon, latInterpolada, lonInterpolada);
    if (distancia < minima) minima = distancia;
  }
  return minima;
}

function conexionMasCercana(lat, lon) {
  let mejor = null;
  let mejorDistancia = Infinity;

  for (const id in conexionesPorId) {
    const conexion = conexionesPorId[id];
    const origen = ubicacionesPorId[conexion.origen_id];
    const destino = ubicacionesPorId[conexion.destino_id];
    if (!origen || !destino) continue;

    const distancia = distanciaAConexion(lat, lon, origen, destino);
    if (distancia < mejorDistancia) {
      mejorDistancia = distancia;
      mejor = conexion;
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

function configurarBuscador(inputId, sugerenciasId, alElegir, alInvalidar) {
  const input = document.getElementById(inputId);
  const listaSugerencias = document.getElementById(sugerenciasId);
  let temporizador = null;
  let ultimaSeleccionConfirmada = null;

  input.addEventListener("input", () => {
    if (input.value !== ultimaSeleccionConfirmada) {
      alInvalidar();
    }

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

        const textoElegido = resultado.display_name
          .split(",")
          .slice(0, 2)
          .join(",");

        input.value = textoElegido;
        ultimaSeleccionConfirmada = textoElegido;

        listaSugerencias.hidden = true;
        listaSugerencias.innerHTML = "";

        alElegir(lat, lon);
      });

      listaSugerencias.appendChild(item);
    }

    listaSugerencias.hidden = false;
  }
}

configurarBuscador(
  "origen-input",
  "origen-sugerencias",
  (lat, lon) => {
    const cercana = ubicacionMasCercana(lat, lon);
    seleccionOrigen = cercana;
    marcadorOrigen = ubicarMarcadorSeleccion(
      marcadorOrigen,
      cercana,
      "Origen",
      "#1a7d3c"
    );
    mapa.panTo([cercana.latitud, cercana.longitud]);
  },
  () => {
    seleccionOrigen = null;
  }
);

configurarBuscador(
  "destino-input",
  "destino-sugerencias",
  (lat, lon) => {
    const cercana = ubicacionMasCercana(lat, lon);
    seleccionDestino = cercana;
    marcadorDestino = ubicarMarcadorSeleccion(
      marcadorDestino,
      cercana,
      "Destino",
      "#a12727"
    );
    mapa.panTo([cercana.latitud, cercana.longitud]);
  },
  () => {
    seleccionDestino = null;
  }
);

async function cargarUbicaciones() {
  const respuesta = await fetch(`${API_BASE_URL}/locations`);
  const ubicaciones = await respuesta.json();

  ubicacionesPorId = {};
  for (const ubicacion of ubicaciones) {
    ubicacionesPorId[ubicacion.id] = ubicacion;
  }
}

async function cargarConexiones() {
  const respuesta = await fetch(`${API_BASE_URL}/connections`);
  const conexiones = await respuesta.json();

  conexionesPorId = {};
  for (const conexion of conexiones) {
    conexionesPorId[conexion.id] = conexion;
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

function formatearDetalleError(detail) {
  if (!detail) return "No se pudo calcular la ruta.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || "Valor inválido.").join(" ");
  }
  return "No se pudo calcular la ruta.";
}

async function calcularRuta() {
  limpiarResultadoAnterior();

  if (!seleccionOrigen) {
    divError.textContent = "Falta elegir un origen de la lista de sugerencias.";
    return;
  }
  if (!seleccionDestino) {
    divError.textContent = "Falta elegir un destino de la lista de sugerencias.";
    return;
  }

  const origin = seleccionOrigen.id;
  const destination = seleccionDestino.id;
  const criteria = selectCriterio.value;

  const parametros = new URLSearchParams({ origin, destination, criteria });

  if (criteria === "balanceada") {
    const alpha = Number(inputAlpha.value);
    const beta = Number(inputBeta.value);

    const fueraDeRango = (valor) => Number.isNaN(valor) || valor < 0 || valor > 1;
    if (fueraDeRango(alpha) || fueraDeRango(beta)) {
      divError.textContent = "Alpha y Beta deben ser números entre 0 y 1.";
      return;
    }

    parametros.set("alpha", alpha);
    parametros.set("beta", beta);
  }

  try {
    const respuesta = await fetch(`${API_BASE_URL}/route?${parametros}`);
    const datos = await respuesta.json();

    if (!respuesta.ok) {
      divError.textContent = formatearDetalleError(datos.detail);
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

let token = localStorage.getItem("token");

const divCuentaLogueada = document.getElementById("cuenta-logueada");
const spanCuentaEmail = document.getElementById("cuenta-email");
const botonCerrarSesion = document.getElementById("cerrar-sesion");
const detallesCuentaDesconectada = document.getElementById(
  "cuenta-desconectada"
);
const inputCuentaEmail = document.getElementById("cuenta-email-input");
const inputCuentaPassword = document.getElementById("cuenta-password-input");
const botonCuentaLogin = document.getElementById("cuenta-login");
const botonCuentaRegistro = document.getElementById("cuenta-registro");
const divCuentaError = document.getElementById("cuenta-error");
const listaMisReportes = document.getElementById("lista-mis-reportes");

function mostrarSesionActiva(email) {
  divCuentaLogueada.hidden = false;
  detallesCuentaDesconectada.hidden = true;
  detallesReporte.hidden = false;
  spanCuentaEmail.textContent = email;
  cargarMisReportes();
}

function mostrarSesionInactiva() {
  divCuentaLogueada.hidden = true;
  detallesCuentaDesconectada.hidden = false;
  detallesReporte.hidden = true;
  listaMisReportes.innerHTML = "";
}

function guardarSesion(nuevoToken, email) {
  token = nuevoToken;
  localStorage.setItem("token", token);
  localStorage.setItem("email", email);
  mostrarSesionActiva(email);
}

function cerrarSesion() {
  token = null;
  localStorage.removeItem("token");
  localStorage.removeItem("email");
  mostrarSesionInactiva();
}

async function intentarLogin(email, password) {
  const respuesta = await fetch(`${API_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const datos = await respuesta.json();
  return { ok: respuesta.ok, datos };
}

async function intentarRegistro(email, password) {
  const respuesta = await fetch(`${API_BASE_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const datos = await respuesta.json();
  return { ok: respuesta.ok, datos };
}

async function iniciarSesion() {
  divCuentaError.textContent = "";
  const email = inputCuentaEmail.value;
  const password = inputCuentaPassword.value;

  try {
    const { ok, datos } = await intentarLogin(email, password);
    if (!ok) {
      divCuentaError.textContent = formatearDetalleError(datos.detail);
      return;
    }
    guardarSesion(datos.access_token, email);
  } catch (error) {
    divCuentaError.textContent = "No se pudo conectar con la API.";
  }
}

async function registrarse() {
  divCuentaError.textContent = "";
  const email = inputCuentaEmail.value;
  const password = inputCuentaPassword.value;

  try {
    const { ok, datos } = await intentarRegistro(email, password);
    if (!ok) {
      divCuentaError.textContent = formatearDetalleError(datos.detail);
      return;
    }
    await iniciarSesion();
  } catch (error) {
    divCuentaError.textContent = "No se pudo conectar con la API.";
  }
}

botonCuentaLogin.addEventListener("click", iniciarSesion);
botonCuentaRegistro.addEventListener("click", registrarse);
botonCerrarSesion.addEventListener("click", cerrarSesion);

const modalBienvenida = document.getElementById("bienvenida-modal");
const inputBienvenidaEmail = document.getElementById("bienvenida-email-input");
const inputBienvenidaPassword = document.getElementById(
  "bienvenida-password-input"
);
const botonBienvenidaLogin = document.getElementById("bienvenida-login");
const botonBienvenidaRegistro = document.getElementById("bienvenida-registro");
const botonBienvenidaInvitado = document.getElementById(
  "bienvenida-invitado"
);
const divBienvenidaError = document.getElementById("bienvenida-error");

function cerrarBienvenida() {
  modalBienvenida.hidden = true;
}

async function iniciarSesionDesdeBienvenida() {
  divBienvenidaError.textContent = "";
  const email = inputBienvenidaEmail.value;
  const password = inputBienvenidaPassword.value;

  try {
    const { ok, datos } = await intentarLogin(email, password);
    if (!ok) {
      divBienvenidaError.textContent = formatearDetalleError(datos.detail);
      return;
    }
    guardarSesion(datos.access_token, email);
    cerrarBienvenida();
  } catch (error) {
    divBienvenidaError.textContent = "No se pudo conectar con la API.";
  }
}

async function registrarseDesdeBienvenida() {
  divBienvenidaError.textContent = "";
  const email = inputBienvenidaEmail.value;
  const password = inputBienvenidaPassword.value;

  try {
    const { ok, datos } = await intentarRegistro(email, password);
    if (!ok) {
      divBienvenidaError.textContent = formatearDetalleError(datos.detail);
      return;
    }
    const resultadoLogin = await intentarLogin(email, password);
    if (resultadoLogin.ok) {
      guardarSesion(resultadoLogin.datos.access_token, email);
      cerrarBienvenida();
    }
  } catch (error) {
    divBienvenidaError.textContent = "No se pudo conectar con la API.";
  }
}

function continuarComoInvitado() {
  mostrarSesionInactiva();
  cerrarBienvenida();
}

botonBienvenidaLogin.addEventListener("click", iniciarSesionDesdeBienvenida);
botonBienvenidaRegistro.addEventListener(
  "click",
  registrarseDesdeBienvenida
);
botonBienvenidaInvitado.addEventListener("click", continuarComoInvitado);

async function cargarMisReportes() {
  if (!token) return;

  try {
    const respuesta = await fetch(`${API_BASE_URL}/incidents/mine`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!respuesta.ok) return;

    const incidentes = await respuesta.json();
    renderizarMisReportes(incidentes);
  } catch (error) {}
}

function renderizarMisReportes(incidentes) {
  listaMisReportes.innerHTML = "";

  for (const incidente of incidentes) {
    const item = document.createElement("li");
    item.textContent = `${incidente.tipo} (gravedad ${incidente.gravedad})`;

    const botonBorrar = document.createElement("button");
    botonBorrar.textContent = "Borrar";
    botonBorrar.addEventListener("click", () => borrarReporte(incidente.id));

    item.appendChild(botonBorrar);
    listaMisReportes.appendChild(item);
  }
}

async function borrarReporte(id) {
  try {
    const respuesta = await fetch(`${API_BASE_URL}/incidents/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (respuesta.status === 204) {
      cargarMisReportes();
    }
  } catch (error) {}
}

const detallesReporte = document.getElementById("detalles-reporte");
const selectIncidenteTipo = document.getElementById("incidente-tipo");
const botonEnviarIncidente = document.getElementById("incidente-enviar");
const divIncidenteResultado = document.getElementById("incidente-resultado");
const divIncidenteError = document.getElementById("incidente-error");

function marcarCalleSeleccionada(conexion) {
  if (lineaCalleIncidente) {
    mapa.removeLayer(lineaCalleIncidente);
  }
  const origen = ubicacionesPorId[conexion.origen_id];
  const destino = ubicacionesPorId[conexion.destino_id];

  lineaCalleIncidente = L.polyline(
    [
      [origen.latitud, origen.longitud],
      [destino.latitud, destino.longitud],
    ],
    { color: "#c98a12", weight: 6, opacity: 0.9 }
  ).addTo(mapa);

  mapa.fitBounds(lineaCalleIncidente.getBounds(), { padding: [60, 60] });
}

configurarBuscador(
  "incidente-direccion-input",
  "incidente-direccion-sugerencias",
  (lat, lon) => {
    seleccionCalleIncidente = conexionMasCercana(lat, lon);
    if (seleccionCalleIncidente) {
      marcarCalleSeleccionada(seleccionCalleIncidente);
    }
  },
  () => {
    seleccionCalleIncidente = null;
  }
);

detallesReporte.addEventListener("toggle", () => {
  if (detallesReporte.open) {
    divIncidenteResultado.textContent = "";
    divIncidenteError.textContent = "";
  } else {
    if (lineaCalleIncidente) {
      mapa.removeLayer(lineaCalleIncidente);
      lineaCalleIncidente = null;
    }
    seleccionCalleIncidente = null;
    document.getElementById("incidente-direccion-input").value = "";
  }
});

async function enviarIncidente() {
  divIncidenteError.textContent = "";
  divIncidenteResultado.textContent = "";

  if (!token) {
    divIncidenteError.textContent = "Iniciá sesión para reportar un incidente.";
    return;
  }

  if (!seleccionCalleIncidente) {
    divIncidenteError.textContent =
      "Buscá y elegí una dirección de la lista de sugerencias.";
    return;
  }

  const cuerpo = {
    conexion_id: seleccionCalleIncidente.id,
    tipo: selectIncidenteTipo.value,
  };

  try {
    const respuesta = await fetch(`${API_BASE_URL}/incidents`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(cuerpo),
    });
    const datos = await respuesta.json();

    if (!respuesta.ok) {
      divIncidenteError.textContent = formatearDetalleError(datos.detail);
      return;
    }

    divIncidenteResultado.textContent =
      "¡Gracias! Reporte cargado. La seguridad de esta calle se va a " +
      "ajustar en los próximos cálculos de ruta.";
    cargarMisReportes();
  } catch (error) {
    divIncidenteError.textContent =
      "No se pudo conectar con la API. ¿Está corriendo el backend?";
  }
}

botonEnviarIncidente.addEventListener("click", enviarIncidente);

if (token) {
  mostrarSesionActiva(localStorage.getItem("email") || "");
  cerrarBienvenida();
} else {
  mostrarSesionInactiva();
}

cargarUbicaciones().catch(() => {
  divError.textContent =
    "No se pudieron cargar las ubicaciones. ¿Está corriendo el backend?";
});

cargarConexiones().catch(() => {
  divError.textContent =
    "No se pudieron cargar las calles. ¿Está corriendo el backend?";
});