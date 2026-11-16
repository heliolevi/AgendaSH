const u = exigirLogin();
document.getElementById("avatar").innerHTML = avatarHtml(u);
renderNav("perfil");

const $ = (id) => document.getElementById(id);
const erro = (e) => ($("msgErro").textContent = e.message);

if (!ehAdmin()) {
    $("bloqueado").hidden = false;
} else {
    $("conteudo").hidden = false;
    carregar();
}

async function carregar() {
    try {
        const [resumo, usuarios] = await Promise.all([api("/admin/resumo"), api("/admin/usuarios")]);
        $("resumo").innerHTML = [
            ["Usuarios", resumo.usuarios],
            ["Reunioes", resumo.reunioes],
            ["Salas", resumo.salas],
            ["Convites", resumo.convites],
        ].map(([r, n]) => `<div class="admin-card"><b>${n}</b><span>${r}</span></div>`).join("");

        $("listaUsuarios").innerHTML = usuarios.length
            ? usuarios.map(cartaoUsuario).join("")
            : '<p class="vazio">Nenhum usuario.</p>';
    } catch (e) {
        erro(e);
    }
}

function cartaoUsuario(us) {
    const admin = us.papel === "admin";
    const souEu = us.id_usuario === u.id_usuario;
    return `<div class="admin-user" data-id="${us.id_usuario}">
        <div class="admin-user-info">
            <h3>${esc(us.nome)} ${admin ? '<span class="selo">admin</span>' : ""}</h3>
            <div class="linha">${esc(us.email)}</div>
        </div>
        <div class="admin-user-acoes">
            <button class="mini" data-acao="papel" data-papel="${admin ? "membro" : "admin"}" ${souEu ? "disabled title='Voce'" : ""}>
                ${admin ? "Tornar membro" : "Tornar admin"}
            </button>
            <button class="mini perigo" data-acao="remover" ${souEu ? "disabled" : ""}>Excluir</button>
        </div>
    </div>`;
}

$("listaUsuarios").addEventListener("click", async (ev) => {
    const b = ev.target.closest("button[data-acao]");
    if (!b || b.disabled) return;
    const card = b.closest(".admin-user");
    const id = card.dataset.id;
    $("msgErro").className = "msg";
    $("msgErro").textContent = "";
    try {
        if (b.dataset.acao === "papel") {
            await api("/admin/usuarios/" + id, { method: "PATCH", body: { papel: b.dataset.papel } });
        } else {
            if (!confirm("Excluir este usuario? Esta acao nao pode ser desfeita.")) return;
            await api("/admin/usuarios/" + id, { method: "DELETE" });
        }
        carregar();
    } catch (e) {
        erro(e);
    }
});
