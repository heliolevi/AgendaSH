# Design do front (AgendaSH)

Mundo visual: noite com aurora (violeta → ciano → magenta), herdado do protótipo do Misael.
Duas assinaturas: a **barra com os símbolos de controle** (△ □ + × ○) e a **régua do dia**.

## Tokens (`frontend/style.css`, `:root`)
| Grupo | Valores |
|---|---|
| Fundo / superfícies | `--fundo #07061a`, `--superficie` (branco 4,5%), `--superficie-2` (7,5%), `--superficie-solida #121036` |
| Texto | `--texto #f3f1ff`, `--suave #bdb8ea` (secundário), `--suave-2 #9d97d4` (terciário). Todos passam AA sobre o fundo |
| Semântica | `--reuniao #b49cff` (violeta), `--evento #22d3ee` (ciano), `--perigo #ff8fa3`, `--ok #6ee7a8` |
| Espaço (4pt) | `--e1 4` `--e2 8` `--e3 12` `--e4 16` `--e5 24` `--e6 32` `--e7 48` |
| Raio | `--r-sm 10` `--r-md 14` `--r-lg 20` `--r-xl 26` |
| Movimento | `--rapido 160ms`, `--medio 260ms`, `--ease cubic-bezier(.16,1,.3,1)` |
| Pontos de quebra | base celular · 768 tablet · 1024 PC (barra lateral) · 1440 PC largo |

## Tipografia
- **Michroma**: títulos de tela e marca.
- **Poppins**: texto, botões, rótulos (16px nos campos para o iPhone não dar zoom).
- **Oswald** com números tabulares: horários, datas, contadores.

## Componentes
- **Cartão de compromisso (`.ag`)**: coluna de horário (início grande, fim embaixo, "até 29/11" se passar do dia), tipo com ponto colorido + texto (a cor nunca é a única pista), local (link seguro), duração e papel ("Você organiza", "Convidado", "Equipe"), ações editar/cancelar só para quem pode.
- **Régua do dia (`desenharRegua`)**: faixa das 7h às 22h (cresce se precisar) com seus compromissos, local ocupado em hachurado, seu horário com moldura branca (vermelha se houver conflito) e a linha verde de "agora". No formulário, clicar na régua escolhe o início.
- **Destaque**: o próximo compromisso, único cartão com o anel em gradiente da marca.
- **Segmentos**, **chips de duração**, **diálogo** (`confirmar()`), **avisos** (`avisar()`), **estado vazio/erro/carregando**.

## Regras
- Uma ação principal por tela (botão em gradiente). Destrutivo sempre em vermelho e com confirmação.
- Alvos de toque com no mínimo 44px. Foco visível em ciano.
- Ícones só do Phosphor (`icone("nome")`), nada de emoji.
- Respeita "reduzir movimento" e "reduzir transparência" do sistema.
