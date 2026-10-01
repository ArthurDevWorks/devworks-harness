#!/usr/bin/env python3
"""Gera o guia completo e compartilhavel do DEVWORKS Harness."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "guia-completo-devworks-harness.pdf"

PAGE_W, PAGE_H = A4
NAVY = colors.HexColor("#07131F")
PANEL = colors.HexColor("#0D2134")
PANEL_ALT = colors.HexColor("#12304A")
LINE = colors.HexColor("#285D88")
INK = colors.HexColor("#E7F1FC")
MUTED = colors.HexColor("#91A9C1")
BLUE = colors.HexColor("#68AEFF")
GREEN = colors.HexColor("#49D7A5")
YELLOW = colors.HexColor("#F2CC69")
RED = colors.HexColor("#FF8290")
WHITE = colors.white


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


def page_background(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#102B47"))
    canvas.rect(0, PAGE_H - 12 * mm, PAGE_W, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.setFont("Courier-Bold", 7.6)
    canvas.drawString(18 * mm, PAGE_H - 7.6 * mm, "DEVWORKS HARNESS / GUIA COMPLETO")
    canvas.setFillColor(MUTED)
    canvas.setFont("Courier", 7)
    canvas.drawRightString(PAGE_W - 18 * mm, PAGE_H - 7.6 * mm, f"PAGINA {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 13 * mm, PAGE_W - 18 * mm, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Courier", 6.8)
    canvas.drawString(18 * mm, 8 * mm, "Planejar. Detalhar. Executar. Validar. Commitar. Repetir.")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="Kicker", parent=styles["Normal"], fontName="Courier-Bold", fontSize=8.5,
    leading=11, textColor=BLUE, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="TitleDark", parent=styles["Title"], fontName="Courier-Bold", fontSize=26,
    leading=30, textColor=BLUE, alignment=TA_LEFT, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading1"], fontName="Courier-Bold", fontSize=16,
    leading=20, textColor=BLUE, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Sub", parent=styles["Heading2"], fontName="Courier-Bold", fontSize=10.5,
    leading=14, textColor=INK, spaceBefore=7, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2,
    leading=13.5, textColor=INK, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.9,
    leading=11, textColor=INK,
))
styles.add(ParagraphStyle(
    name="Tiny", parent=styles["BodyText"], fontName="Helvetica", fontSize=6.8,
    leading=9, textColor=MUTED,
))
styles.add(ParagraphStyle(
    name="TerminalCode", parent=styles["Code"], fontName="Courier", fontSize=7.5,
    leading=10.2, textColor=INK,
))
styles.add(ParagraphStyle(
    name="Center", parent=styles["BodyText"], fontName="Helvetica", fontSize=9,
    leading=13, textColor=INK, alignment=TA_CENTER,
))


def para(text: str, style: str = "Body", raw: bool = False) -> Paragraph:
    return Paragraph(text if raw else escape(text).replace("\n", "<br/>"), styles[style])


def code(text: str) -> Table:
    text = text.replace("\n+", "\n")
    cell = para(text, "TerminalCode")
    table = Table([[cell]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#061827")),
        ("BOX", (0, 0), (-1, -1), .7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return table


def callout(label: str, text: str, accent: colors.Color = BLUE) -> Table:
    table = Table([[para(label, "Kicker")], [para(text, "Small")]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6 * mm),
    ]))
    return table


def grid(headers: list[str], rows: list[list[str]], widths: list[float], font: str = "Small") -> Table:
    data = [[para(value, "Small") for value in headers]]
    data.extend([[para(value, font) for value in row] for row in rows])
    table = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL_ALT),
        ("BACKGROUND", (0, 1), (-1, -1), PANEL),
        ("GRID", (0, 0), (-1, -1), .35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.6 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.6 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
    ]))
    return table


def checklist(items: list[str]) -> Table:
    return grid(["", "Verificacao"], [["[ ]", item] for item in items], [14, 160])


def section(number: str, title: str, kicker: str) -> list:
    return [para(kicker, "Kicker"), para(f"{number}. {title}", "Section"), Divider(174 * mm), Spacer(1, 4 * mm)]


def source_link(label: str, url: str) -> Paragraph:
    return para(f'<link href="{escape(url)}" color="#68AEFF">{escape(label)}</link>', "Tiny", raw=True)


def build_story() -> list:
    story: list = []

    story += [
        Spacer(1, 30 * mm),
        para("DEVWORKS", "Kicker"),
        para("HARNESS\nGUIA COMPLETO DE USO", "TitleDark"),
        para("Da instalação ao ciclo contínuo de desenvolvimento com Plan, Task Builder, Ralph, gates, dashboard e failover de modelos.", "Body"),
        Spacer(1, 5 * mm),
        callout("PUBLICO", "Desenvolvedores e equipes que desejam usar o harness em projetos novos ou legados, com diferentes assinaturas e engines de IA.", GREEN),
        Spacer(1, 6 * mm),
        grid(["Edicao", "Data", "Escopo"], [["MVP operacional", "28/09/2026", "Uso local e compartilhamento interno"]], [45, 42, 87]),
        Spacer(1, 10 * mm),
        para("A regra central é simples: o agente prepara ou executa; a equipe revisa, valida e decide o commit.", "Center"),
        PageBreak(),
    ]

    story += section("1", "Visão geral", "O FLUXO EM UMA PAGINA")
    story += [
        para("O DEVWORKS Harness organiza o trabalho em quatro passos. Para um projeto novo, o ponto de partida é um PRD. Para um legado, o ponto de partida é a documentação do código real."),
        grid(
            ["Etapa", "Responsabilidade", "Saída"],
            [
                ["Plan", "Transforma PRD ou solicitação em fases maiores, semelhantes a releases.", "SPEC.md, PLAN.md e visão de fases"],
                ["Task Builder", "Detalha uma fase em tarefas pequenas, ordenadas e testáveis.", "PHASES.md executável"],
                ["Ralph", "Executa uma fase por vez, com sessões novas, correções e quatro gates.", "Código alterado, logs e estado"],
                ["Humano", "Valida critérios, revisa o diff e cria o commit.", "Checkpoint seguro para o próximo ciclo"],
            ],
            [30, 94, 50],
        ),
        Spacer(1, 5 * mm),
        callout("CICLO RECOMENDADO", "Plan -> Task Builder -> Ralph -> gates verdes -> revisão manual -> testes manuais -> commit -> próxima fase.", GREEN),
        para("O commit manual é o ponto de segurança entre execuções. O Ralph não faz stage, commit, reset ou alteração de exclusões do Git."),
        para("Estado real deste MVP", "Sub"),
        grid(
            ["Componente", "Situação"],
            [
                ["Ralph e quatro engines", "Implementado e testado"],
                ["Gates, histórico, lock, TUI e dashboard web", "Implementado"],
                ["Política Antigravity com fallback de modelo", "Implementada no Ralph"],
                ["Skills portáveis e Task Builder", "Implementados: init, plan, task-builder e ai-context"],
                ["Plugin Claude", "Comandos legados preservados como adaptador"],
            ],
            [65, 109],
        ),
        PageBreak(),
    ]

    story += section("2", "Pré-requisitos e segurança", "ANTES DE INSTALAR")
    story += [
        para("O harness trabalha sobre um repositório Git local. Ele pode executar comandos e editar arquivos sem intervenção durante uma fase. Use apenas em projetos confiáveis e prefira uma branch própria."),
        checklist([
            "Git instalado e repositório inicializado.",
            "Bash 4 ou superior para execução funcional completa dos testes do harness.",
            "Python 3 para o dashboard web local.",
            "Pelo menos uma engine instalada e autenticada.",
            "Comando real de testes do projeto conhecido.",
            "Branch de trabalho criada antes da primeira execução.",
        ]),
        Spacer(1, 5 * mm),
        callout("SEGREDOS", "Nunca coloque tokens, chaves ou senhas no repositório, no PHASES.md ou nos prompts. Use o login oficial da CLI, variáveis de ambiente seguras ou o cofre corporativo.", RED),
        para("Permissões de execução", "Sub"),
        para("A sessão implementadora recebe permissão para editar e executar comandos. O Gate 3 usa uma sessão restrita e somente leitura. Essa separação reduz o risco de o próprio implementador aprovar o que fez."),
        para("Checklist mínimo antes de rodar", "Sub"),
        checklist([
            "Confirmar diretório, branch e arquivo PHASES.md.",
            "Revisar mudanças já existentes na árvore.",
            "Definir o comando de teste com --test-cmd quando a detecção automática não for suficiente.",
            "Revisar migrations, integrações externas e operações irreversíveis antes de autorizar a fase.",
        ]),
        PageBreak(),
    ]

    story += section("3", "Instalação do harness", "REPOSITORIO CENTRAL")
    story += [
        para("Mantenha uma cópia central do DEVWORKS Harness fora dos projetos atendidos. Os scripts são chamados a partir da raiz do projeto-alvo."),
        code("git clone <url-interno-ou-github>/devworks-harness.git\ncd devworks-harness\ngit switch main\nchmod +x scripts/*.sh scripts/engines/*.sh"),
        para("Valide o harness antes de compartilhar", "Sub"),
        code("./scripts/check-shell.sh\n./scripts/test-ralph.sh\ngit diff --check"),
        para("Uso a partir de outro projeto", "Sub"),
        code("cd /caminho/do/projeto-alvo\ngit switch -c feat/minha-entrega\n/caminho/devworks-harness/scripts/ralph.sh --help"),
        callout("IMPORTANTE", "O Ralph é independente e está pronto para as quatro engines. Os quatro Skills canônicos já estão empacotados; rode check-skill-drift antes de distribuir uma nova versão. O plugin Claude continua como adaptador compatível.", YELLOW),
        para("Estrutura relevante", "Sub"),
        grid(
            ["Caminho", "Finalidade"],
            [
                ["scripts/ralph.sh", "Orquestrador principal"],
                ["scripts/engines/", "Adaptadores Codex, Claude, OpenCode e Antigravity"],
                ["config/model-policy.tsv", "Política de modelos do Antigravity"],
                ["scripts/ralph-watch.sh", "Painel de terminal"],
                ["scripts/ralph-web.sh", "Dashboard web local"],
                ["skills/", "Fonte canônica: init, plan, task-builder e ai-context"],
                ["commands/ e agents/", "Adaptador de compatibilidade do plugin Claude"],
            ],
            [61, 113],
        ),
        PageBreak(),
    ]

    story += section("4", "Engines suportadas", "ESCOLHA POR ACESSO E CONTEXTO")
    story += [
        para("Engine é a CLI que executa o trabalho. Modelo é a inteligência selecionada dentro daquela engine. Trocar a engine não exige reescrever o PHASES.md."),
        grid(
            ["Engine", "Executável", "Melhor uso inicial", "Autenticação"],
            [
                ["Codex", "codex", "Equipe com assinatura ChatGPT/Codex; execução e revisão de código.", "Login com conta ChatGPT ou credencial corporativa"],
                ["Claude Code", "claude", "Planejamento, arquitetura e uso completo do plugin atual.", "Claude Pro/Max, Console, Bedrock ou Vertex"],
                ["OpenCode", "opencode", "Equipe que precisa escolher entre vários provedores.", "Login por provedor; conferir política corporativa"],
                ["Antigravity", "agy", "Assinatura Google com acesso a Gemini e, quando disponível, Claude.", "Google OAuth ou projeto Google Cloud"],
            ],
            [28, 25, 72, 49],
            font="Tiny",
        ),
        Spacer(1, 5 * mm),
        para("Instalação rápida por engine", "Sub"),
        code("# Codex\nnpm install -g @openai/codex\ncodex\n\n# Claude Code\nnpm install -g @anthropic-ai/claude-code\nclaude\n\n# OpenCode\nnpm install -g @opencode/cli\nopencode auth login\n\n# Antigravity - macOS/Linux\ncurl -fsSL https://antigravity.google/cli/install.sh | bash\nagy"),
        callout("NÃO CONFUNDA", "Claude é a família de modelos e Claude Code é uma engine. Antigravity é outra engine e pode expor Claude Opus/Sonnet e Gemini conforme a assinatura. A lista real deve ser confirmada com agy models.", BLUE),
        PageBreak(),
    ]

    story += section("5", "Configuração e teste das engines", "UM TESTE POR MAQUINA")
    story += [
        grid(
            ["Engine", "Verificar", "Executar no Ralph"],
            [
                ["Codex", "codex --version e login interativo", "--engine codex"],
                ["Claude", "claude --version e claude", "--engine claude"],
                ["OpenCode", "opencode --version e opencode auth list", "--engine opencode"],
                ["Antigravity", "agy --version e agy models", "--engine antigravity"],
            ],
            [35, 79, 60],
        ),
        Spacer(1, 5 * mm),
        code("./scripts/ralph.sh --engine codex --test-cmd 'npm test' PHASES.md\n./scripts/ralph.sh --engine claude --test-cmd 'composer test' PHASES.md\n./scripts/ralph.sh --engine opencode --test-cmd 'pytest' PHASES.md\n./scripts/ralph.sh --engine antigravity --profile standard PHASES.md"),
        para("Como escolher", "Sub"),
        checklist([
            "Use Codex quando a equipe já possui acesso e quer uma engine direta para implementação.",
            "Use Claude Code quando o fluxo também depende dos comandos e agentes do plugin DEVWORKS.",
            "Use OpenCode quando a flexibilidade de provedor for o fator principal.",
            "Use Antigravity quando a assinatura Google é a fonte principal e o fallback entre modelos deve ser automático.",
        ]),
        callout("PORTABILIDADE", "O contrato do Ralph é o PHASES.md. A mesma fase pode ser executada por outra engine, desde que a primeira execução tenha sido encerrada e o diff atual tenha sido revisado.", GREEN),
        PageBreak(),
    ]

    story += section("6", "Política de modelos do Antigravity", "QUALIDADE ONDE IMPORTA; VELOCIDADE NO VOLUME")
    story += [
        para("A política inicial reserva Claude Opus e Gemini 3.1 Pro High para decisões pesadas. Gemini 3.8 Flash atende a execução recorrente. Os nomes são identificadores reais da CLI e podem mudar; confirme periodicamente com agy models."),
        grid(
            ["Papel/perfil", "Primário", "Fallback 1", "Fallback 2"],
            [
                ["Plan", "Claude Opus 4.6 Thinking", "Gemini 3.1 Pro High", "Gemini 3.8 Flash High"],
                ["Task Builder", "Claude Opus 4.6 Thinking", "Gemini 3.1 Pro High", "Gemini 3.8 Flash High"],
                ["Execução routine", "Gemini 3.8 Flash Medium", "Gemini 3.8 Flash High", "Gemini 3.1 Pro High"],
                ["Execução standard", "Gemini 3.8 Flash High", "Gemini 3.1 Pro High", "Claude Opus 4.6 Thinking"],
                ["Execução complex", "Gemini 3.1 Pro High", "Claude Opus 4.6 Thinking", "Gemini 3.8 Flash High"],
                ["Verificação", "Claude Sonnet 4.6", "Gemini 3.8 Flash High", "-"],
            ],
            [34, 48, 47, 45],
            font="Tiny",
        ),
        Spacer(1, 5 * mm),
        code("# Rotina simples\n./scripts/ralph.sh --engine antigravity --profile routine PHASES.md\n\n# Padrão recomendado\n./scripts/ralph.sh --engine antigravity --profile standard PHASES.md\n\n# Arquitetura/refatoração difícil\n./scripts/ralph.sh --engine antigravity --profile complex PHASES.md"),
        para("Quando ocorre limite de uso do modelo atual, o Ralph tenta o próximo modelo da mesma rota e continua a mesma fase. Se todas as rotas estiverem esgotadas, ele aguarda o reset. Falha de teste ou gate vermelho não troca o modelo automaticamente: ela abre um ciclo normal de correção."),
        para("No MVP atual, o Ralph aplica automaticamente somente as rotas execution-* e verify. Para Plan e Task Builder, selecione a rota definida na política dentro da interface da engine; a Skill preserva o mesmo contrato de saída."),
        callout("CONFIGURAÇÃO CENTRAL", "Edite config/model-policy.tsv para ajustar a ordem corporativa. Evite espalhar nomes de modelos em scripts e documentação de projeto.", YELLOW),
        PageBreak(),
    ]

    story += section("7", "Artefatos e contrato entre etapas", "CADA PASSO DEIXA UMA SAIDA REVISAVEL")
    story += [
        grid(
            ["Artefato", "Responsável", "Uso seguinte"],
            [
                ["PRD ou solicitação", "Produto / solicitante", "Entrada do Plan"],
                ["SPEC.md", "Plan", "Requisitos e critérios de aceite"],
                ["PLAN.md", "Plan", "Arquitetura, riscos, dependências e fases"],
                ["PHASES.md", "Task Builder", "Input direto do Ralph"],
                ["AGENTS.md e docs/agents/*", "ai-context", "Contexto real de projeto legado"],
                [".phases/runs/*", "Ralph", "Logs, prompts, gates e histórico"],
                ["Commit", "Desenvolvedor", "Checkpoint entre ciclos"],
            ],
            [58, 40, 76],
        ),
        Spacer(1, 5 * mm),
        para("Formato mínimo do PHASES.md", "Sub"),
        code("## Phase 1: Nome da fase\n\n- [ ] Task 1: resultado verificável\n  - Arquivos prováveis: caminho/arquivo.ext\n  - Critério de aceite: condição binária\n  - Teste: comando ou cenário\n\n- [ ] Task 2: próximo resultado"),
        callout("REGRA DE FORMATO", "Cada fase de nível superior deve usar exatamente ## Phase N: Título. Subfases podem usar ### Phase N.M:. Uma task deve ser pequena o bastante para ter critério binário e evidência verificável.", RED),
        PageBreak(),
    ]

    story += section("8", "Projeto novo", "PRD -> RELEASES -> TASKS -> CÓDIGO")
    story += [
        para("Em um projeto novo, o Plan define as fases maiores. Elas funcionam como releases ou marcos. O Task Builder só detalha a fase que será executada agora, evitando planejar em excesso."),
        checklist([
            "Criar o repositório e uma branch inicial.",
            "Escrever ou anexar o PRD com objetivo, público, regras, restrições e critérios de aceite.",
            "Executar o Plan com Claude Opus; usar Gemini 3.1 Pro High como fallback.",
            "Revisar arquitetura, dependências, riscos e ordem das fases.",
            "Escolher a próxima fase e detalhá-la no Task Builder.",
            "Executar com Ralph; perfil standard por padrão, complex quando necessário.",
            "Validar, revisar o diff e commitar.",
            "Repetir o ciclo para a próxima fase ou melhoria.",
        ]),
        Spacer(1, 5 * mm),
        para("Prompt de Plan", "Sub"),
        code("Use o modo Plan. Leia o PRD em docs/PRD.md.\nDefina arquitetura, dependências, riscos, critérios de aceite e fases maiores.\nAs fases devem funcionar como releases. Não implemente código."),
        para("Prompt de Task Builder", "Sub"),
        code("Leia SPEC.md e PLAN.md. Detalhe somente a próxima fase em PHASES.md.\nCrie tasks pequenas, ordenadas, com arquivos prováveis, critérios binários,\ntestes, dependências e riscos. Não implemente código."),
        callout("REVISÃO OBRIGATÓRIA", "O Task Builder já é um Skill portável. Revise o PHASES.md antes de chamar o Ralph: o arquivo é o contrato que define o escopo executável.", YELLOW),
        PageBreak(),
    ]

    story += section("9", "Projeto legado", "DOCUMENTAR O QUE EXISTE ANTES DE MUDAR")
    story += [
        para("No legado, não comece pelo PRD nem pela implementação. Primeiro gere contexto a partir do código real. O ai-context não deve usar a pasta .spec como fonte; ele documenta apenas o que está implementado."),
        checklist([
            "Abrir o repositório correto e registrar branch, stack e comandos existentes.",
            "Executar ai-context para gerar AGENTS.md, CLAUDE.md e docs/agents/*.",
            "Revisar arquitetura, domínio, contratos, modelo de dados e dependências documentadas.",
            "Descrever a manutenção desejada, incluindo comportamento atual e esperado.",
            "Executar o Plan usando a documentação real como referência.",
            "Detalhar somente a fase necessária no Task Builder.",
            "Executar Ralph, validar regressões e commitar manualmente.",
        ]),
        Spacer(1, 5 * mm),
        code("# Usando qualquer engine após instalar os Skills\nUse o Skill ai-context no repositório atual.\nUse o Skill plan para: <descrição da manutenção>.\nUse task-builder para a fase <N>.\n\n# Depois de revisar o PHASES.md gerado\n/caminho/devworks-harness/scripts/ralph.sh --engine antigravity \\\n+  --profile standard --test-cmd '<comando-real>' \\\n+  .spec/features/<slug>/phases/<NN>-<nome>/PHASES.md"),
        callout("PRESERVE O LEGADO", "A documentação gerada é AS IS. O Plan descreve o TO BE. Não use ai-context para inventar arquitetura ideal nem para reescrever regras antigas sem evidência.", GREEN),
        PageBreak(),
    ]

    story += section("10", "Plan e Task Builder", "RESPONSABILIDADES DIFERENTES")
    story += [
        grid(
            ["Decisão", "Plan", "Task Builder"],
            [
                ["Escopo", "Produto/feature e fases maiores", "Uma fase por vez"],
                ["Arquitetura", "Decide abordagem e dependências", "Respeita a abordagem aprovada"],
                ["Granularidade", "Release/marco", "Task pequena e verificável"],
                ["Riscos", "Mapeia riscos amplos", "Traduz em travas e sequência"],
                ["Testes", "Define estratégia", "Define teste/evidência por task"],
                ["Código", "Não escreve", "Não escreve"],
            ],
            [46, 64, 64],
        ),
        Spacer(1, 5 * mm),
        para("Critério de pronto do Plan", "Sub"),
        checklist([
            "Fases têm objetivo, dependências, riscos e critérios de aceite.",
            "Decisões críticas e limites de escopo estão explícitos.",
            "A fase seguinte pode ser escolhida sem rediscutir toda a arquitetura.",
        ]),
        para("Critério de pronto do Task Builder", "Sub"),
        checklist([
            "Cada task produz um resultado observável.",
            "Arquivos prováveis e comandos de teste estão indicados.",
            "A ordem respeita dependências.",
            "A fase cabe em uma execução revisável.",
        ]),
        callout("EVITE", "Não transforme o Task Builder em um segundo Plan. Se uma task exige uma nova decisão de arquitetura, volte ao Plan e atualize a fase antes de executar.", RED),
        PageBreak(),
    ]

    story += section("11", "Execução com Ralph", "UMA SESSÃO NOVA POR FASE E CORREÇÃO")
    story += [
        para("O Ralph lê o PHASES.md, separa as fases e abre uma sessão nova para cada uma. Uma falha abre outra sessão com a causa real. A sessão anterior não é reutilizada."),
        code("./scripts/ralph.sh [opções] [arquivo]\n\n--engine codex|claude|opencode|antigravity\n--profile routine|standard|complex\n--from N\n--keep-going\n--max-cycles N\n--test-cmd '<comando>'\n--no-verify\n--dashboard"),
        para("Exemplos", "Sub"),
        code("# Projeto Laravel\n./scripts/ralph.sh --engine antigravity --profile standard \\\n+  --test-cmd 'vendor/bin/sail test' .spec/features/cadastro/PHASES.md\n\n# Retomar da fase 3\n./scripts/ralph.sh --engine codex --from 3 PHASES.md\n\n# Refatoração complexa\n./scripts/ralph.sh --engine antigravity --profile complex \\\n+  --max-cycles 2 PHASES.md"),
        callout("PADRÃO", "Use standard para a maioria das fases. Use routine para trabalho repetitivo e bem delimitado. Use complex para arquitetura difícil, refatoração ampla ou diagnóstico com muitas dependências.", BLUE),
        PageBreak(),
    ]

    story += section("12", "Gates, correção e failover", "O QUE REALMENTE APROVA UMA FASE")
    story += [
        grid(
            ["Gate", "Pergunta", "Decisão"],
            [
                ["G0", "A engine terminou de verdade?", "Contrato específico da CLI e evento terminal"],
                ["G1", "A sessão alterou a árvore?", "Sinal de escrita; não aprova sozinho"],
                ["G2", "A suíte de testes passou?", "Ralph executa fora da sessão do agente"],
                ["G3", "Cada task existe no código?", "Verificador read-only decide DONE/INCOMPLETE"],
            ],
            [18, 70, 86],
        ),
        Spacer(1, 5 * mm),
        para("Comportamentos diferentes", "Sub"),
        grid(
            ["Evento", "Resposta"],
            [
                ["Gate vermelho", "Nova sessão de correção; consome um ciclo"],
                ["Limite do modelo Antigravity", "Próximo modelo da rota; mesma fase; não consome ciclo"],
                ["Todas as rotas limitadas", "Aguarda reset e repete a mesma fase"],
                ["Fase falha após máximo de ciclos", "Para por padrão; --keep-going continua"],
                ["Mudança parcial", "Permanece na árvore para diagnóstico e revisão"],
            ],
            [58, 116],
        ),
        callout("IDEMPOTÊNCIA", "A troca de modelo reapresenta a fase completa. Por isso, tasks devem ser seguras para rechecagem e efeitos externos precisam estar claramente sinalizados para revisão humana.", YELLOW),
        PageBreak(),
    ]

    story += section("13", "Dashboard e observabilidade", "ACOMPANHAR SEM CONTROLAR")
    story += [
        code("# Painel de terminal em outro terminal\n./scripts/ralph-watch.sh /caminho/do/projeto\n\n# Dashboard web local\n./scripts/ralph-web.sh /caminho/do/projeto\n# abrir http://127.0.0.1:7331"),
        para("O dashboard é somente leitura e escuta apenas no computador local. Ele mostra run, engine, modelo, perfil, fase, task, ciclo, gates, atividade, duração, logs e histórico quando esses dados estão disponíveis no estado."),
        para("Arquivos de diagnóstico", "Sub"),
        grid(
            ["Caminho", "Conteúdo"],
            [
                [".phases/current", "Ponteiro para o run atual"],
                [".phases/runs/<run>/logs/", "Saída de implementação e verificação"],
                [".phases/runs/<run>/prompts/", "Prompt autocontido de cada sessão"],
                [".phases/runs/<run>/state/", "Estado consolidado e progresso ao vivo"],
                [".phases/progress/", "Fases concluídas por hash do input"],
                [".phases/.ralph.lock/", "Trava contra dois Ralphs no mesmo repositório"],
            ],
            [72, 102],
        ),
        callout("LIMITAÇÃO INTENCIONAL", "O dashboard não pausa, cancela, retoma nem altera a execução. Controle operacional permanece no terminal e no processo do Ralph.", GREEN),
        PageBreak(),
    ]

    story += section("14", "Ciclo de validação e commit", "CHECKPOINT HUMANO")
    story += [
        para("Quando os gates ficarem verdes, ainda existe uma etapa humana. O objetivo é criar um ponto estável antes de continuar o desenvolvimento."),
        code("git status --short\ngit diff --check\ngit diff\n# executar validação manual do fluxo\ngit add <arquivos-revisados>\ngit commit -m 'feat: entrega a fase validada'"),
        checklist([
            "Revisar todos os arquivos alterados, inclusive não rastreados.",
            "Confirmar que o diff corresponde somente à fase executada.",
            "Executar validação manual dos critérios de aceite relevantes.",
            "Conferir migrations, permissões, logs e rollback quando aplicável.",
            "Criar o commit somente depois da revisão.",
            "Iniciar o próximo ciclo a partir desse checkpoint.",
        ]),
        callout("POR QUE O COMMIT É MANUAL", "O commit registra uma decisão humana. Ele separa as execuções, facilita comparação, rollback e retomada, e impede que o agente consolide mudanças que ninguém revisou.", BLUE),
        PageBreak(),
    ]

    story += section("15", "Diagnóstico rápido", "QUANDO ALGO NÃO FUNCIONA")
    story += [
        grid(
            ["Sintoma", "Ação"],
            [
                ["CLI não encontrada", "Instalar a engine e confirmar --version"],
                ["Falha de autenticação", "Abrir a CLI interativa e concluir o login oficial"],
                ["Antigravity sem modelo", "Executar agy models e atualizar model-policy.tsv"],
                ["G0 vermelho", "Ler o final do log da sessão e o evento terminal"],
                ["G2 vermelho", "Executar o mesmo comando de teste fora do Ralph"],
                ["G3 vermelho", "Ler o log verify; identificar tasks INCOMPLETE"],
                ["Painel parado", "Conferir run.tsv, live.tsv e marcadores RALPH-TASK"],
                ["Run concorrente", "Confirmar o processo ativo; não apagar lock de um processo vivo"],
                ["Plano mudou", "Encerrar o run, revisar PHASES.md e iniciar novo ciclo"],
                ["Árvore já estava suja", "Separar visualmente mudanças antigas e novas antes do commit"],
            ],
            [58, 116],
        ),
        Spacer(1, 5 * mm),
        para("Validação do próprio harness", "Sub"),
        code("./scripts/check-shell.sh\n./scripts/test-ralph.sh\ngit diff --check"),
        callout("NÃO MASCARAR", "Não desligue testes, Gate 3 ou validações apenas para deixar a fase verde. Corrija a causa ou registre conscientemente a limitação.", RED),
        PageBreak(),
    ]

    story += section("16", "Adoção na empresa", "COMEÇAR PEQUENO E PADRONIZAR")
    story += [
        checklist([
            "Publicar o harness em um repositório interno com versão e changelog.",
            "Definir quais engines e assinaturas a empresa permite.",
            "Definir política padrão de modelos por papel e revisar nomes periodicamente.",
            "Criar um projeto piloto pequeno, com testes confiáveis e baixo risco.",
            "Treinar a equipe no ciclo Plan -> Task Builder -> Ralph -> revisão -> commit.",
            "Exigir branch própria e comando de testes em toda execução.",
            "Coletar falhas reais antes de aumentar a automação.",
            "Rodar check-skill-drift e testar instalação em uma máquina piloto antes de atualizar a distribuição.",
        ]),
        Spacer(1, 5 * mm),
        para("Responsabilidades", "Sub"),
        grid(
            ["Papel", "Responsabilidade"],
            [
                ["Produto/solicitante", "PRD, prioridade e critérios de aceite"],
                ["Desenvolvedor", "Plan, revisão de tarefas, execução e commit"],
                ["Líder técnico", "Política de engines/modelos, arquitetura e exceções"],
                ["Segurança/infra", "Segredos, permissões, rede e ambientes"],
                ["Harness", "Orquestração, gates, estado, logs e continuidade"],
            ],
            [50, 124],
        ),
        callout("PRIMEIRA META", "Não tente automatizar toda a empresa de uma vez. Primeiro prove um ciclo completo e repetível em um projeto real, mantendo o commit manual como checkpoint.", GREEN),
        PageBreak(),
    ]

    story += section("17", "Referência rápida", "COPIAR, ADAPTAR E EXECUTAR")
    story += [
        para("Projeto novo", "Sub"),
        code("PRD -> Plan (Opus / Pro High) -> revisar fases\n-> Task Builder da próxima fase -> revisar PHASES.md\n-> Ralph (Flash / perfil standard) -> gates\n-> validação manual -> commit"),
        para("Projeto legado", "Sub"),
        code("ai-context -> revisar documentação AS IS\n-> Plan da manutenção -> Task Builder\n-> Ralph -> gates -> regressão manual -> commit"),
        para("Comandos Ralph", "Sub"),
        code("./scripts/ralph.sh --engine codex PHASES.md\n./scripts/ralph.sh --engine claude PHASES.md\n./scripts/ralph.sh --engine opencode PHASES.md\n./scripts/ralph.sh --engine antigravity --profile standard PHASES.md"),
        para("Decisão de modelo", "Sub"),
        grid(
            ["Situação", "Escolha inicial"],
            [
                ["Planejamento e decisões pesadas", "Claude Opus; fallback Gemini 3.1 Pro High"],
                ["Execução comum", "Gemini 3.8 Flash High"],
                ["Execução repetitiva", "Gemini 3.8 Flash Medium"],
                ["Refatoração/arquitetura complexa", "Gemini 3.1 Pro High; fallback Opus"],
                ["Verificação", "Claude Sonnet; fallback Flash High"],
            ],
            [73, 101],
        ),
        PageBreak(),
    ]

    story += section("18", "Fontes e notas de versão", "DOCUMENTAÇÃO CONSULTADA")
    story += [
        para("As instruções de instalação e autenticação abaixo foram conferidas em documentação oficial. A lista de modelos Antigravity foi também conferida na CLI instalada durante a preparação deste guia."),
        source_link("OpenAI - Codex CLI e login com ChatGPT", "https://help.openai.com/en/articles/11381614-api-codex-cli-and-sign-in-with-chatgpt"),
        Spacer(1, 2 * mm),
        source_link("Anthropic - instalação do Claude Code", "https://docs.anthropic.com/en/docs/claude-code/getting-started"),
        Spacer(1, 2 * mm),
        source_link("OpenCode - instalação e CLI", "https://opencode.ai/v2/docs"),
        Spacer(1, 2 * mm),
        source_link("Google - Antigravity CLI, modelos e modo headless", "https://codelabs.developers.google.com/antigravity-cli-hands-on"),
        Spacer(1, 6 * mm),
        callout("INFORMAÇÃO VOLÁTIL", "Modelos, planos, limites, comandos de autenticação e disponibilidade por assinatura podem mudar. Antes de um rollout corporativo, revise a documentação oficial e execute os comandos de versão/modelos em uma máquina piloto.", YELLOW),
        para("Limitações conhecidas desta edição", "Sub"),
        checklist([
            "As Skills são portáveis por contrato; a interface de chamada ainda varia por engine.",
            "Plan e Task Builder usam a política de modelos como recomendação; a seleção de rota nessas interfaces ainda é manual.",
            "O failover de modelos está implementado para a engine Antigravity; outras engines mantêm seu próprio modelo configurado.",
            "O dashboard é local e somente leitura.",
        ]),
        Spacer(1, 8 * mm),
        para("DEVWORKS Harness - guia de uso interno - edição MVP operacional", "Center"),
    ]
    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(18 * mm, 17 * mm, 174 * mm, 258 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=17 * mm,
        title="DEVWORKS Harness - Guia Completo de Uso",
        author="DEVWORKS",
        subject="Instalação, engines, modelos, projetos novos, legados e operação do Ralph",
    )
    document.addPageTemplates([PageTemplate(id="devworks", frames=[frame], onPage=page_background)])
    document.build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()
