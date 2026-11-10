const msg = document.getElementById("msgErro");

const formLogin = document.getElementById("formLogin");
if (formLogin) formLogin.addEventListener("submit", entrar);

async function entrar(e) {
    e.preventDefault();
    msg.textContent = "";
    try {
        const usuario = await api("/auth/login", {
            method: "POST",
            body: {
                email: document.getElementById("loginUsuario").value.trim(),
                senha: document.getElementById("loginSenha").value,
            },
        });
        localStorage.setItem("usuario", JSON.stringify(usuario));
        location.href = "index.html";
    } catch (erro) {
        msg.textContent = erro.message;
    }
}

// Pré-checagem só para dar resposta rápida; quem decide de verdade é o backend (backend/app/core/email_policy.py).
const EMAIL_ALUNO = /^002-02\d{1,10}@aluno\.undb\.edu\.br$/;
const EMAIL_PROFESSOR = /^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*@undb\.edu\.br$/;
function emailUndbValido(email) {
    const e = email.trim().toLowerCase();
    return EMAIL_ALUNO.test(e) || EMAIL_PROFESSOR.test(e);
}

const formCadastro = document.getElementById("formCadastro");
if (formCadastro) {
    formCadastro.addEventListener("submit", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        const nome = document.getElementById("cadUsuario").value.trim();
        const email = document.getElementById("cadEmail").value.trim();
        const senha = document.getElementById("cadSenha").value;
        if (!nome) return (msg.textContent = "Informe seu nome");
        if (!email) return (msg.textContent = "Informe seu e-mail");
        if (!emailUndbValido(email)) return (msg.textContent = "Use seu e-mail institucional da UNDB (002-02…@aluno.undb.edu.br ou nome@undb.edu.br).");
        if (senha.length < 6) return (msg.textContent = "Senha precisa de no mínimo 6 caracteres");
        try {
            await api("/usuarios", { method: "POST", body: { nome, email: email.toLowerCase(), senha } });
            // já entra direto após criar a conta
            const usuario = await api("/auth/login", { method: "POST", body: { email, senha } });
            localStorage.setItem("usuario", JSON.stringify(usuario));
            location.href = "index.html";
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });
}

// Recuperar senha: etapa 1 pede o link por e-mail; etapa 2 (abre com ?token=...) grava a nova senha.
const formEsqueci = document.getElementById("formEsqueci");
const formRecuperar = document.getElementById("formRecuperar");
if (formEsqueci && formRecuperar) {
    const token = new URLSearchParams(location.search).get("token");
    formEsqueci.style.display = token ? "none" : "";
    formRecuperar.style.display = token ? "" : "none";

    formEsqueci.addEventListener("submit", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        const email = document.getElementById("recEmail").value.trim();
        if (!email) return (msg.textContent = "Informe seu e-mail");
        try {
            const r = await api("/auth/esqueci-senha", { method: "POST", body: { email } });
            msg.textContent = r.detail;
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });

    formRecuperar.addEventListener("submit", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        const nova = document.getElementById("recSenha").value;
        if (nova.length < 6) return (msg.textContent = "Senha precisa de no mínimo 6 caracteres");
        if (nova !== document.getElementById("recConfirma").value) return (msg.textContent = "As senhas não conferem");
        try {
            const r = await api("/auth/redefinir-senha", { method: "POST", body: { token, nova_senha: nova } });
            msg.textContent = r.detail;
            setTimeout(() => (location.href = "login.html"), 1500);
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });
}
