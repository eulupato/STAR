"""Fundação de agentes/capacidades da STAR.

Os agentes não são personalidades, cérebros independentes ou instâncias da STAR.
Eles são executores especializados acionados pelo STAR Core. A V1.9 implementa
somente capacidades compatíveis com a Foundation; sistemas futuros permanecem
explicitamente marcados como parciais/planejados.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from core.commands import CommandMatch, command_count, command_variables, match_command
from core.thematic_voice import THEMATIC_VOICE_VARIATIONS
from core.weather import WeatherService, format_weather


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    status: str
    roadmap: str
    remote_policy: str


AGENT_SPECS = (
    AgentSpec("voice_command", "Interpreta comandos de voz/texto em intents estruturadas e catálogo temático de estudo.", "available", "V1.9 Foundation", "safe"),
    AgentSpec("computer", "Ações locais simples de computador já suportadas pela Foundation.", "partial", "V1.9 → V4 Operator", "safe-subset"),
    AgentSpec("file", "Busca nominal de arquivos; índice semântico fica para V4.", "partial", "V1.9 → V4 Operator", "read"),
    AgentSpec("research", "Abre pesquisas web quando o modo ONLINE estiver autorizado.", "partial", "V1.9 → V12+ Research", "network"),
    AgentSpec("knowledge", "Consulta conhecimento interno, Física, Química, biblioteca multidisciplinar e Knowledge Packs.", "partial", "V1.9 → V3 Knowledge", "read"),
    AgentSpec("memory", "Memória básica atual; arquitetura episódica/semântica fica para V2.", "partial", "V1.9 → V2 Mind", "read"),
    AgentSpec("project", "Entidades e acompanhamento persistente de projetos.", "planned", "V2/V8", "none"),
    AgentSpec("music", "Spotify e controles multimídia locais disponíveis em escopo limitado.", "partial", "V1.9 → V4 Operator", "safe-subset"),
    AgentSpec(
        "vision",
        "STAR Vision Portal local com webcam, tracking de mãos, portal AR e filtros; análise semântica de cena permanece futura.",
        "partial",
        "V1.9 experimental → V5 Senses",
        "read/local-camera",
    ),
    AgentSpec("device", "Gateway LAN experimental e runtime adaptativo; Device Manager completo é futuro.", "partial", "V1.9 experimental → V9", "read"),
    AgentSpec("cure", "Diagnóstico básico existente; Guardian/Cura inteligente fica para V7.", "partial", "V1.9 → V7 Guardian", "read"),
    AgentSpec("security", "Ações sensíveis aguardam Permission Manager, Audit Log e autenticação forte.", "planned", "V7 Guardian", "block-sensitive"),
    AgentSpec(
        "personal_assistant",
        "Hora/data, conversa contextual e clima atual sob demanda; agenda persistente fica para V8.",
        "partial",
        "V1.9 → V8 Agent",
        "read/network-weather",
    ),
    AgentSpec("web", "Camada operacional mínima de navegador/pesquisa web.", "partial", "V1.9 → V4/V12+", "network"),
    AgentSpec("coding", "Abertura de ferramentas de desenvolvimento; coding agent autônomo não existe ainda.", "partial", "V1.9 → V12+", "safe-subset"),
    AgentSpec("home", "Automação residencial.", "planned", "V9 Ecosystem", "none"),
    AgentSpec("body", "Controle abstrato de corpo/robótica.", "planned", "V10 Embodied", "none"),
    AgentSpec("creation", "Orquestração de projetos criativos na Central de Criação.", "planned", "V6/V12+", "none"),
    AgentSpec("orchestrator", "Coordenação de múltiplos agentes e objetivos longos.", "planned", "V8 Agent", "none"),
)


class AgentManager:
    """Despacha somente capacidades já suportadas e mantém limites do roadmap."""

    def __init__(self, weather_provider: WeatherService | None = None):
        self._specs = {spec.name: spec for spec in AGENT_SPECS}
        self.weather = weather_provider or WeatherService()

    def list(self) -> dict:
        return {name: asdict(spec) for name, spec in self._specs.items()}

    def summary(self) -> str:
        available = [s.name for s in AGENT_SPECS if s.status == "available"]
        partial = [s.name for s in AGENT_SPECS if s.status == "partial"]
        planned = [s.name for s in AGENT_SPECS if s.status == "planned"]
        return (
            f"Agentes/capacidades: {len(AGENT_SPECS)} registrados. "
            f"Disponíveis: {', '.join(available) or 'nenhum'}. "
            f"Parciais: {', '.join(partial) or 'nenhum'}. "
            f"Planejados: {', '.join(planned) or 'nenhum'}."
        )

    def dispatch(self, text: str, *, network_enabled: bool = False, remote: bool = False) -> str | None:
        match = match_command(text)
        if match is None:
            return None

        if remote and not match.remote_safe:
            return (
                "Esse comando é reconhecido, mas exige confirmação local. "
                "A STAR não executa ações sensíveis pelo Watch enquanto o "
                "Permission Manager ainda não estiver implementado."
            )
        return self._execute(match, network_enabled=network_enabled)

    def _execute(self, match: CommandMatch, *, network_enabled: bool) -> str:
        from modules import computer_control as computer

        if match.intent == "agents_status":
            return self.summary()
        if match.intent == "commands_status":
            total = command_count() + THEMATIC_VOICE_VARIATIONS
            return (
                f"Tenho {total} variações auditáveis de comandos de voz: "
                f"{command_count()} operacionais da Foundation + {THEMATIC_VOICE_VARIATIONS} temáticas de estudo, "
                "geradas por intents/slots e combinações sob demanda em vez de milhões de if/else."
            )
        if match.intent == "command_variables":
            variables = command_variables()
            names = ", ".join(sorted(variables))
            return (
                f"Os comandos operacionais aceitam {len(variables)} famílias de variáveis/slots: {names}. "
                "O catálogo temático aceita matéria, tema livre, profundidade, formato, contexto e intenção de estudo."
            )
        if match.intent == "time":
            return computer.local_time()
        if match.intent == "date":
            return computer.local_date()
        if match.intent == "weather_current":
            snapshot = self.weather.current(match.slots.get("location"))
            if snapshot is None:
                return (
                    "Não consegui obter o clima atual agora. "
                    "Posso tentar novamente quando houver conexão e localização disponível."
                )
            return format_weather(snapshot)
        if match.intent == "volume_up":
            return computer.volume_up()
        if match.intent == "volume_down":
            return computer.volume_down()
        if match.intent == "volume_mute":
            return computer.volume_mute()
        if match.intent == "media_toggle":
            return computer.media_play_pause()
        if match.intent == "media_next":
            return computer.media_next()
        if match.intent == "media_previous":
            return computer.media_previous()
        if match.intent == "screenshot":
            return computer.take_screenshot()
        if match.intent == "find_file":
            hits = computer.find_files(match.slots["query"])
            if not hits:
                return "Não encontrei arquivos com esse nome."
            return "Encontrei: " + "; ".join(str(path) for path in hits)
        if match.intent == "open_app":
            target = match.slots["target"]
            if target in {"browser", "spotify", "discord"} and not network_enabled:
                return computer.network_required_message()
            return computer.open_app(target)
        if match.intent == "spotify_search":
            if not network_enabled:
                return computer.network_required_message()
            return computer.spotify_search(match.slots["query"])
        if match.intent == "web_search":
            if not network_enabled:
                return computer.network_required_message()
            return computer.web_search(match.slots["query"])
        if match.intent in {"close_app", "lock_pc"}:
            return (
                "Eu reconheço esse comando, mas ele exige confirmação. "
                "A execução ficará bloqueada até o Permission Manager da STAR."
            )
        return "Comando reconhecido, mas esta capacidade ainda não está disponível."