
import json
import streamlit as st

from graph import meeting_graph


st.set_page_config(
    page_title="Smart Meeting Agenda Creator",
    page_icon="📋",
    layout="centered",
)

st.title("📋 Smart Meeting Agenda Creator")
st.write(
    "Turn your meeting objectives into a structured, "
    "time-efficient agenda with AI."
)

with st.form("meeting_form"):
    title = st.text_input(
        "Meeting title",
        placeholder="Weekly project planning",
    )

    objective = st.text_area(
        "Meeting objective",
        placeholder="What should this meeting accomplish?",
    )

    meeting_type = st.selectbox(
        "Meeting type",
        [
            "Team meeting",
            "Project planning",
            "Brainstorming",
            "Client meeting",
            "Sprint review",
            "Other",
        ],
    )

    participants = st.text_input(
        "Participants",
        placeholder="Project manager, developers, designer",
    )

    duration = st.number_input(
        "Meeting duration (minutes)",
        min_value=5,
        max_value=480,
        value=30,
        step=5,
    )

    context = st.text_area(
        "Additional context (optional)",
        placeholder="Topics, constraints, priorities...",
    )

    submitted = st.form_submit_button(
        "Generate Agenda",
        type="primary",
        use_container_width=True,
    )


if submitted:
    if not title.strip() or not objective.strip():
        st.error("Please enter a meeting title and objective.")
    else:
        meeting_details = {
            "title": title.strip(),
            "objective": objective.strip(),
            "meeting_type": meeting_type,
            "participants": participants.strip() or "Not specified",
            "duration": int(duration),
            "additional_context": context.strip() or "None",
        }

        try:
            with st.spinner("Creating your meeting agenda..."):
                result = meeting_graph.invoke({
                    "meeting_details": meeting_details,
                    "agenda": {},
                })

                agenda = result["agenda"]

            st.success("Agenda generated successfully!")

            st.subheader(agenda["meeting_title"])
            st.write(agenda["meeting_objective"])

            st.metric(
                "Total meeting duration",
                f'{agenda["total_duration_minutes"]} minutes',
            )

            st.subheader("Agenda")

            elapsed = 0

            for index, item in enumerate(
                agenda["agenda_items"], start=1
            ):
                minutes = item["duration_minutes"]

                start_time = elapsed
                end_time = elapsed + minutes

                with st.expander(
                    f'{index}. {item["topic"]} — {minutes} min',
                    expanded=True,
                ):
                    st.caption(
                        f"{start_time}–{end_time} minutes"
                    )

                    st.write("**Discussion points**")

                    for point in item["discussion_points"]:
                        st.markdown(f"- {point}")

                    st.write("**Expected outcome**")
                    st.write(item["expected_outcome"])

                elapsed = end_time

            lines = [
                f'Meeting: {agenda["meeting_title"]}',
                f'Objective: {agenda["meeting_objective"]}',
                f'Total duration: {agenda["total_duration_minutes"]} minutes',
                "",
            ]

            elapsed = 0

            for index, item in enumerate(
                agenda["agenda_items"], start=1
            ):
                start_time = elapsed
                end_time = start_time + item["duration_minutes"]

                lines.extend([
                    f'{index}. {item["topic"]}',
                    f'Time: {start_time}–{end_time} minutes',
                    f'Duration: {item["duration_minutes"]} minutes',
                    "Discussion points:",
                ])

                lines.extend(
                    f'- {point}'
                    for point in item["discussion_points"]
                )

                lines.extend([
                    f'Expected outcome: {item["expected_outcome"]}',
                    "",
                ])

                elapsed = end_time

            st.download_button(
                "Download agenda (.txt)",
                data="\n".join(lines),
                file_name="meeting_agenda.txt",
                mime="text/plain",
                use_container_width=True,
            )

        except json.JSONDecodeError:
            st.error(
                "The AI returned an invalid JSON response. "
                "Please try again."
            )
        except Exception as exc:
            st.error(f"Could not generate the agenda: {exc}")
