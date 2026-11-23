// Agenda: tudo que vem pela frente (reuniões + eventos), agrupado por dia, com filtro, editar e cancelar.
const usuario = exigirLogin();
$("avatar").innerHTML = avatarHtml(usuario);
renderNav("reunioes");
$("linkFixas").insertAdjacentHTML("afterbegin", icone("repeat"));

let itens = [];
const filtroInicial = new URLSearchParams(location.search).get("filtro");
let filtro = ["reuniao", "evento"].includes(filtroInicial) ? filtroInicial : "todos";

function desenhar() {
    document.querySelectorAll("#filtros [data-filtro]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.filtro === filtro)));
    const visiveis = itens.filter((x) => filtro === "todos" || x.tipo === filtro);
    if (!visiveis.length) {
        const nome = filtro === "evento" ? "eventos" : filtro === "reuniao" ? "reuniões" : "compromissos";
        const titulo = filtro === "reuniao" ? "Nenhuma reunião pela frente" : filtro === "evento" ? "Nenhum evento pela frente" : "Nada marcado pela frente";
        $("lista").innerHTML = estadoVazio(titulo,
            `Quando houver ${nome} marcados, eles aparecem aqui separados por dia.`, "calendario.html#novo", "Agendar");
        return;
    }
    $("lista").innerHTML = agruparPorDia(visiveis).map(([k, xs]) => {
        const d = deChave(k);
        const rot = rotuloDia(d);
        return `<section class="dia-grupo" aria-label="${esc(dataLonga(d))}">
            <h3>${esc(rot)}<span>${["Hoje", "Amanhã"].includes(rot) ? dataLonga(d) : xs.length + (xs.length > 1 ? " compromissos" : " compromisso")}</span></h3>
            <div class="lista">${xs.map((x) => cartaoAgenda(x, { acoes: true })).join("")}</div>
        </section>`;
    }).join("");
}

async function carregar() {
    try {
        const { minhas } = await carregarAgenda(usuario);
        const agora = new Date();
        itens = minhas.filter((x) => x.fim > agora);
        desenhar();
    } catch (e) {
        $("lista").innerHTML = estadoErro(e.message);
    }
}

$("filtros").addEventListener("click", (e) => {
    const b = e.target.closest("[data-filtro]");
    if (!b) return;
    filtro = b.dataset.filtro;
    history.replaceState(null, "", filtro === "todos" ? "reunioes.html" : "reunioes.html?filtro=" + filtro);
    desenhar();
});
$("filtros").addEventListener("keydown", (e) => { // setas trocam a aba (padrão de tablist)
    if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    const abas = [...document.querySelectorAll("#filtros [data-filtro]")];
    const i = abas.findIndex((b) => b.dataset.filtro === filtro);
    const prox = abas[(i + (e.key === "ArrowRight" ? 1 : abas.length - 1)) % abas.length];
    prox.focus();
    prox.click();
});
$("lista").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-excluir]");
    if (b && (await excluirDoCartao(b))) carregar();
});

carregar();
