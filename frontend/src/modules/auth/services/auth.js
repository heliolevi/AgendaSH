const msg = document.getElementById("msgErro");

const formLogin = document.getElementById("formLogin");
if (formLogin) formLogin.addEventListener("submit", entrar);

async function entrar(e) {
    e.preventDefault();
    msg.textContent = "";
    const emailEl = document.getElementById("loginUsuario");
    const senhaEl = document.getElementById("loginSenha");
    const btn = document.getElementById("btnLogin");
    const email = emailEl.value.trim();
    // erro perto do campo e foco nele (sem ida ao servidor à toa)
    if (!email) { msg.textContent = "Informe seu e-mail."; emailEl.focus(); return; }
    if (!senhaEl.value) { msg.textContent = "Informe sua senha."; senhaEl.focus(); return; }

    const rotulo = btn ? btn.textContent : "";
    if (btn) { btn.disabled = true; btn.classList.add("carregando"); btn.textContent = "Entrando…"; }
    try {
        const resp = await api("/auth/login", { method: "POST", body: { email, senha: senhaEl.value } });
        setSessao(resp.access_token, resp.usuario);
        location.href = "index.html";
    } catch (erro) {
        msg.textContent = erro.message;
        if (btn) { btn.disabled = false; btn.classList.remove("carregando"); btn.textContent = rotulo; }
    }
}

// Mostrar/ocultar senha (qualquer tela com .ver-senha + aria-controls)
document.querySelectorAll(".ver-senha").forEach((b) => {
    const alvo = document.getElementById(b.getAttribute("aria-controls"));
    if (!alvo) return;
    b.addEventListener("click", () => {
        const mostrar = alvo.type === "password";
        alvo.type = mostrar ? "text" : "password";
        b.setAttribute("aria-pressed", String(mostrar));
        b.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
        alvo.focus();
    });
});

// Pre-checagem so para dar resposta rapida; quem decide de verdade e o backend (backend/app/core/email_policy.py).
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
        const codigo = document.getElementById("cadCodigo").value.trim();
        if (!nome) return (msg.textContent = "Informe seu nome");
        if (!email) return (msg.textContent = "Informe seu e-mail");
        if (!emailUndbValido(email)) return (msg.textContent = "Use seu e-mail institucional da UNDB (002-02...@aluno.undb.edu.br ou nome@undb.edu.br).");
        if (!/^\d{6}$/.test(codigo)) return (msg.textContent = "Digite o codigo de 6 digitos enviado ao seu e-mail");
        if (senha.length < 6) return (msg.textContent = "Senha precisa de no minimo 6 caracteres");
        try {
            await api("/usuarios", { method: "POST", body: { nome, email: email.toLowerCase(), senha, codigo } });
            // ja entra direto apos criar a conta
            const resp = await api("/auth/login", { method: "POST", body: { email, senha } });
            setSessao(resp.access_token, resp.usuario);
            location.href = "index.html";
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });
}

// Espera entre pedidos de codigo (o servidor tambem limita: 1 por minuto).
function contagem(botao, rotulo, segundos = 60) {
    botao.disabled = true;
    let restante = segundos;
    const t = setInterval(() => {
        restante -= 1;
        if (restante <= 0) {
            clearInterval(t);
            botao.disabled = false;
            botao.textContent = rotulo;
        } else botao.textContent = `${rotulo} (${restante}s)`;
    }, 1000);
}

// Cadastro: botao que envia o codigo para o e-mail institucional.
const btnEnviarCodigo = document.getElementById("btnEnviarCodigo");
if (btnEnviarCodigo) {
    const rotulo = btnEnviarCodigo.textContent;
    btnEnviarCodigo.addEventListener("click", async () => {
        msg.textContent = "";
        const email = document.getElementById("cadEmail").value.trim();
        if (!email) return (msg.textContent = "Informe seu e-mail");
        if (!emailUndbValido(email)) return (msg.textContent = "Use seu e-mail institucional da UNDB (002-02...@aluno.undb.edu.br ou nome@undb.edu.br).");
        btnEnviarCodigo.disabled = true;
        btnEnviarCodigo.textContent = "Enviando...";
        try {
            const r = await api("/auth/cadastro/enviar-codigo", { method: "POST", body: { email: email.toLowerCase() } });
            msg.textContent = `${r.detail} Vale por ${r.expira_em_minutos} minutos.`;
            contagem(btnEnviarCodigo, rotulo);
        } catch (erro) {
            msg.textContent = erro.message;
            btnEnviarCodigo.disabled = false;
            btnEnviarCodigo.textContent = rotulo;
        }
    });
}

// Recuperar senha: etapa 1 pede o codigo por e-mail; etapa 2 confere o codigo e grava a nova senha.
const formEsqueci = document.getElementById("formEsqueci");
const formRecuperar = document.getElementById("formRecuperar");
if (formEsqueci && formRecuperar) {
    let emailRecuperacao = "";
    async function pedirCodigo(email) {
        const r = await api("/auth/esqueci-senha", { method: "POST", body: { email } });
        emailRecuperacao = email;
        formEsqueci.style.display = "none";
        formRecuperar.style.display = "";
        msg.textContent = r.detail;
    }

    formEsqueci.addEventListener("submit", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        const email = document.getElementById("recEmail").value.trim().toLowerCase();
        if (!email) return (msg.textContent = "Informe seu e-mail");
        try {
            await pedirCodigo(email);
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });

    document.getElementById("linkReenviar").addEventListener("click", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        try {
            await pedirCodigo(emailRecuperacao);
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });

    formRecuperar.addEventListener("submit", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        const codigo = document.getElementById("recCodigo").value.trim();
        const nova = document.getElementById("recSenha").value;
        if (!/^\d{6}$/.test(codigo)) return (msg.textContent = "Digite o codigo de 6 digitos enviado ao seu e-mail");
        if (nova.length < 6) return (msg.textContent = "Senha precisa de no minimo 6 caracteres");
        if (nova !== document.getElementById("recConfirma").value) return (msg.textContent = "As senhas nao conferem");
        try {
            const r = await api("/auth/redefinir-senha", { method: "POST", body: { email: emailRecuperacao, codigo, nova_senha: nova } });
            msg.textContent = r.detail;
            setTimeout(() => (location.href = "login.html"), 1500);
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });
}
