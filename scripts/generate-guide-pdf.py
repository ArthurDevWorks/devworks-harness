#!/usr/bin/env python3
"""Gera o guia operacional DEVWORKS Ralph em PDF, sem dependências além de ReportLab."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "guia-devworks-ralph.pdf"

NAVY = colors.HexColor("#06111D")
PANEL = colors.HexColor("#0B1D30")
LINE = colors.HexColor("#285D88")
INK = colors.HexColor("#D8E9FF")
MUTED = colors.HexColor("#86A3BE")
BLUE = colors.HexColor("#65A8FF")
GREEN = colors.HexColor("#38D39F")
YELLOW = colors.HexColor("#F4CD63")
RED = colors.HexColor("#FF7184")
PAGE_W, PAGE_H = A4


class Divider(Flowable):
    def __init__(self, width: float, color: colors.Color = LINE) -> None:
        super().__init__()
        self.width = width
        self.color = color
        self.height = 3

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(1)
        self.canv.line(0, 1, self.width, 1)


def background(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#102B47"))
    canvas.rect(0, PAGE_H - 12 * mm, PAGE_W, 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(BLUE)
    canvas.setFont("Courier-Bold", 8)
    canvas.drawString(18 * mm, PAGE_H - 7.7 * mm, "DEVWORKS / RALPH OPERATIONS GUIDE")
    canvas.setFillColor(MUTED)
    canvas.setFont("Courier", 7)
    canvas.drawRightString(PAGE_W - 18 * mm, PAGE_H - 7.7 * mm, f"PAGE {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(.6)
    canvas.line(18 * mm, 13 * mm, PAGE_W - 18 * mm, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Courier", 7)
    canvas.drawString(18 * mm, 8 * mm, "Local-first. Read the plan. Respect the gates. Keep production safe.")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="Kicker", parent=styles["Normal"], fontName="Courier-Bold", fontSize=9,
    leading=12, textColor=BLUE, spaceAfter=5, letterSpacing=.6,
))
styles.add(ParagraphStyle(
    name="TitleDark", parent=styles["Title"], fontName="Courier-Bold", fontSize=27,
    leading=31, textColor=BLUE, alignment=TA_LEFT, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading1"], fontName="Courier-Bold", fontSize=17,
    leading=22, textColor=BLUE, spaceBefore=6, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Sub", parent=styles["Heading2"], fontName="Courier-Bold", fontSize=11,
    leading=14, textColor=INK, spaceBefore=7, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="BodyDark", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5,
    leading=14, textColor=INK, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="SmallDark", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.3,
    leading=11.5, textColor=INK,
))
styles.add(ParagraphStyle(
    name="TerminalCode", parent=styles["Code"], fontName="Courier", fontSize=8.1,
    leading=11.5, textColor=INK,
))
styles.add(ParagraphStyle(
    name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9,
    leading=13, textColor=NAVY,
))


def p(text: str, style: str = "BodyDark") -> Paragraph:
    return Paragraph(text, styles[style])


def code(text: str) -> Table:
    # Algumas linhas de exemplos terminam com a barra de continuação do shell.
    # Normaliza o marcador de patch para que ele nunca apareça no PDF.
    normalized = text.replace("\n+", "\n")
    table = Table([[p(normalized.replace("\n", "<br/>"), "TerminalCode")]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#071827")),
        ("BOX", (0, 0), (-1, -1), .7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return table


def callout(label: str, text: str, color: colors.Color = BLUE) -> Table:
    table = Table([[p(label, "Kicker")], [p(text.replace("\n", "<br/>"), "SmallDark")]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6 * mm),
    ]))
    return table


def checklist(items: list[tuple[str, str]]) -> Table:
    rows = [[p("CHECK", "SmallDark"), p("AÇÃO", "SmallDark")]]
    rows.extend([[p(mark, "SmallDark"), p(text, "SmallDark")] for mark, text in items])
    table = Table(rows, colWidths=[26 * mm, 148 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#143554")),
        ("BACKGROUND", (0, 1), (-1, -1), PANEL),
        ("GRID", (0, 0), (-1, -1), .35, LINE),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]))
    return table


def section(title: str, kicker: str) -> list:
    return [p(kicker, "Kicker"), p(title, "Section"), Divider(174 * mm), Spacer(1, 4 * mm)]


def build_story() -> list:
    story: list = []
    story += [Spacer(1, 30 * mm), p("DEVWORKS", "Kicker"), p("RALPH\nOPERATIONS GUIDE", "TitleDark")]
    story += [p("Guia prático para planejar, executar e acompanhar trabalho assistido por agentes em projetos existentes, produção e projetos novos.", "BodyDark"), Spacer(1, 5 * mm)]
    story += [callout("PRINCÍPIO OPERACIONAL", "O Ralph não substitui a revisão humana. Ele executa um plano explícito, em sessões novas, e só aceita uma fase quando os quatro gates estiverem verdes.", GREEN), Spacer(1, 8 * mm)]
    story += [p("TRÊS CAMINHOS", "Kicker"), checklist([
        ("01", "Ajustar um sistema existente sem ampliar o escopo."),
        ("02", "Implementar uma funcionalidade em um projeto em produção com rollout controlado."),
        ("03", "Criar um projeto do zero a partir de contexto, especificação e fases."),
    ])]
    story += [Spacer(1, 9 * mm), p("Versão operacional - DEVWORKS Harness", "SmallDark"), PageBreak()]

    story += section("1. Modelo mental e guardrails", "COMECE AQUI")
    story += [p("O Harness separa descoberta, planejamento, contexto, execução e observação. Cada etapa deixa um artefato revisável; o próximo passo só consome o que foi explicitamente aceito."),
              checklist([
                  ("INIT", "Constrói `.spec/init/*` para um projeto novo ou pouco documentado."),
                  ("PLAN", "Cria `SPEC.md`, `PLAN.md` e `PHASES.md` para uma feature com slug."),
                  ("CONTEXT", "Mantém `AGENTS.md`, `CLAUDE.md` e `docs/agents/*` baseados no código real."),
                  ("RALPH", "Executa `PHASES.md`, abre uma sessão nova por fase e aplica G0, G1, G2 e G3."),
                  ("MONITOR", "Mostra estado e logs; não inicia, cancela, pausa ou retoma runs."),
              ]), Spacer(1, 5 * mm),
              callout("REGRA DE OURO", "Antes de qualquer run: confirme repositório, branch, arquivo de fases e comandos de teste. Ralph preserva as mudanças para revisão e commit manual.", YELLOW),
              p("Os quatro engines têm o mesmo contrato de saída. Escolha um engine por disponibilidade e autenticação; não reescreva o plano apenas para trocar de fornecedor."),
              code("scripts/install-platform.sh --platform codex --scope project\n./scripts/ralph.sh --engine codex .spec/features/meu-ajuste/PHASES.md"), PageBreak()]

    story += section("2. Projeto existente: comandos exatos", "SEM HARNESS INSTALADO")
    story += [p("Este é o caminho para quando o repositório contém apenas os arquivos do sistema. Mantenha o DEVWORKS Harness em outro diretório e execute os comandos abaixo na raiz do projeto-alvo."),
              code("cd /caminho/do/meu-projeto\ngit switch -c feat/minha-funcionalidade\ncodex login\ncodex --version\n/caminho/devworks-harness/scripts/install-platform.sh \\\n+  --platform codex --scope project"),
              checklist([
                  ("cd", "Entra na raiz correta; Ralph e os Skills usarão este repositório."),
                  ("switch", "Cria uma branch isolada, pronta para revisão e rollback."),
                  ("login", "Abre o fluxo oficial de autenticação da CLI; não grava token no repositório."),
                  ("version", "Confirma que a CLI do agente está instalada e responde normalmente."),
                  ("install", "Copia somente os Skills para `.agents/skills/` do projeto."),
              ]),
              p("No Codex, abra esse projeto e envie primeiro:", "Sub"),
              code("Use o Skill ai-context. Analise o código existente e gere o contexto do projeto.\nNão implemente nenhuma funcionalidade."),
              p("Depois, descreva a funcionalidade para o Skill plan. Inclua objetivo, regras de negócio, perfis afetados, critérios de aceite, limites e o comando de testes. Não peça implementação nessa etapa."),
              code("/caminho/devworks-harness/scripts/ralph.sh --engine codex \\\n+  --test-cmd 'php artisan test' .spec/features/<slug>/PHASES.md\n/caminho/devworks-harness/scripts/ralph-web.sh ."),
              callout("REVISÃO MANUAL", "O Ralph não faz stage, commit, reset nem altera exclusões do Git. Ao fim do run, revise o diff acumulado e faça o commit manualmente.", YELLOW), PageBreak()]

    story += section("3. Caso 1 - Ajuste em sistema existente", "MENOR MUDANÇA SEGURA")
    story += [p("Use este caminho para correções, compatibilidade, comportamento inesperado ou uma mudança pequena e conhecida. A prioridade é preservar regras existentes e limitar o diff."),
              p("Passo a passo", "Sub"),
              checklist([
                  ("1", "Reproduza o problema e registre o comportamento atual, o esperado e a evidência disponível."),
                  ("2", "Atualize contexto se ele estiver ausente ou desatualizado: rode `ai-context` e revise a saída antes de planejar."),
                  ("3", "Crie uma feature curta via `plan`, com tarefas pequenas, arquivos prováveis e critérios de aceitação verificáveis."),
                  ("4", "Revise `PHASES.md`: garanta que não inclui refactor, migration ou alteração de regra fora do pedido."),
                  ("5", "Crie branch de trabalho e execute Ralph com o comando de teste real; mudanças existentes não bloqueiam o run."),
                  ("6", "Revise o diff acumulado, faça teste manual do cenário e só então faça o commit, merge ou deploy."),
              ]),
              code("git switch -c fix/ajuste-relatado\n./scripts/ralph.sh --engine codex --test-cmd 'php artisan test' \\\n+  .spec/features/ajuste-relatado/PHASES.md"),
              callout("NÃO PULE", "Gate 1 só observa se houve escrita. Gate 3 é quem confirma task por task. Uma fase sem diff pode estar correta, mas somente se os gates finais sustentarem isso.", BLUE), PageBreak()]

    story += section("4. Caso 2 - Nova funcionalidade em produção", "PLANEJE O ROLLOUT")
    story += [p("Em produção, a execução deve ser progressiva e reversível. O plano precisa explicitar compatibilidade, dados existentes, observabilidade, feature flags quando aplicáveis e rollback."),
              p("Antes do planejamento", "Sub"),
              checklist([
                  ("A", "Defina objetivo, usuários afetados, critérios de aceite e o que não pode mudar."),
                  ("B", "Mapeie contrato de API, permissões, jobs, filas, migrations, índices e integrações."),
                  ("C", "Defina estratégia de rollout: flag, deploy gradual, migration aditiva, métrica de saúde e rollback."),
              ]),
              p("Estrutura recomendada de fases", "Sub"),
              checklist([
                  ("F1", "Base compatível: schema aditivo, contrato, permissão e testes de regressão."),
                  ("F2", "Comportamento novo protegido por configuração/flag e observabilidade."),
                  ("F3", "Interface, fluxo final e validação de acessibilidade."),
                  ("F4", "Testes integrados, checklist de deploy, rollback e documentação operacional."),
              ]),
              callout("DADOS E PRODUÇÃO", "Não deixe o agente decidir migração destrutiva, backfill em massa ou corte de compatibilidade. Essas decisões devem constar no PHASES.md com consulta de conferência, janela de execução e plano de retorno.", RED),
              code("./scripts/ralph.sh --engine claude --max-cycles 2 \\\n+  --test-cmd './vendor/bin/sail test' \\\n+  .spec/features/nova-funcionalidade/PHASES.md"), PageBreak()]

    story += section("5. Caso 3 - Projeto novo", "DO ZERO A UM PLANO EXECUTÁVEL")
    story += [p("Para um projeto novo, não comece pelo Ralph. Primeiro construa uma cadeia de documentos que torne decisões de negócio e arquitetura verificáveis."),
              checklist([
                  ("1", "Instale o Skill da plataforma escolhida e inicialize o repositório Git."),
                  ("2", "Execute `init` até revisar descrição do projeto, histórias, dados e fases iniciais em `.spec/init/`."),
                  ("3", "Acrescente referências de interface em `.spec/init/design/` quando houver telas, componentes ou inspiração visual."),
                  ("4", "Revise `.spec/init/project-phases.md`: cada `## Phase N:` deve ter tasks, arquivos e testes possíveis."),
                  ("5", "Rode a primeira fase em uma branch isolada e trate o resultado como uma revisão de arquitetura, não só como código gerado."),
                  ("6", "Depois de código real existir, rode `ai-context` para documentar a arquitetura observada."),
              ]),
              code("git init\nscripts/install-platform.sh --platform opencode --scope project\n# Use o workflow init na interface da sua plataforma\n./scripts/ralph.sh --engine opencode .spec/init/project-phases.md"),
              callout("DEFINIÇÃO DE PRONTO", "Um projeto novo não está pronto quando compila. Ele está pronto quando os fluxos essenciais, testes, configuração, segurança, deploy e operação foram assumidos explicitamente no plano.", GREEN), PageBreak()]

    story += section("6. Execução e acompanhamento", "O QUE O RALPH FAZ")
    story += [p("O Ralph abre uma sessão nova em cada fase e em cada ciclo de correção. Ele não usa exit code do agente como prova final. Os gates são mecânicos:"),
              checklist([
                  ("G0", "A CLI terminou conforme o contrato do adaptador."),
                  ("G1", "A sessão alterou a árvore? É sinal, não veredito."),
                  ("G2", "A suíte de testes configurada passou fora da sessão do agente."),
                  ("G3", "Um verificador read-only confirma `TASK n: DONE/INCOMPLETE`. Este é o veredito final."),
              ]),
              p("Acompanhe pelo TUI ou pelo monitor web", "Sub"),
              code("./scripts/ralph-watch.sh /caminho/do/projeto\n./scripts/ralph-web.sh /caminho/do/projeto\n# abre http://127.0.0.1:7331"),
              p("O monitor mostra projeto, engine, run, PID, duração, progresso, fase, ciclo, gate, tabela hierárquica, logs recentes e histórico. Ele lê somente `.phases/`; não expõe a execução à rede e não tem botões de controle."),
              p("A estrutura de estado permite interromper o terminal sem apagar diagnóstico. `runs/<run-id>/` mantém logs e prompts; `progress/<input-hash>.progress` só retoma um documento de fases idêntico."), PageBreak()]

    story += section("7. Checklist de decisão e operação", "ANTES, DURANTE E DEPOIS")
    story += [p("Antes de executar", "Sub"), checklist([
        ("[ ]", "Repositório, branch e `PHASES.md` corretos."),
        ("[ ]", "Alterações existentes foram identificadas; Ralph não as inclui em commits nem altera o índice."),
        ("[ ]", "CLI autenticada; engine escolhido explicitamente."),
        ("[ ]", "Comando de testes real definido; ambiente necessário disponível."),
        ("[ ]", "Dados, migrations, integrações e rollback revisados quando houver produção."),
    ]), p("Durante", "Sub"), checklist([
        ("[ ]", "Observe G0-G3 e trate limite de uso como espera, não como falha funcional."),
        ("[ ]", "Não altere o plano enquanto o run está ativo. Pare e crie um novo plano se o escopo mudou."),
        ("[ ]", "Use logs e prompts do run para investigar; não exponha tokens ou dados sensíveis."),
    ]), p("Depois", "Sub"), checklist([
        ("[ ]", "Revise o diff completo e faça o commit manualmente, quando desejado."),
        ("[ ]", "Execute validação manual dos critérios de aceite."),
        ("[ ]", "Para produção: valide métricas, logs, rollback e comunicação operacional."),
    ]), Spacer(1, 6 * mm),
    callout("COMANDO DE VALIDAÇÃO DO HARNESS", "scripts/check-shell.sh\nscripts/check-skill-drift.sh\npython3 -m unittest tests/test_dashboard.py\ngit diff --check", BLUE)]
    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(18 * mm, 17 * mm, 174 * mm, 258 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document = BaseDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=17 * mm,
        title="DEVWORKS Ralph Operations Guide", author="DEVWORKS",
    )
    document.addPageTemplates([PageTemplate(id="devworks", frames=[frame], onPage=background)])
    document.build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()
