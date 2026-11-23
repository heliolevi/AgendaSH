// Login, cadastro (com código por e-mail) e recuperação de senha.
// As checagens aqui só dão resposta rápida; quem decide de verdade é o backend.
const msg = document.getElementById("msgErro");
const el = (id) => document.getElementById(id);

function carregandoBtn(btn, sim, rotulo) {
    if (!btn) return;
    if (sim) {
        btn.dataset.rotulo = btn.textContent;
        btn.disabled = true;
        btn.classList.add("carregando");
        btn.setAttribute("aria-busy", "true");
        if (rotulo) btn.textContent = rotulo;
    } else {
        btn.disabled = false;
        btn.classList.remove("carregando");
        btn.removeAttribute("aria-busy");
        if (btn.dataset.rotulo) btn.textContent = btn.dataset.rotulo;
    }
}

function erro(texto, campo) {
    msg.className = "msg";
    msg.textContent = texto;
    if (campo) { campo.setAttribute("aria-invalid", "true"); campo.focus(); }
}
function sucesso(texto) {
    msg.className = "msg ok";
    msg.textContent = texto;
}
document.addEventListener("input", (e) => { if (e.target.matches("input")) e.target.removeAttribute("aria-invalid"); });

// Já logado? Não faz sentido ver login/cadastro.
if ((el("formLogin") || el("formCadastro")) && usuarioLogado() && getToken()) location.replace("index.html");

// Mostrar/ocultar senha (qualquer tela com .ver-senha + aria-controls)
document.querySelectorAll(".ver-senha").forEach((b) => {
    const alvo = el(b.getAttribute("aria-controls"));
    if (!alvo) return;
    b.addEventListener("click", () => {
        const mostrar = alvo.type === "password";
        alvo.type = mostrar ? "text" : "password";
        b.setAttribute("aria-pressed", String(mostrar));
        b.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
        alvo.focus();
    });
});

const EMAIL_ALUNO = /^002-02\d{1,10}@aluno\.undb\.edu\.br$/;
const EMAIL_PROFESSOR = /^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*@undb\.edu\.br$/;
function emailUndbValido(email) {
    const e = email.trim().toLowerCase();
    return EMAIL_ALUNO.test(e) || EMAIL_PROFESSOR.test(e);
}
const MSG_EMAIL_UNDB = "Use seu e-mail institucional da UNDB (002-02…@aluno.undb.edu.br ou nome@undb.edu.br).";

// ------------------------------------------------------------ login
const formLogin = el("formLogin");
if (formLogin) {
    if (new URLSearchParams(location.search).get("expirou")) erro("Sua sessão expirou. Entre de novo para continuar.");
    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const emailEl = el("loginUsuario"), senhaEl = el("loginSenha"), btn = el("btnLogin");
        const email = emailEl.value.trim().toLowerCase();
        if (!email) return erro("Informe seu e-mail.", emailEl);
        if (!senhaEl.value) return erro("Informe sua senha.", senhaEl);
        msg.textContent = "";
        carregandoBtn(btn, true, "Entrando…");
        try {
            const resp = await api("/auth/login", { method: "POST", body: { email, senha: senhaEl.value } });
            setSessao(resp.access_token, resp.usuario);
            location.replace("index.html");
        } catch (err) {
            // a mensagem não diz se errou o e-mail ou a senha (o backend responde igual): evita descobrir contas
            erro(err.status === 429 ? "Muitas tentativas. Espere um pouco e tente de novo." : err.message);
            senhaEl.value = "";
            senhaEl.focus();
            carregandoBtn(btn, false);
        }
    });
}

// ------------------------------------------------------------ força da senha (cadastro)
function forcaSenha(s) {
    let p = 0;
    if (s.length >= 6) p++;
    if (s.length >= 10) p++;
    if (/[a-z]/.test(s) && /[A-Z]/.test(s)) p++;
    if (/\d/.test(s)) p++;
    if (/[^A-Za-z0-9]/.test(s)) p++;
    if (/^(.)\1+$/.test(s) || /^(123456|senha|password|qwerty|undb)/i.test(s)) p = 0;
    return Math.min(p, 4);
}
const barraForca = el("forcaBarra");
if (barraForca) {
    const niveis = [["muito fraca", "#ff8fa3"], ["fraca", "#ff8fa3"], ["razoável", "#fcd34d"], ["boa", "#6ee7a8"], ["forte", "#22d3ee"]];
    el("cadSenha").addEventListener("input", (e) => {
        const v = e.target.value;
        const n = v ? forcaSenha(v) : 0;
        barraForca.style.width = v ? (n + 1) * 20 + "%" : "0";
        barraForca.style.background = niveis[n][1];
        el("forcaTexto").textContent = v ? `Senha ${niveis[n][0]}. Use 8+ caracteres misturando letras, números e símbolos.` : "Use 8+ caracteres misturando letras, números e símbolos.";
    });
}

// ------------------------------------------------------------ cadastro
const formCadastro = el("formCadastro");
if (formCadastro) {
    formCadastro.addEventListener("submit", async (e) => {
        e.preventDefault();
        const nomeEl = el("cadUsuario"), emailEl = el("cadEmail"), codEl = el("cadCodigo"), senhaEl = el("cadSenha");
        const nome = nomeEl.value.trim(), email = emailEl.value.trim().toLowerCase(), codigo = codEl.value.trim(), senha = senhaEl.value;
        if (!nome) return erro("Informe seu nome.", nomeEl);
        if (!email) return erro("Informe seu e-mail.", emailEl);
        if (!emailUndbValido(email)) return erro(MSG_EMAIL_UNDB, emailEl);
        if (!/^\d{6}$/.test(codigo)) return erro("Digite o código de 6 dígitos enviado ao seu e-mail.", codEl);
        if (senha.length < 6) return erro("A senha precisa de no mínimo 6 caracteres.", senhaEl);
        if (forcaSenha(senha) === 0) return erro("Essa senha é fácil demais de adivinhar. Escolha outra.", senhaEl);
        msg.textContent = "";
        const btn = el("btnCriar");
        carregandoBtn(btn, true, "Criando conta…");
        try {
            await api("/usuarios", { method: "POST", body: { nome, email, senha, codigo } });
            const resp = await api("/auth/login", { method: "POST", body: { email, senha } }); // já entra direto
            setSessao(resp.access_token, resp.usuario);
            location.replace("index.html");
        } catch (err) {
            erro(err.message);
            carregandoBtn(btn, false);
        }
    });

    // código por e-mail (o servidor também limita: 1 por minuto)
    const btnCodigo = el("btnEnviarCodigo");
    btnCodigo.addEventListener("click", async () => {
        const emailEl = el("cadEmail");
        const email = emailEl.value.trim().toLowerCase();
        if (!email) return erro("Informe seu e-mail primeiro.", emailEl);
        if (!emailUndbValido(email)) return erro(MSG_EMAIL_UNDB, emailEl);
        msg.textContent = "";
        carregandoBtn(btnCodigo, true, "Enviando…");
        try {
            const r = await api("/auth/cadastro/enviar-codigo", { method: "POST", body: { email } });
            sucesso(`${r.detail} Vale por ${r.expira_em_minutos} minutos.`);
            el("cadCodigo").focus();
            contagem(btnCodigo, "Reenviar");
        } catch (err) {
            erro(err.message);
            carregandoBtn(btnCodigo, false);
        }
    });
}

function contagem(botao, rotulo, segundos = 60) {
    botao.classList.remove("carregando");
    botao.removeAttribute("aria-busy");
    botao.disabled = true;
    let restante = segundos;
    botao.textContent = `${rotulo} (${restante}s)`;
    const t = setInterval(() => {
        restante -= 1;
        if (restante <= 0) {
            clearInterval(t);
            botao.disabled = false;
            botao.textContent = rotulo;
        } else botao.textContent = `${rotulo} (${restante}s)`;
    }, 1000);
}

// ------------------------------------------------------------ recuperar senha (2 etapas)
const formEsqueci = el("formEsqueci");
const formRecuperar = el("formRecuperar");
if (formEsqueci && formRecuperar) {
    let emailRecuperacao = "";
    async function pedirCodigo(email, btn) {
        carregandoBtn(btn, true, "Enviando…");
        try {
            const r = await api("/auth/esqueci-senha", { method: "POST", body: { email } });
            emailRecuperacao = email;
            formEsqueci.hidden = true;
            formRecuperar.hidden = false;
            el("passo2").classList.add("feito");
            el("subRec").textContent = `Digite o código enviado para ${email} e escolha a nova senha.`;
            sucesso(r.detail);
            el("recCodigo").focus();
            return true;
        } catch (err) {
            erro(err.message);
            return false;
        } finally {
            carregandoBtn(btn, false);
        }
    }

    formEsqueci.addEventListener("submit", async (e) => {
        e.preventDefault();
        const emailEl = el("recEmail");
        const email = emailEl.value.trim().toLowerCase();
        if (!email) return erro("Informe seu e-mail.", emailEl);
        await pedirCodigo(email, el("btnPedir"));
    });

    el("linkReenviar").addEventListener("click", async (e) => {
        const b = e.currentTarget;
        if (await pedirCodigo(emailRecuperacao, b)) contagem(b, "Reenviar código");
    });

    formRecuperar.addEventListener("submit", async (e) => {
        e.preventDefault();
        const codEl = el("recCodigo"), novaEl = el("recSenha"), confEl = el("recConfirma");
        if (!/^\d{6}$/.test(codEl.value.trim())) return erro("Digite o código de 6 dígitos enviado ao seu e-mail.", codEl);
        if (novaEl.value.length < 6) return erro("A senha precisa de no mínimo 6 caracteres.", novaEl);
        if (novaEl.value !== confEl.value) return erro("As senhas não conferem.", confEl);
        const btn = el("btnRedefinir");
        carregandoBtn(btn, true, "Salvando…");
        try {
            const r = await api("/auth/redefinir-senha", { method: "POST", body: { email: emailRecuperacao, codigo: codEl.value.trim(), nova_senha: novaEl.value } });
            sucesso(r.detail);
            setTimeout(() => location.replace("login.html"), 1500);
        } catch (err) {
            erro(err.message);
            carregandoBtn(btn, false);
        }
    });
}
