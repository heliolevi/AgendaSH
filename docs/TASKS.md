# Tasks AgendaSH

Fonte: *Cronograma Sistema de Agendamento de Reuniões (AgendaSH)*, de 05/11/2026. **Sprint único: 06/11 a 19/11. Entrega: qui 19/11** (20/11 é feriado).
Rotas e formato de erro: `docs/API.md`.

## Equipe
| Pessoa | Área |
|---|---|
| **Hélio Levi** | Tech lead: faz par nas tarefas mais difíceis (segurança, verificação de e-mail, banco, deploy) e revisa tudo antes do merge |
| Derick, Anderson, Iago | Backend |
| Wesley, Thiago | Frontend |
| Misael | Design (entrega as telas antes do front usar) |

Legenda de **Quem**: `A + Hélio` = A é o responsável, Hélio faz junto (par) e revisa. Status: ✅ feito · 🟡 parcial · ⬜ a fazer.

## Entrega (o que precisa estar pronto)
1. Agendar reunião: dia, horário, local/link e convidados, sem choque de horário.
2. Conta verificada: confirmar o e-mail com código enviado à caixa da pessoa.
3. E-mail de estudante: só domínios permitidos (lista configurável) + código.
4. Sem dados sensíveis nas respostas (senha, código, dados de terceiros).

## Marcos
| Marco | Data | Precisa estar pronto |
|---|---|---|
| Kickoff | sex 06/11 | T1 (decisões abaixo) |
| M1 | qua 11/11 | Login com token e rotas protegidas |
| M2 | sex 13/11 | Cadastro com verificação na API; respostas mínimas e filtradas |
| M3 | ter 17/11 | Fluxo completo nas telas; **nenhuma funcionalidade nova depois disso** |
| Entrega | qui 19/11 | No ar, testado, checklist de dados sensíveis conferido |

## Decisões do kickoff (T1, sex 06/11, 30 min, todos)
| Decisão | Sugestão | Quem decide |
|---|---|---|
| Domínios que contam como estudante | Lista em variável de ambiente (`EMAIL_DOMINIOS_PERMITIDOS`). **Falta confirmar o domínio real da instituição** | Time |
| Como enviar e-mail | SMTP ou API; em dev, o código aparece no console | Iago e Anderson |
| Validade do código | 30 min, uso único | Time |
| Senha mínima | 8 (aceitar até 64+) | Time |
| Onde fica local/link | Na própria reunião (modo + local); salas só para espaços reais | Derick e Thiago |
| Contas que já existem | Passam a valer como não verificadas e pedem o código no próximo login | Time |

## Já feito (fora do cronograma original)
| Item | Quem | Status |
|---|---|---|
| Telas mobile: welcome, login, cadastro, início, calendário, reuniões, perfil (HTML/CSS/JS puro) | Hélio | ✅ |
| Middlewares: erro global em JSON (sem traceback, com CORS), `X-Request-ID`, log por requisição, cabeçalhos de segurança, CORS por `CORS_ORIGINS` (`backend/app/core/`) | Hélio | ✅ |
| Handlers 422/404/405 no formato `{detail, codigo, request_id}` e erros do Postgres mapeados (409/400/503) | Hélio | ✅ |
| 13 testes dos middlewares (`backend/tests`), `docs/API.md` | Hélio | ✅ |
| `requirements.txt` alinhado ao código (adicionado `psycopg`; removidos `sqlalchemy`, `pymysql`, `python-multipart`) + `requirements-dev.txt` | Hélio | ✅ (T2: falta Iago conferir o README) |
| `api.js` do front trata servidor fora do ar e expõe `erro.status`/`erro.codigo` | Hélio | ✅ |

## Caminhos críticos (se atrasar, atrasa a entrega)
1. **Segurança:** T3 → T7 → T10 → T14 → telas T22–T25 → T28 → T30 → T32
2. **Verificação de e-mail:** T1 → T4 → T9 → T13 → T18 → T28 → T30 → T32 (T5 e T6 também alimentam o T9)

Começam já, sem esperar: **T1, T2, T3**. O banco (T4) e o e-mail (T5) travam a verificação: comecem na terça de manhã.

## Backend
| ID | Tarefa | Quem | Prazo | Depende | Status |
|---|---|---|---|---|---|
| T2 | Alinhar `requirements.txt` e README com o que o código usa | Iago | sex 06/11 | – | 🟡 requirements feito; conferir README |
| T3 | Login com JWT: `/auth/login` devolve o token; `/auth/me` devolve a própria pessoa | **Anderson + Hélio** | seg 09/11 | – | ⬜ |
| T4 | Migrations (Alembic ou SQL numerado): colunas de verificação, tabela de códigos, campos obrigatórios (`NOT NULL`), `CHECK` de status, trava de horário (`EXCLUDE USING gist`), tratar contas antigas | **Derick + Hélio** | ter 10/11 | T1 | ⬜ |
| T5 | Serviço de envio de e-mail, com modo de teste que mostra o código no console | Iago | ter 10/11 | T1 | ⬜ |
| T6 | Regra de e-mail de estudante: domínios em variável de ambiente + validação de formato (no backend) | Iago | ter 10/11 | T1 | ⬜ |
| T7 | Proteger as rotas; organizador = usuário do token (remover `id_usuario` do corpo de `/reunioes`) | **Anderson + Hélio** | qua 11/11 | T3 | ⬜ |
| T9 | Cadastro com verificação: conta nasce não verificada, código aleatório, uso único, validade; **resposta sempre igual** exista a conta ou não | **Iago + Hélio** | qui 12/11 | T4, T5, T6 | ⬜ |
| T10 | Respostas mínimas: usuário público só com `id` e `nome`; perfil completo só da própria pessoa; colunas explícitas no lugar de `SELECT *` | **Anderson + Hélio** | qui 12/11 | T7 | ⬜ |
| T11 | Guardar modo e local/link na própria reunião; parar de criar sala por reunião; migrar dados existentes | Derick | qui 12/11 | T4 | ⬜ |
| T12 | Permissões: só a própria conta; só o organizador cancela; só o convidado responde o próprio convite | Derick (Hélio revisa) | sex 13/11 | T7 | ⬜ |
| T13 | Confirmação de e-mail por código, reenvio com limite, login bloqueado até verificar | **Iago + Hélio** | sex 13/11 | T3, T9 | ⬜ |
| T14 | Listagens filtradas: reuniões e convites só do organizador e convidados; busca limitada de pessoas para convidar | **Anderson + Hélio** | sex 13/11 | T10 | ⬜ |
| T17 | Subir homologação para testar com e-mail de verdade | Iago + Hélio | seg 16/11 | T13 | ⬜ |
| T19 | Criar reunião já com convidados (uma chamada, transação) e impedir choque também **por pessoa** | **Derick + Hélio** | seg 16/11 | T7, T11, T12 | ⬜ |
| T20 | Limite de tentativas (login, cadastro, reenvio), mensagens genéricas, **origens reais no CORS** | Anderson (Hélio revisa) | seg 16/11 | T13 | 🟡 CORS por env já feito; falta rate limit |
| T21 | Trocar e-mail no perfil: domínio permitido + nova verificação | Iago | ter 17/11 | T13 | ⬜ |
| T26 | Testes automáticos de segurança: nenhuma resposta traz senha/código/e-mail de terceiros; rota sem token = 401; ninguém acessa dado de outra pessoa | **Anderson + Hélio** | ter 17/11 | T13, T14, T20 | ⬜ (testes de middleware já existem como base) |
| T27 | Checklist manual de dados sensíveis: cada rota, resposta, logs e `.env` | Derick + Hélio | qua 18/11 manhã | T26 | ⬜ |
| T30 | Deploy final em produção com variáveis de ambiente | Iago + Hélio | qua 18/11 tarde | T17, T27, T28 | ⬜ |
| T33 | Editar reunião (opcional) | Derick | se sobrar | T19 | ⬜ |
| T34 | Recuperar senha por e-mail com o mesmo mecanismo de código (opcional) | Iago | se sobrar | T13 | ⬜ |

## Frontend
| ID | Tarefa | Quem | Prazo | Depende | Status |
|---|---|---|---|---|---|
| T8 | Guardar só o token, enviar em cada chamada, voltar ao login no 401 (hoje o `localStorage` guarda o cadastro inteiro) | Wesley (Hélio revisa) | qua 11/11 | T3 | ⬜ |
| T15 | Calendário no novo modelo (modo, local, início e **fim**) e aviso de conflito (409) | Thiago | sex 13/11 | T11 | 🟡 calendário e erro 409 já existem; falta modelo novo e fim |
| T16 | Cadastro: mensagem de código enviado, regras da senha, aviso de domínio não permitido | Wesley | sex 13/11 | T9 | 🟡 tela existe (sem verificação) |
| T18 | Tela de confirmar e-mail com reenvio; aviso de conta não verificada no login | Wesley | seg 16/11 | T13 | ⬜ |
| T22 | Perfil e demais telas usando `/auth/me` e respostas mínimas | Wesley | ter 17/11 | T10, T14 | 🟡 perfil existe; trocar fonte dos dados |
| T23 | Escolher convidados no formulário da reunião | Thiago | ter 17/11 | T14, T19 | ⬜ |
| T24 | Tela "meus convites" com aceitar/recusar | Wesley | ter 17/11 | T12, T14 | ⬜ |
| T25 | Detalhes da reunião com participantes e status | Thiago | ter 17/11 | T14, T19 | ⬜ |
| T28 | Teste ponta a ponta: cadastrar com e-mail de estudante, confirmar, entrar, agendar, convidar e aceitar | Wesley e Thiago (+ Hélio) | qua 18/11 manhã | T16, T18, T22–T25 | ⬜ |
| T29 | Ajustes de celular, acessibilidade, detalhes visuais (com Misael) | Thiago | qua 18/11 | T25 | ⬜ |

## Todos
| ID | Tarefa | Prazo | Depende |
|---|---|---|---|
| T1 | Kickoff de 30 min com as decisões acima | sex 06/11 | – |
| T31 | Corrigir bugs do teste | qua 18/11 e qui 19/11 manhã | T28 |
| T32 | Entrega e retrospectiva | qui 19/11 | T30, T31 |

## Ordem de corte se apertar
Cortar nesta ordem: **T34** (recuperar senha) → **T33** (editar reunião) → **T25** (detalhes) → **T29** (ajustes de celular).
**Não dá para cortar:** T3, T7, T9, T10, T13, T14, T26, T27 (segurança e verificação).

## Como o Hélio ajuda a equipe
- **Par programando** em T3, T4, T7, T9, T10, T13, T14, T19, T26 (30-60 min no início de cada uma; o responsável digita, Hélio guia).
- **Revisa todos os PRs** de backend antes do merge: checar `SELECT *`, campos sensíveis e permissões.
- **Padrão de erro:** toda rota nova levanta `HTTPException` com mensagem em português; erros de banco já são tratados pelo middleware (ver `docs/API.md`). Nova rota = novo teste.
- **Desbloqueios:** domínio de e-mail da instituição, provedor de e-mail e ambiente de homologação (T1, T5, T17).

## Pontos de atenção
- **Contas antigas:** tratar na T4, senão ninguém antigo consegue entrar.
- **E-mail pode cair no spam:** testar na homologação (T17) com caixa real do domínio de estudante.
- **Domínio de estudante** ainda não confirmado: sem isso a T6 não fecha.
- **Feriados locais** entre 06/11 e 19/11: confirmar.
- Fora do escopo: integração com Google Calendar/Meet.

## Revisão de dados sensíveis
| Dado | Onde pode vazar | O que fazer | Tarefa |
|---|---|---|---|
| Hash da senha | Respostas de usuário e login | Nunca sai (`UsuarioOut` já corta); teste garante | T26 |
| Código de verificação | Resposta do cadastro e logs | Só por e-mail; nunca na resposta nem nos logs (exceto modo de teste local). O log de requisição já **não** grava corpo nem query | T9, T27 |
| Nome/e-mail de outros usuários | `GET /usuarios` aberto | Lista pública só com `id` e `nome` | T10, T14 |
| Reuniões, convites e links | `GET /reunioes`, `/convites`, `/salas` abertos | Só organizador e convidados | T14 |
| Dados no navegador | `localStorage` com cadastro completo | Só o token; dados via `/auth/me` | T8, T22 |
| Mensagens de erro | "E-mail já cadastrado" revela quem tem conta | Resposta genérica no cadastro | T9, T20 |
| Alterar/apagar conta de outra pessoa | `PUT`/`DELETE /usuarios/{id}` abertos | Só a própria pessoa | T12 |
| Segredos | `.env` com URL do banco | Nunca no git (já no `.gitignore`); trocar a senha do banco se tiver ido | T27 |

## Dicionário rápido
Backend (servidor/regras/banco) · Frontend (telas) · API (como as telas falam com o backend) · Token JWT (crachá digital do login) · Migration (arquivo que registra uma mudança no banco) · Rate limit (recusar muitas tentativas seguidas) · Homologação (ambiente de teste parecido com o real) · Deploy (colocar no ar).
