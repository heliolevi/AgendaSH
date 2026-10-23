# Frontend AgendaSH

Uso interno. Um único código responsivo (desktop + mobile). Sugestão: **React + Vite** (PWA para "instalar" no celular).
O time pode trocar a tecnologia, mas **mantenha a estrutura de módulos** abaixo, que espelha o backend.

```
src/
├── core/        # roteador, cliente HTTP (base URL da API), contexto de auth, layout base
├── shared/      # componentes reutilizáveis (Button, Modal, Table, DateTimePicker), hooks, utils
└── modules/
    ├── auth/        # login
    ├── usuarios/    # CRUD de usuários
    ├── salas/       # CRUD de salas
    ├── reunioes/    # agenda/calendário + CRUD de reuniões
    └── convites/    # convidar participantes, aceitar/recusar
        ├── components/   # peças do módulo
        ├── pages/        # telas (rotas)
        └── services/     # chamadas à API deste módulo
```

Regra: um módulo **não importa** de outro módulo; o que for comum vai para `shared/`.
API: `http://localhost:8000` (docs interativas em `/docs`). Veja `docs/TASKS.md`.
