# Tasks AgendaSH

Estado atual: backend com CRUD básico dos 4 módulos funcionando contra o Neon (testado). Frontend só tem a estrutura de pastas.
Prioridade: **P0** = bloqueia o MVP, **P1** = MVP completo, **P2** = depois.

## Modelo de dados (já existe no Neon)
```
usuario (id_usuario PK, nome, email UNIQUE, senha_hash, criado_em)
sala    (id_sala PK, nome, capacidade, tipo, localizacao_link)
reuniao (id_reuniao PK, id_usuario FK=organizador, id_sala FK, titulo, descricao, data_inicio, data_fim, comeca_em)
convite (PK id_reuniao+id_usuario, status_resposta, data_hora)
```
Relações: usuário organiza N reuniões · sala recebe N reuniões · reunião tem N convites · usuário recebe N convites.

## Decisões de banco para o time validar (reunir 15 min)
1. `reuniao.comeca_em` (default `CURRENT_DATE`) duplica `data_inicio` e não é usada: remover ou definir o propósito.
2. `reuniao.id_usuario` e `id_sala` aceitam NULL: devem ser `NOT NULL`.
3. `convite.status_resposta` é texto livre: a API aceita `pendente|aceito|recusado`; criar `CHECK` no banco.
4. Conflito de horário hoje é checado na API (há brecha se duas requisições chegarem juntas): criar `EXCLUDE USING gist` (extensão `btree_gist`) em `(id_sala, tsrange(data_inicio, data_fim))`.
5. Não há perfil/permissão (admin x comum) nem exclusão lógica. Definir se o MVP precisa.
6. Datas sem fuso (`TIMESTAMP`). Se houver times em fusos diferentes, migrar para `TIMESTAMPTZ`.

## Back-end
| # | Task | Prio |
|---|---|---|
| B1 | Autenticação JWT: `/auth/login` devolver token; dependência `usuario_atual` | P0 |
| B2 | Proteger todas as rotas (exceto login/health); organizador da reunião = usuário logado (remover `id_usuario` do body) | P0 |
| B3 | Migrations versionadas (Alembic ou SQL numerado em `db/migrations`); hoje o schema está só em `config/dbConect.py` | P0 |
| B4 | Aplicar as decisões de banco acima (constraints, EXCLUDE) | P0 |
| B5 | Permissões: só o organizador edita/exclui a reunião; só o convidado responde o próprio convite | P1 |
| B6 | Criar reunião já com lista de convidados (uma única chamada, transação) | P1 |
| B7 | `GET /reunioes` com filtros por período, por usuário (organizada/convidado) e paginação | P1 |
| B8 | `GET /salas/{id}/disponibilidade?data=` (horários livres) | P1 |
| B9 | Validar e-mail (domínio da empresa) e política de senha; endpoint trocar senha | P1 |
| B10 | Testes automatizados (pytest) dos 5 módulos, com banco de teste separado | P1 |
| B11 | Troca de `allow_origins=["*"]` por origens reais; variáveis por ambiente; pool de conexões | P1 |
| B12 | Notificação por e-mail ao convidar/alterar/cancelar reunião | P2 |
| B13 | Reuniões recorrentes; link de videochamada automático | P2 |
| B14 | Deploy (backend + front) e CI | P2 |

## Front-end
| # | Task | Prio |
|---|---|---|
| F1 | Setup do projeto (Vite + roteador), cliente HTTP em `core/`, layout base responsivo (menu lateral no desktop, barra inferior no mobile) | P0 |
| F2 | Tela de login + guarda de rotas + guardar token (depende de B1) | P0 |
| F3 | Módulo **salas**: listagem, criar/editar, excluir | P1 |
| F4 | Módulo **usuarios**: listagem, criar/editar, excluir | P1 |
| F5 | Módulo **reunioes**: calendário (dia/semana/mês) com as reuniões por sala | P0 |
| F6 | Módulo **reunioes**: formulário de agendar (sala, data/hora, título, descrição) tratando erro 409 de conflito | P0 |
| F7 | Módulo **convites**: escolher participantes no formulário; tela "meus convites" com aceitar/recusar | P1 |
| F8 | Tela de detalhes da reunião (participantes e status de cada um) | P1 |
| F9 | Componentes compartilhados em `shared/`: Modal, Tabela, DateTimePicker, Toast de erro/sucesso, estados de loading/vazio | P1 |
| F10 | Filtros na agenda (por sala, por "minhas reuniões") | P1 |
| F11 | PWA (instalável no celular) e/ou empacotar desktop (Tauri/Electron) se realmente for necessário | P2 |
| F12 | Acessibilidade e testes de interface (Playwright) | P2 |

## Ordem sugerida (para recuperar o atraso)
- **Semana 1:** B3+B4 e F1 em paralelo; depois B1/B2 e F2. Front já consome o CRUD atual de salas/usuários (F3, F4) sem esperar o login.
- **Semana 2:** F5/F6 (núcleo do produto) + B5, B7, B8.
- **Semana 3:** convites (B6, F7, F8), testes (B10), ajustes e deploy.
