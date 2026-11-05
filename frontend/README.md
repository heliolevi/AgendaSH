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

## O que já existe
- `login.html`: entra com **e-mail** + senha (`POST /auth/login`) e guarda o usuário no `localStorage`
- `cadastro.html`: cria usuário (`POST /usuarios`)
- `esqueciSenha.html`: só o layout (sem rota na API ainda)
- `index.html`: home provisória, protegida (volta ao login se não houver usuário) com botão Sair

## Estrutura de módulos (espelha o backend)
```
src/
├── core/api.js              # cliente HTTP + usuarioLogado()
├── shared/                  # componentes/utilitários reutilizáveis
└── modules/
    ├── auth/services/auth.js
    ├── usuarios/  salas/  reunioes/  convites/
        ├── components/  pages/  services/
```
Regra: um módulo não importa de outro; o que for comum vai para `shared/`. Próximos passos em `docs/TASKS.md`.
