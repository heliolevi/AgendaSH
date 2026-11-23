// Calendário + formulário de agendamento com INÍCIO e FIM.
// - reunião: mesmo dia, fim depois do início; evento: pode terminar em outro dia ("Termina em")
// - régua do dia: seus compromissos, o local já ocupado e o horário que você está escolhendo
// - aviso de conflito ANTES de enviar (o backend continua sendo quem decide: 409)
// - edição: calendario.html?editar=reuniao-12 ou ?editar=evento-3 (PUT)
const usuario = exigirLogin();
const DIAS_CAB = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
const DURACAO_PADRAO = 60;

let agenda = { todas: [], minhas: [], salas: [] };
let mes = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
let selecionado = chaveDia(new Date());
let editando = null; // {tipo, id, item}
let enviando = false;
let duracaoLembrada = DURACAO_PADRAO;

$("avatar").innerHTML = avatarHtml(usuario);
renderNav("calendario");
$("ant").innerHTML = icone("caret-left");
$("prox").innerHTML = icone("caret-right");
$("segModo").innerHTML = `
    <label><input type="radio" name="modo" value="Online" checked><span>${icone("video-camera")}Online</span></label>
    <label><input type="radio" name="modo" value="Presencial"><span>${icone("map-pin")}Presencial</span></label>`;

const tipoAtual = () => document.querySelector('input[name="tipo"]:checked').value;
const modoAtual = () => document.querySelector('input[name="modo"]:checked').value;
const hojeChave = () => chaveDia(new Date());
const ehEditado = (x) => !!editando && x.tipo === editando.tipo && x.id === editando.id;
const telaPequena = () => matchMedia("(max-width: 1023px)").matches;

// ------------------------------------------------------------ calendário mensal
function compromissosPorDia() {
    const mapa = new Map();
    for (const x of agenda.minhas) {
        // marca todos os dias que o compromisso atravessa (eventos de vários dias)
        const d = deChave(chaveDia(x.inicio));
        while (d < x.fim) {
            const k = chaveDia(d);
            if (!mapa.has(k)) mapa.set(k, []);
            mapa.get(k).push(x.tipo);
            d.setDate(d.getDate() + 1);
        }
    }
    return mapa;
}

function desenharCalendario() {
    $("mes").textContent = MESES[mes.getMonth()].replace(/^./, (c) => c.toUpperCase()) + " de " + mes.getFullYear();
    const marcas = compromissosPorDia();
    const hoje = hojeChave();
    const primeiro = mes.getDay();
    const total = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
    let html = DIAS_CAB.map((d) => `<div class="dow" aria-hidden="true">${d}</div>`).join("");
    for (let i = 0; i < primeiro; i++) html += '<div aria-hidden="true"></div>';
    for (let d = 1; d <= total; d++) {
        const k = chaveDia(new Date(mes.getFullYear(), mes.getMonth(), d));
        const passado = k < hoje; // não se agenda em dia que já passou (mesma regra do backend)
        const tipos = marcas.get(k) || [];
        const qtd = tipos.length;
        const cls = ["dia", k === hoje && "hoje", k === selecionado && "sel"].filter(Boolean).join(" ");
        const rotulo = `${d} de ${MESES[mes.getMonth()]}${qtd ? `, ${qtd} compromisso${qtd > 1 ? "s" : ""}` : ""}${passado ? ", já passou" : ""}`;
        const pontos = [...new Set(tipos)].sort().map((t) => `<i class="m-${t}"></i>`).join("");
        html += `<button type="button" class="${cls}" data-dia="${k}" aria-label="${rotulo}" aria-pressed="${k === selecionado}"${k === hoje ? ' aria-current="date"' : ""}${passado ? " disabled" : ""}>${d}${pontos ? `<span class="marcas" aria-hidden="true">${pontos}</span>` : ""}</button>`;
    }
    $("grade").innerHTML = html;
    const mesAtual = new Date(); mesAtual.setDate(1); mesAtual.setHours(0, 0, 0, 0);
    $("ant").disabled = mes <= mesAtual;
}

function selecionarDia(k, { rolar = false } = {}) {
    if (k < hojeChave() && !editando) k = hojeChave();
    const mudouDia = k !== selecionado;
    selecionado = k;
    const d = deChave(k);
    mes = new Date(d.getFullYear(), d.getMonth(), 1);
    $("dataIni").value = k;
    $("dataFim").min = k;
    if (mudouDia && !editando) sugerirHorario();
    else definirFimPorDuracao(duracaoLembrada);
    desenharCalendario();
    desenharDoDia();
    atualizarProposta();
    if (rolar && telaPequena()) $("novo").scrollIntoView({ behavior: "smooth", block: "start" });
}

// hoje: próxima meia hora a partir de agora; outros dias: 09:00
function sugerirHorario() {
    let ini = "09:00";
    if (selecionado === hojeChave()) {
        const a = new Date();
        let min = Math.ceil((a.getHours() * 60 + a.getMinutes() + 5) / 30) * 30;
        if (min > 23 * 60) min = 23 * 60;
        ini = pad(Math.floor(min / 60)) + ":" + pad(min % 60);
    }
    $("horaIni").value = ini;
    definirFimPorDuracao(duracaoLembrada);
}

// ------------------------------------------------------------ início, fim e duração
function intervalo() {
    const di = $("dataIni").value, hi = $("horaIni").value, hf = $("horaFim").value;
    if (!di || !hi || !hf) return null;
    const df = tipoAtual() === "evento" && $("dataFim").value ? $("dataFim").value : di;
    return { inicio: juntarDataHora(di, hi), fim: juntarDataHora(df, hf) };
}

function duracaoAtual() {
    const r = intervalo();
    return r ? minutosEntre(r.inicio, r.fim) : 0;
}

function definirFimPorDuracao(min) {
    if (!$("horaIni").value) return;
    const ini = juntarDataHora($("dataIni").value || selecionado, $("horaIni").value);
    let fim = new Date(ini.getTime() + min * 60000);
    if (tipoAtual() === "reuniao" && chaveDia(fim) !== chaveDia(ini)) fim = juntarDataHora(chaveDia(ini), "23:55"); // reunião não passa da meia-noite
    $("horaFim").value = horaDe(fim);
    $("dataFim").value = chaveDia(fim);
}

$("horaIni").addEventListener("change", () => { definirFimPorDuracao(duracaoLembrada); atualizarProposta(); });
$("horaFim").addEventListener("change", () => { const d = duracaoAtual(); if (d > 0) duracaoLembrada = d; atualizarProposta(); });
$("dataFim").addEventListener("change", () => { const d = duracaoAtual(); if (d > 0) duracaoLembrada = d; atualizarProposta(); });
$("dataIni").addEventListener("change", () => { if ($("dataIni").value) selecionarDia($("dataIni").value); });
$("duracoes").addEventListener("click", (e) => {
    const b = e.target.closest("[data-min]");
    if (!b) return;
    duracaoLembrada = Number(b.dataset.min);
    definirFimPorDuracao(duracaoLembrada);
    atualizarProposta();
});

// ------------------------------------------------------------ local (sala) e conflito
function sincronizarModo() {
    const online = modoAtual() === "Online";
    $("rotuloLocal").textContent = online ? "Link da reunião" : "Endereço ou sala";
    $("local").placeholder = online ? "https://meet.exemplo.com/abc-defg" : "Ex.: Bloco B, sala 204";
    $("local").inputMode = online ? "url" : "text";
    $("dicaLocal").textContent = online ? "Cole o link completo, começando com https://" : "As sugestões mostram os locais já usados.";
    const usados = [...new Set(agenda.salas.filter((s) => s.tipo === modoAtual()).map((s) => s.localizacao_link || s.nome))].slice(0, 30);
    const dl = $("locais");
    dl.textContent = "";
    for (const v of usados) { const o = document.createElement("option"); o.value = v; dl.appendChild(o); }
}
document.querySelectorAll('input[name="modo"]').forEach((r) => r.addEventListener("change", () => { sincronizarModo(); validarLocal(false); atualizarProposta(); }));
$("local").addEventListener("input", () => { $("erroLocal").textContent = ""; $("local").removeAttribute("aria-invalid"); atualizarProposta(); });
$("local").addEventListener("blur", () => validarLocal(false));

function validarLocal(obrigatorio) {
    const v = $("local").value.trim();
    let erro = "";
    if (!v) erro = obrigatorio ? "Informe onde vai ser." : "";
    else if (modoAtual() === "Online" && !urlSegura(v)) erro = "Para reunião online, use um link completo começando com https://";
    $("erroLocal").textContent = erro;
    if (erro) $("local").setAttribute("aria-invalid", "true"); else $("local").removeAttribute("aria-invalid");
    return !erro;
}

function salaEscolhida() {
    const v = $("local").value.trim();
    return v ? acharSala(agenda.salas, modoAtual(), v) : null;
}

// ------------------------------------------------------------ proposta: régua + resumo + validação de horário
function validarHorario(r) {
    if (!$("horaIni").value || !$("horaFim").value) return "Informe o início e o fim.";
    if (!r) return "Escolha a data.";
    if (r.fim <= r.inicio) {
        return tipoAtual() === "reuniao"
            ? "O fim precisa ser depois do início. Se passar da meia-noite, marque como evento."
            : "O fim precisa ser depois do início.";
    }
    if (!editando && r.inicio < new Date(Date.now() - 5 * 60000)) return "Esse horário já passou. Escolha um início a partir de agora.";
    if (minutosEntre(r.inicio, r.fim) > 14 * 24 * 60) return "Um evento pode durar no máximo 14 dias.";
    return "";
}

function atualizarProposta() {
    const r = intervalo();
    const erroH = validarHorario(r);
    $("erroHorario").textContent = erroH;
    ["horaIni", "horaFim"].forEach((id) => (erroH ? $(id).setAttribute("aria-invalid", "true") : $(id).removeAttribute("aria-invalid")));
    const dur = !erroH && r ? minutosEntre(r.inicio, r.fim) : 0;
    document.querySelectorAll("#duracoes .chip").forEach((c) => c.setAttribute("aria-pressed", String(Number(c.dataset.min) === dur)));

    const sala = salaEscolhida();
    const itens = agenda.minhas.filter((x) => !ehEditado(x));
    const ocupados = sala ? agenda.todas.filter((x) => x.id_sala === sala.id_sala && !ehEditado(x) && !itens.includes(x)) : [];
    const conflitos = sala && r && !erroH
        ? agenda.todas.filter((x) => x.id_sala === sala.id_sala && !ehEditado(x) && x.inicio < r.fim && x.fim > r.inicio)
        : [];

    desenharRegua($("reguaForm"), {
        dia: deChave(selecionado),
        itens,
        ocupados,
        proposta: r && !erroH ? { ...r, conflito: conflitos.length > 0 } : null,
        aoEscolherHora: (hhmm) => { $("horaIni").value = hhmm; definirFimPorDuracao(duracaoLembrada); atualizarProposta(); },
    });

    const resumo = $("resumo");
    resumo.classList.toggle("conflito", conflitos.length > 0);
    resumo.hidden = !!erroH || !r;
    if (!resumo.hidden) {
        const multi = chaveDia(r.inicio) !== chaveDia(r.fim);
        const fimTxt = multi ? `${dataCurta(r.fim)} ${horaDe(r.fim)}` : horaDe(r.fim);
        let html = `${icone(conflitos.length ? "warning-circle" : "clock")}<span>${esc(rotuloDia(r.inicio))}</span><b>${horaDe(r.inicio)} às ${esc(fimTxt)}</b><span>· ${duracaoTexto(dur)}</span>`;
        if (conflitos.length) {
            const c = conflitos[0];
            const quem = c.organizo ? `"${esc(c.titulo)}"` : (c.tipo === "evento" ? "um evento" : "outra reunião");
            html += `<span class="aviso-conflito">Esse local já tem ${quem} das ${horaDe(c.inicio)} às ${horaDe(c.fim)}. Mude o horário ou o local.</span>`;
        }
        resumo.innerHTML = html;
    }
    return { r, erroH, conflitos };
}

// ------------------------------------------------------------ tipo (reunião / evento)
function sincronizarTipo() {
    const evento = tipoAtual() === "evento";
    $("campoDataFim").hidden = !evento;
    $("dicaTipo").textContent = evento
        ? "Evento aparece para toda a equipe e pode durar mais de um dia."
        : "Reunião aparece para você e para quem for convidado. Começa e termina no mesmo dia.";
    $("titulo").placeholder = evento ? "Ex.: Hackathon da SH" : "Ex.: Alinhamento da sprint";
    if (!evento) $("dataFim").value = $("dataIni").value;
    $("btnSalvar").textContent = editando ? "Salvar alterações" : evento ? "Confirmar evento" : "Confirmar reunião";
    $("tForm").innerHTML = icone(editando ? "pencil-simple" : "calendar-plus") + (editando ? (evento ? "Editar evento" : "Editar reunião") : "Novo agendamento");
}
document.querySelectorAll('input[name="tipo"]').forEach((r) => r.addEventListener("change", () => {
    sincronizarTipo();
    definirFimPorDuracao(duracaoLembrada);
    atualizarProposta();
}));

// ------------------------------------------------------------ compromissos do dia selecionado
function desenharDoDia() {
    const d = deChave(selecionado);
    const k = selecionado;
    const doDia = agenda.minhas.filter((x) => chaveDia(x.inicio) <= k && chaveDia(x.fim) >= k);
    const rot = rotuloDia(d);
    $("tDia").textContent = rot === "Hoje" || rot === "Amanhã" ? `${rot}, ${dataLonga(d)}` : dataLonga(d).replace(/^./, (c) => c.toUpperCase());
    $("subDia").textContent = doDia.length ? `${doDia.length} compromisso${doDia.length > 1 ? "s" : ""} na sua agenda` : "";
    $("doDia").innerHTML = doDia.length
        ? `<div class="lista">${doDia.map((x) => cartaoAgenda(x, { acoes: true })).join("")}</div>`
        : estadoVazio("Dia livre", "Nada marcado para você neste dia.");
}
$("doDia").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-excluir]");
    if (b && (await excluirDoCartao(b))) await carregar();
});

// ------------------------------------------------------------ calendário: cliques e teclado
$("grade").addEventListener("click", (e) => {
    const b = e.target.closest("[data-dia]");
    if (b && !b.disabled) selecionarDia(b.dataset.dia, { rolar: true });
});
$("grade").addEventListener("keydown", (e) => { // setas movem o dia selecionado
    const passos = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (!(e.key in passos) || !e.target.matches("[data-dia]")) return;
    e.preventDefault();
    const d = deChave(e.target.dataset.dia);
    d.setDate(d.getDate() + passos[e.key]);
    const k = chaveDia(d);
    if (k < hojeChave()) return;
    selecionarDia(k);
    $("grade").querySelector(`[data-dia="${k}"]`)?.focus();
});
$("ant").addEventListener("click", () => { mes = new Date(mes.getFullYear(), mes.getMonth() - 1, 1); desenharCalendario(); });
$("prox").addEventListener("click", () => { mes = new Date(mes.getFullYear(), mes.getMonth() + 1, 1); desenharCalendario(); });
$("irHoje").addEventListener("click", () => selecionarDia(hojeChave()));

// ------------------------------------------------------------ enviar
$("titulo").addEventListener("input", () => { $("erroTitulo").textContent = ""; $("titulo").removeAttribute("aria-invalid"); });

$("formAgenda").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (enviando) return;
    $("msgErro").textContent = "";
    const titulo = $("titulo").value.trim();
    const local = $("local").value.trim();
    const descricao = $("descricao").value.trim();
    const evento = tipoAtual() === "evento";

    $("erroTitulo").textContent = titulo ? "" : `Dê um nome para ${evento ? "o evento" : "a reunião"}.`;
    titulo ? $("titulo").removeAttribute("aria-invalid") : $("titulo").setAttribute("aria-invalid", "true");
    const okLocal = validarLocal(true);
    const { r, erroH, conflitos } = atualizarProposta();

    const primeiroInvalido = !titulo ? $("titulo") : erroH ? $("horaIni") : !okLocal ? $("local") : null;
    if (primeiroInvalido) { primeiroInvalido.focus(); return; }
    if (conflitos.length) { $("msgErro").textContent = "O local escolhido já está ocupado nesse horário."; $("horaIni").focus(); return; }

    enviando = true;
    ocupado($("btnSalvar"), true, editando ? "Salvando…" : "Confirmando…");
    try {
        const sala = await obterSala(modoAtual(), local, agenda.salas);
        const corpo = { id_sala: sala.id_sala, titulo, descricao: descricao || null, data_inicio: paraIsoLocal(r.inicio), data_fim: paraIsoLocal(r.fim) };
        const base = evento ? "/eventos" : "/reunioes";
        if (editando) {
            await api(`${base}/${Number(editando.id)}`, { method: "PUT", body: corpo });
            avisar(evento ? "Evento atualizado." : "Reunião atualizada.");
            sairEdicao();
        } else {
            await api(base, { method: "POST", body: corpo });
            avisar(`${evento ? "Evento confirmado" : "Reunião confirmada"}: ${rotuloDia(r.inicio).toLowerCase()}, ${horaDe(r.inicio)} às ${horaDe(r.fim)}.`);
            $("titulo").value = "";
            $("descricao").value = "";
        }
        await carregar();
    } catch (err) {
        $("msgErro").textContent = err.status === 409
            ? "Alguém marcou esse local nesse horário agora há pouco. Escolha outro horário ou local."
            : err.message;
    } finally {
        enviando = false;
        ocupado($("btnSalvar"), false);
        sincronizarTipo();
    }
});

// ------------------------------------------------------------ edição
function entrarEdicao(item) {
    editando = { tipo: item.tipo, id: item.id };
    document.querySelector(`input[name="tipo"][value="${item.tipo}"]`).checked = true;
    document.querySelectorAll('input[name="tipo"]').forEach((r) => (r.disabled = r.value !== item.tipo)); // trocar o tipo exigiria apagar e recriar
    $("titulo").value = item.titulo;
    $("descricao").value = item.descricao || "";
    if (item.sala) {
        document.querySelector(`input[name="modo"][value="${item.sala.tipo === "Presencial" ? "Presencial" : "Online"}"]`).checked = true;
        $("local").value = item.sala.localizacao_link || item.sala.nome;
    }
    sincronizarModo();
    selecionado = chaveDia(item.inicio);
    mes = new Date(item.inicio.getFullYear(), item.inicio.getMonth(), 1);
    $("dataIni").value = selecionado;
    $("horaIni").value = horaDe(item.inicio);
    $("horaFim").value = horaDe(item.fim);
    $("dataFim").value = chaveDia(item.fim);
    duracaoLembrada = minutosEntre(item.inicio, item.fim);
    $("textoEdicao").textContent = `Editando "${item.titulo}"`;
    $("faixaEdicao").hidden = false;
    sincronizarTipo();
}

function sairEdicao() {
    editando = null;
    $("faixaEdicao").hidden = true;
    document.querySelectorAll('input[name="tipo"]').forEach((r) => (r.disabled = false));
    $("titulo").value = "";
    $("descricao").value = "";
    history.replaceState(null, "", "calendario.html");
    sincronizarTipo();
}

// ------------------------------------------------------------ carregar
async function carregar() {
    try {
        agenda = await carregarAgenda(usuario);
    } catch (e) {
        $("doDia").innerHTML = estadoErro(e.message);
        avisar(e.message, "erro");
        return;
    }
    sincronizarModo();
    desenharCalendario();
    desenharDoDia();
    atualizarProposta();
}

(async function iniciar() {
    $("dataIni").min = hojeChave();
    sincronizarTipo();
    sincronizarModo();
    selecionarDia(hojeChave());
    sugerirHorario();
    await carregar();

    const alvo = new URLSearchParams(location.search).get("editar");
    const m = alvo && /^(reuniao|evento)-(\d+)$/.exec(alvo);
    if (m) {
        const item = agenda.todas.find((x) => x.tipo === m[1] && x.id === Number(m[2]));
        if (item && item.podeEditar) {
            entrarEdicao(item);
            desenharCalendario();
            desenharDoDia();
            atualizarProposta();
            $("titulo").focus({ preventScroll: !telaPequena() });
            if (telaPequena()) $("novo").scrollIntoView({ block: "start" });
        } else {
            avisar("Esse compromisso não existe mais ou você não pode editá-lo.", "erro");
            history.replaceState(null, "", "calendario.html");
        }
    } else if (location.hash === "#novo") {
        $("titulo").focus({ preventScroll: true });
        if (telaPequena()) $("novo").scrollIntoView({ block: "start" });
    }
})();
