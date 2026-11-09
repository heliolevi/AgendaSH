# Frontend AgendaSH

Telas criadas pela equipe (branch `login_html`, visual roxo em `style.css`) + ligação básica com a API.
Mantenha esse visual nas próximas telas. HTML/CSS/JS puro por enquanto; a equipe pode adotar um framework depois.

## Rodar
```
# terminal 1: API (ver backend/README.md)
cd backend && uvicorn app.main:app --reload
# terminal 2: front
cd frontend && python -m http.server 5500
```
Abrir http://localhost:5500/login.html (a URL da API fica em `src/core/api.js`).

## O que já existe (MVP, baseado no protótipo mobile)
- `welcome.html`: tela inicial (Criar conta / Entrar)
- `cadastro.html` (`POST /usuarios`, já entra logado) · `login.html` (`POST /auth/login`)
- `esqueciSenha.html`: só o layout (a API ainda não tem rota de recuperação)
- `index.html`: home com próximas reuniões (organizadas por você ou com convite)
- `calendario.html`: calendário mensal + agendar (horário, modo, nome, local). Modo+Local viram uma `sala` (reaproveita ou cria); duração fixa de 1h; erro 409 de conflito é exibido
- `reunioes.html`: lista de reuniões com cancelar (só organizador)
- `perfil.html`: dados do usuário, editar perfil (`PUT /usuarios/{id}`), sair
- Logo: `BOTTOM_SH.png` (ícone oficial da SH, usado nas telas de entrada)

## Estrutura de módulos (espelha o backend)
```
src/
├── core/api.js              # cliente HTTP + usuarioLogado()
├── shared/app.js            # guarda de login, barra inferior, leitura de reuniões
├── shared/                  # componentes/utilitários reutilizáveis
└── modules/
    ├── auth/services/auth.js
    ├── usuarios/  salas/  reunioes/  convites/
        ├── components/  pages/  services/
```
Regra: um módulo não importa de outro; o que for comum vai para `shared/`. Próximos passos em `docs/TASKS.md`.
