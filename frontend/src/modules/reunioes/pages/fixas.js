// Reuniões fixas (semanais): criar série e cancelar série.
const usuario = exigirLogin();
$("avatar").innerHTML = avatarHtml(usuario);
renderNav("reunioes");

let salas = [];
let enviando = false;
const hoje = chaveDia(new Date());

$("dia").innerHTML = DIAS_SEMANA.map((d, i) => `<option value="${i}">${d}</option>`).join("");
$("dia").value = String((new Date().getDay() + 6) % 7); // hoje, no padrão do backend (0 = segunda)
$("dataIni").value = hoje;
$("dataIni").min = hoje;
$("dataFim").min = hoje;
$("segModo").innerHTML = `
    <label><input type="radio" name="modo" value="Online" checked><span>${icone("video-camera")}Online</span></label>
    <label><input type="radio" name="modo" value="Presencial"><span>${icone("map-pin")}Presencial</span></label>`;
const modoAtual = () => document.querySelector('input[name="modo"]:checked').value;

function sincronizarModo() {
    const online = modoAtual() === "Online";
    $("rotuloLocal").textContent = online ? "Link da reunião" : "Endereço ou sala";
    $("local").placeholder = online ? "https://meet.exemplo.com/abc-defg" : "Ex.: Bloco B, sala 204";
    $("dicaLocal").textContent = online ? "Cole o link completo, começando com https://" : "As sugestões mostram os locais já usados.";
    $("locais").textContent = "";
    for (const v of [...new Set(salas.filter((s) => s.tipo === modoAtual()).map((s) => s.localizacao_link || s.nome))].slice(0, 30)) {
        const o = document.createElement("option"); o.value = v; $("locais").appendChild(o);
    }
}
document.querySelectorAll('input[name="modo"]').forEach((r) => r.addEventListener("change", sincronizarModo));

// primeira data real da série (o primeiro dia da semana escolhido a partir de "A partir de")
function primeiraData() {
    if (!$("dataIni").value) return null;
    const d = deChave($("dataIni").value);
    const alvo = Number($("dia").value);
    while ((d.getDay() + 6) % 7 !== alvo) d.setDate(d.getDate() + 1);
    return d;
}

function atualizarResumo() {
    const p = primeiraData();
    const ini = $("horaIni").value, fim = $("horaFim").value;
    if (!p || !ini || !fim || fim <= ini) { $("resumoFixa").textContent = ""; return; }
    const min = minutosEntre(juntarDataHora(chaveDia(p), ini), juntarDataHora(chaveDia(p), fim));
    $("resumoFixa").textContent = `Toda ${DIAS_SEMANA[Number($("dia").value)].toLowerCase()}, das ${ini} às ${fim} (${duracaoTexto(min)}). Primeira em ${dataCurta(p)}.`;
}
["dia", "horaIni", "horaFim", "dataIni", "dataFim"].forEach((id) => $(id).addEventListener("change", atualizarResumo));

function cartaoFixa(f, porSala) {
    const sala = porSala[f.id_sala] || null;
    const ini = f.hora_inicio.slice(0, 5), fim = f.hora_fim.slice(0, 5);
    const min = minutosEntre(juntarDataHora(hoje, ini), juntarDataHora(hoje, fim));
    const ate = f.data_fim ? ` até ${f.data_fim.split("-").reverse().join("/")}` : ", sem data para acabar";
    return `<article class="ag ag-reuniao" data-id="${Number(f.id_fixa)}">
        <div class="ag-hora" aria-label="Das ${ini} às ${fim}"><small>${esc(DIAS_SEMANA[f.dia_semana].slice(0, 3).toLowerCase())}</small><b>${ini}</b><span>${fim}</span></div>
        <div class="ag-corpo">
            <p class="ag-tipo">${icone("repeat", "ic ponto-ic")}Toda ${esc(DIAS_SEMANA[f.dia_semana].toLowerCase())}</p>
            <h3>${esc(f.titulo)}</h3>
            <p class="ag-meta">${icone(sala && sala.tipo === "Presencial" ? "map-pin" : "video-camera")}<span class="ag-local">${localHtml(sala)}</span></p>
            <p class="ag-meta suave">${icone("hourglass-medium")}<span>${duracaoTexto(min)} · desde ${f.data_inicio.split("-").reverse().join("/")}${esc(ate)}</span></p>
        </div>
        <div class="ag-acoes"><button class="icone-btn perigo" type="button" data-cancelar aria-label="Cancelar série ${esc(f.titulo)}">${icone("trash")}</button></div>
    </article>`;
}

async function carregar() {
    try {
        const [fixas, s] = await Promise.all([api("/reunioes-fixas?id_usuario=" + encodeURIComponent(usuario.id_usuario)), api("/salas")]);
        salas = s;
        sincronizarModo();
        const porSala = Object.fromEntries(salas.map((x) => [x.id_sala, x]));
        $("lista").innerHTML = fixas.length
            ? fixas.map((f) => cartaoFixa(f, porSala)).join("")
            : estadoVazio("Nenhuma reunião fixa", "Crie uma série para a daily, a reunião semanal da equipe ou a monitoria.");
    } catch (e) {
        $("lista").innerHTML = estadoErro(e.message);
    }
}

$("formFixa").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (enviando) return;
    const msg = $("msgErro");
    msg.className = "msg";
    msg.textContent = "";
    const titulo = $("titulo").value.trim(), local = $("local").value.trim();
    const falha = (texto, campo) => { msg.textContent = texto; if (campo) $(campo).focus(); };
    if (!titulo) return falha("Dê um nome para a reunião fixa.", "titulo");
    if (!$("horaIni").value || !$("horaFim").value) return falha("Informe o início e o fim.", "horaIni");
    if ($("horaFim").value <= $("horaIni").value) return falha("O fim precisa ser depois do início.", "horaFim");
    if (!$("dataIni").value || $("dataIni").value < hoje) return falha("A série não pode começar em um dia que já passou.", "dataIni");
    if ($("dataFim").value && $("dataFim").value < $("dataIni").value) return falha("A data final não pode ser antes da inicial.", "dataFim");
    if (!local) return falha("Informe onde vai ser.", "local");
    if (modoAtual() === "Online" && !urlSegura(local)) return falha("Para reunião online, use um link completo começando com https://", "local");

    enviando = true;
    ocupado($("btnSalvar"), true, "Criando…");
    try {
        const sala = await obterSala(modoAtual(), local, salas);
        const r = await api("/reunioes-fixas", {
            method: "POST",
            body: {
                id_sala: sala.id_sala, titulo, descricao: null,
                dia_semana: Number($("dia").value),
                hora_inicio: $("horaIni").value + ":00", hora_fim: $("horaFim").value + ":00",
                data_inicio: $("dataIni").value, data_fim: $("dataFim").value || null,
            },
        });
        const ign = r.datas_ignoradas.length;
        avisar(`Série criada: ${r.reunioes_criadas} reunião(ões) marcada(s).`);
        if (ign) {
            msg.className = "msg";
            msg.textContent = `${ign} data(s) ficaram de fora porque o local já estava ocupado: ${r.datas_ignoradas.map((d) => d.split("-").reverse().slice(0, 2).join("/")).join(", ")}.`;
        }
        $("titulo").value = "";
        carregar();
    } catch (err) {
        msg.textContent = err.message;
    } finally {
        enviando = false;
        ocupado($("btnSalvar"), false);
    }
});

$("lista").addEventListener("click", async (ev) => {
    const b = ev.target.closest("[data-cancelar]");
    if (!b) return;
    const card = b.closest(".ag");
    const sim = await confirmar({
        titulo: "Cancelar esta reunião fixa?",
        texto: `"${card.querySelector("h3").textContent}" deixa de se repetir e as próximas reuniões dela são apagadas. Isso não pode ser desfeito.`,
        ok: "Cancelar série", cancelar: "Manter", perigo: true,
    });
    if (!sim) return;
    ocupado(b, true);
    try {
        await api("/reunioes-fixas/" + Number(card.dataset.id), { method: "DELETE" });
        avisar("Reunião fixa cancelada.");
        carregar();
    } catch (e) {
        avisar(e.message, "erro");
        ocupado(b, false);
    }
});

sincronizarModo();
atualizarResumo();
carregar();
