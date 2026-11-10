// Calendário + formulário de agendamento (design: tela "Calendário").
const usuario = exigirLogin();
const $ = (id) => document.getElementById(id);
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const DIAS = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SAB"];
const DURACAO_MIN = 60; // o design só pede o horário de início: reunião de 1h

let mes = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
let selecionado = new Date();
let reunioes = [];

$("avatar").innerHTML = avatarHtml(usuario);
renderNav("calendario");

function desenharCalendario() {
    $("mes").textContent = MESES[mes.getMonth()] + " " + mes.getFullYear();
    const comReuniao = new Set(reunioes.map((r) => chaveDia(r.inicio)));
    const hoje = chaveDia(new Date());
    const primeiro = mes.getDay();
    const total = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
    let html = DIAS.map((d) => `<div class="dow">${d}</div>`).join("");
    for (let i = 0; i < primeiro; i++) html += '<div></div>';
    for (let d = 1; d <= total; d++) {
        const data = new Date(mes.getFullYear(), mes.getMonth(), d);
        const k = chaveDia(data);
        const cls = ["dia", k === hoje && "hoje", k === chaveDia(selecionado) && "sel", comReuniao.has(k) && "tem"].filter(Boolean).join(" ");
        html += `<button type="button" class="${cls}" data-dia="${d}">${d}</button>`;
    }
    $("grade").innerHTML = html;
}

function desenharDoDia() {
    const k = chaveDia(selecionado);
    const doDia = reunioes.filter((r) => chaveDia(r.inicio) === k);
    $("doDia").innerHTML = doDia.length
        ? `<div class="secao"><h2>${dataCurta(selecionado)}</h2></div>` + doDia.map((r) => cartaoReuniao(r, usuario)).join("")
        : "";
}

async function carregar() {
    try { reunioes = await minhasReunioes(usuario); } catch (e) { $("msgErro").textContent = e.message; }
    desenharCalendario();
    desenharDoDia();
}

$("grade").addEventListener("click", (e) => {
    const b = e.target.closest("[data-dia]");
    if (!b) return;
    selecionado = new Date(mes.getFullYear(), mes.getMonth(), Number(b.dataset.dia));
    desenharCalendario();
    desenharDoDia();
});
$("ant").onclick = () => { mes = new Date(mes.getFullYear(), mes.getMonth() - 1, 1); desenharCalendario(); };
$("prox").onclick = () => { mes = new Date(mes.getFullYear(), mes.getMonth() + 1, 1); desenharCalendario(); };
$("modo").onchange = () => { $("local").placeholder = $("modo").value === "Online" ? "Link da reunião" : "Endereço"; };

// A tabela reuniao exige uma sala. Modo + Local do formulário viram (ou reaproveitam) uma sala.
async function obterSala(modo, local) {
    const salas = await api("/salas");
    const existente = salas.find((s) => s.tipo === modo && (s.localizacao_link === local || s.nome === local));
    if (existente) return existente;
    return api("/salas", { method: "POST", body: { nome: local.slice(0, 100), capacidade: 10, tipo: modo, localizacao_link: local } });
}

function paraIso(data, hhmm, somarMin = 0) {
    const [h, m] = hhmm.split(":").map(Number);
    const d = new Date(data.getFullYear(), data.getMonth(), data.getDate(), h, m + somarMin);
    return `${chaveDia(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
}

$("formReuniao").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("msgErro");
    msg.className = "msg";
    msg.textContent = "";
    const titulo = $("titulo").value.trim();
    const local = $("local").value.trim();
    if (!$("hora").value) return (msg.textContent = "Informe o horário");
    if (!titulo) return (msg.textContent = "Informe o nome da reunião");
    if (!local) return (msg.textContent = "Informe o local");
    $("btnSalvar").disabled = true;
    try {
        const sala = await obterSala($("modo").value, local);
        await api("/reunioes", {
            method: "POST",
            body: {
                id_usuario: usuario.id_usuario,
                id_sala: sala.id_sala,
                titulo,
                descricao: null,
                data_inicio: paraIso(selecionado, $("hora").value),
                data_fim: paraIso(selecionado, $("hora").value, DURACAO_MIN),
            },
        });
        msg.className = "msg ok";
        msg.textContent = "Reunião confirmada!";
        $("titulo").value = "";
        await carregar();
    } catch (err) {
        msg.textContent = err.message;
    } finally {
        $("btnSalvar").disabled = false;
    }
});

carregar();
