
import json
from typing import TypedDict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from config import get_llm
from prompts import SYSTEM_PROMPT


class MeetingState(TypedDict):
    meeting_details: dict[str, Any]
    agenda: dict[str, Any]


def generate_agenda(state: MeetingState) -> dict:
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=json.dumps(state["meeting_details"], ensure_ascii=False)
        ),
    ])

    content = response.content

    if not isinstance(content, str):
        raise ValueError("The model returned an unexpected response.")

    # Handle models that wrap JSON in Markdown code fences.
    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content[:-3].strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()

    agenda = json.loads(content)

    if not isinstance(agenda, dict):
        raise ValueError("The model did not return a JSON object.")

    items = agenda.get("agenda_items")

    if not isinstance(items, list) or not items:
        raise ValueError("The model returned no agenda items.")

    total = state["meeting_details"]["duration"]

    durations = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("An agenda item has an invalid structure.")

        duration = item.get("duration_minutes")

        if (
            isinstance(duration, bool)
            or not isinstance(duration, int)
            or duration <= 0
        ):
            raise ValueError("An agenda item has an invalid duration.")

        durations.append(duration)

    if sum(durations) != total:
        raise ValueError(
            "Agenda durations do not match the requested meeting duration. "
            "Please try generating again."
        )

    agenda["total_duration_minutes"] = total
    return {"agenda": agenda}


builder = StateGraph(MeetingState)

builder.add_node("generate_agenda", generate_agenda)
builder.add_edge(START, "generate_agenda")
builder.add_edge("generate_agenda", END)

meeting_graph = builder.compile()
