"""Aceite task 021 — pergunta de inventário no caminho completo de produção.

Antes da 021: "tenho algum sensor registrado?" caía no LLM (gpt-4o-mini) e
entrava em loop de tools até UsageLimitExceeded (503).
Depois da 021: o resolver (G13) responde com o snapshot — ZERO chamadas ao LLM.

Uso: uv run python scripts/repro_inventory_loop.py
"""

from __future__ import annotations

import asyncio

from mqtt_chat.agent.chat_agent import create_chat_agent
from mqtt_chat.agent.deps import UserDeps
from mqtt_chat.clients import firebase as firebase_client
from mqtt_chat.config.settings import get_settings
from mqtt_chat.services import chat_turn as chat_turn_service
from mqtt_chat.services.chat_history import load_message_history

USER_ID = "LLBT5EITCBVjvxXGy8A5GW9tXs83"
USER_MESSAGE = "tenho algum sensor registrado?"


async def main() -> None:
    settings = get_settings()
    print(f"modelo configurado: {settings.chat_model}")

    db = firebase_client.get_firestore_client(settings)
    assert db is not None, "Firestore não configurado"

    sessions_col = db.collection("users").document(USER_ID).collection("chat_sessions")
    session_ids = [doc.id for doc in sessions_col.list_documents()]
    session_id = next(
        (sid for sid in session_ids if load_message_history(db, USER_ID, sid, 50)),
        session_ids[0],
    )
    print(f"sessão: {session_id}")

    # Prova de zero-LLM: se o resolver NÃO interceptar, run_chat explode aqui.
    llm_called = {"n": 0}
    original_run_chat = chat_turn_service.run_chat

    async def _spy_run_chat(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        llm_called["n"] += 1
        return await original_run_chat(*args, **kwargs)

    chat_turn_service.run_chat = _spy_run_chat  # type: ignore[assignment]

    agent = create_chat_agent(settings)
    deps = UserDeps(
        user_id=USER_ID,
        display_name="André",
        session_id=session_id,
        db=db,
    )

    outcome = await chat_turn_service.execute_chat_turn(
        agent,
        db,
        deps,
        USER_MESSAGE,
        settings.chat_max_turns,
    )

    print(f"\n=== RESULTADO ===")
    print(f"chamadas ao LLM (run_chat): {llm_called['n']}")
    print(f"scope: {outcome.scope} | persist: {outcome.persist}")
    print(f"suggested_ui: {outcome.suggested_ui}")
    print(f"reply:\n{outcome.reply}")

    if llm_called["n"] == 0:
        print("\n✅ ACEITE 021-01: inventário resolvido pelo resolver, zero LLM.")
    else:
        print("\n⚠️ Caiu no LLM — observar nos logs se o loop guard conteve.")


if __name__ == "__main__":
    asyncio.run(main())
