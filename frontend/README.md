# Frontend AgendaSH

HTML, CSS e JavaScript puro (sem build). Funciona em celular, tablet e PC.

## Rodar
```
# terminal 1: API (ver backend/README.md)
cd backend && uvicorn app.main:app --reload
# terminal 2: front
cd frontend && python -m http.server 5500
```
Abrir http://localhost:5500/login.html.

## Telas
| Arquivo | O que faz |
|---|---|
| `welcome.html`, `login.html`, `cadastro.html`, `esqueciSenha.html` | Entrada. No PC, login/cadastro/recuperar ficam em duas colunas (marca + formulário) |
| `index.html` | Início: próximo compromisso com contagem regressiva, régua de hoje e os próximos 7 dias agrupados por dia |
| `calendario.html` | Agendar e **editar** reunião ou evento com **início e fim**. Atalhos de duração, régua do dia, aviso de conflito de local antes de enviar. Evento pode terminar em outro dia |
| `reunioes.html` | Agenda: tudo que vem pela frente, por dia, com filtro Tudo / Reuniões / Eventos, editar e cancelar |
| `reunioesFixas.html` | Séries semanais (`/reunioes-fixas`) |
| `perfil.html`, `admin.html`, `termos.html`, `404.html` | Conta, painel admin, termos, página não encontrada |

Editar um compromisso: `calendario.html?editar=reuniao-12` ou `?editar=evento-3` (o botão de lápis dos cartões já faz isso).

## Responsivo
- **Celular (base):** uma coluna, barra inferior com os símbolos △ □ + × ○.
- **Tablet (≥ 768px):** mais espaço, mesma barra inferior.
- **PC (≥ 1024px):** barra lateral fixa com "Novo agendamento"; Calendário em duas colunas (calendário + dia à esquerda, formulário à direita); Início com a lista à esquerda e o resumo de hoje à direita.

## Estrutura
```
src/
├── core/api.js              # cliente HTTP, token (expira sozinho), anti-iframe
├── shared/app.js            # guarda de login, navegação, dados da agenda, cartão, régua, diálogo, avisos
├── shared/icones.js         # ícones Phosphor (MIT) embutidos
├── shared/efeitos.js        # animação de entrada opcional (GSAP local)
├── shared/cookies.js
└── modules/
    ├── auth/services/auth.js        # login, cadastro, recuperar senha
    ├── auth/pages/welcome.js, termos.js
    ├── reunioes/pages/inicio.js, calendario.js, agenda.js, fixas.js
    ├── usuarios/pages/perfil.js
    └── admin/admin.js
```
Regra: telas não importam umas das outras; o que é comum vai para `shared/`.

## Segurança (o que o front faz)
- **CSP em toda página** (`<meta http-equiv="Content-Security-Policy">`): só roda script deste site, sem script nem estilo inline, só conversa com a API. Por isso **não existe `<script>` com código dentro do HTML nem `style="..."`**: todo código fica em `src/`.
- **Ao publicar a API em outro endereço**, troque `API_URL` em `src/core/api.js` **e** o `connect-src` da meta CSP em todas as páginas.
- `frame-ancestors` não funciona em meta tag, então `api.js` se recusa a rodar dentro de iframe (anti-clickjacking). Em produção, o servidor que entrega o front deve mandar `Content-Security-Policy: frame-ancestors 'none'`.
- Token: se expirou, a sessão é limpa antes de chamar a API; `401` leva ao login com aviso "sessão expirou".
- O que fica no navegador: só o token e `{id_usuario, nome, email, criado_em, papel}`. O menu de admin depende do papel **do token** (assinado), não do perfil salvo. Quem barra de verdade é sempre o backend.
- Todo texto vindo da API passa por `esc()`. Links de reunião só viram `<a>` se forem `http(s)`, com `rel="noopener noreferrer"`; `javascript:` e afins aparecem como texto.
- `fetch` sem cookies (`credentials: "omit"`), sem cache, sem seguir redirecionamento, com tempo limite de 15 s.
- Botões ficam bloqueados enquanto enviam (sem clique duplo); confirmação acessível antes de cancelar/excluir.

## Design
Tokens, componentes e decisões em [`docs/FRONTEND_DESIGN.md`](../docs/FRONTEND_DESIGN.md).
