"""Loop guard — corta repetição de tool calls idênticas no mesmo run (task 021-02).

Modelos pequenos (ex.: gpt-4o-mini) podem entrar em loop chamando a mesma tool
com os mesmos argumentos até estourar ``request_limit`` (→ 503). Esta capability
conta chamadas por (tool, args) usando ``ctx.deps.tool_call_counts`` (zerado por
turno) e, na primeira repetição, sobe ``ToolFailed`` — o modelo vê a falha e
finaliza com os dados que já tem, sem consumir retry budget.
"""

from __future__ import annotations

import json

from pydantic_ai import RunContext, ToolFailed
from pydantic_ai.capabilities import Hooks

from mqtt_chat.agent.deps import UserDeps

TOOL_LOOP_CODE = "tool_loop_detected"


def build_loop_guard(*, max_identical_calls: int = 1) -> Hooks:
    """Capability que corta loops de tool: repetição da mesma call → ToolFailed.

    ``max_identical_calls=1``: a primeira chamada passa; a segunda idêntica
    falha com instrução de responder com os dados já obtidos.
    """
    hooks = Hooks()

    @hooks.on.before_tool_execute
    async def _guard(ctx: RunContext[UserDeps], *, call, tool_def, args):  # noqa: ANN001, ANN202
        # Output tools (ex.: final_result) não são function tools; ToolFailed nelas
        # abortaria o run — guarda só se aplica a tools de função.
        if getattr(tool_def, "kind", "function") != "function":
            return args
        key = (call.tool_name, json.dumps(args, sort_keys=True, default=str))
        counts = ctx.deps.tool_call_counts
        counts[key] = counts.get(key, 0) + 1
        if counts[key] > max_identical_calls:
            raise ToolFailed(
                f"{TOOL_LOOP_CODE}: você já obteve esses dados — "
                "responda agora ao usuário com o que tem, sem chamar mais tools."
            )
        return args

    return hooks
