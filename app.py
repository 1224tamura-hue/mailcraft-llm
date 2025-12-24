from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

RELATIONSHIPS: list[str] = ["取引先", "社内（上司）", "社内（同僚）", "お客様"]
PURPOSES: list[str] = ["依頼", "お礼", "謝罪", "日程調整", "質問", "報告"]
TONES: list[str] = ["丁寧", "ふつう", "カジュアル"]
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.3


def init_session_state() -> None:
    defaults: dict[str, str] = {
        "relationship": RELATIONSHIPS[0],
        "purpose": PURPOSES[0],
        "tone": TONES[0],
        "required_info": "",
        "signature": "",
        "subject": "",
        "body": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_inputs(required_info: str) -> bool:
    if not required_info.strip():
        st.warning("必須情報を入力してください。")
        return False
    if len(required_info) < 10:
        st.warning("必須情報が短すぎます。10文字以上入力してください。")
        return False
    if len(required_info) > 4000:
        st.warning("必須情報が長すぎます。4000文字以内にしてください。")
        return False
    return True


def normalize_bullets(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    normalized = []
    for line in lines:
        if not line:
            continue
        if line.startswith("- "):
            normalized.append(line)
        else:
            normalized.append(f"- {line}")
    return "\n".join(normalized)


def build_prompt(
    relationship: str, purpose: str, tone: str, required_info: str, signature: str
) -> str:
    return (
        "あなたはビジネスメール作成アシスタントです。"
        "以下の条件に基づき日本語のメールを作成してください。"
        "必ず次の形式で出力してください。\n\n"
        "件名：...\n"
        "本文：\n"
        "...\n\n"
        f"宛先の関係性: {relationship}\n"
        f"目的: {purpose}\n"
        f"トーン: {tone}\n"
        "必須情報（箇条書き）:\n"
        f"{required_info}\n"
        f"署名: {signature or '（なし）'}\n"
    )


def call_llm(prompt: str) -> str:
    # Keep the call path minimal for stability.
    response = get_llm().invoke(prompt)
    return response.content


@st.cache_resource
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)


def build_rewrite_prompt(subject: str, body: str, instruction: str) -> str:
    return (
        "あなたはビジネスメールの編集アシスタントです。"
        "以下のメール本文を指示に従って書き換えてください。"
        "件名は基本維持し、明らかに不自然なら軽く整える程度にしてください。"
        "必ず次の形式で出力してください。\n\n"
        "件名：...\n"
        "本文：\n"
        "...\n\n"
        f"指示: {instruction}\n"
        f"件名: {subject}\n"
        "本文:\n"
        f"{body}\n"
    )


def parse_output(text: str) -> tuple[str, str]:
    subject = ""
    body = ""
    lines = [line.strip() for line in text.splitlines()]
    subject_prefixes = ("件名：", "件名:")
    body_prefixes = ("本文：", "本文:")
    for idx, line in enumerate(lines):
        if line.startswith(subject_prefixes):
            for prefix in subject_prefixes:
                if line.startswith(prefix):
                    subject = line.replace(prefix, "", 1).strip()
                    break
            continue
        if line.startswith(body_prefixes):
            body = "\n".join(lines[idx + 1 :]).strip()
            break

    if not subject:
        return "（自動生成）", text.strip()
    if not body:
        return subject, text.strip()
    return subject, body


def generate_with_llm() -> tuple[str, str]:
    relationship = st.session_state["relationship"]
    purpose = st.session_state["purpose"]
    tone = st.session_state["tone"]
    required_info = st.session_state["required_info"].strip()
    signature = st.session_state["signature"].strip()
    normalized_required_info = normalize_bullets(required_info)
    prompt = build_prompt(
        relationship=relationship,
        purpose=purpose,
        tone=tone,
        required_info=normalized_required_info,
        signature=signature,
    )
    output = call_llm(prompt)
    return parse_output(output)


def handle_generate() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("OPENAI_API_KEY が未設定です。.env を作成してください。")
        return
    required_info = st.session_state["required_info"]
    if not validate_inputs(required_info):
        return
    try:
        with st.spinner("メールを生成中..."):
            subject, body = generate_with_llm()
    except Exception:
        st.error("生成に失敗しました。入力を短くして再試行してください。")
        return
    st.session_state["subject"] = subject
    st.session_state["body"] = body


def handle_rewrite(instruction: str) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("OPENAI_API_KEY が未設定です。.env を作成してください。")
        return
    subject = st.session_state.get("subject", "").strip()
    body = st.session_state.get("body", "").strip()
    if not body:
        st.warning("本文が空のため再生成できません。")
        return
    prompt = build_rewrite_prompt(subject, body, instruction)
    try:
        with st.spinner("メールを調整中..."):
            output = call_llm(prompt)
            new_subject, new_body = parse_output(output)
    except Exception:
        st.error("再生成に失敗しました。入力を短くして再試行してください。")
        return
    if new_subject:
        st.session_state["subject"] = new_subject
    st.session_state["body"] = new_body


def handle_clear() -> None:
    keys = [
        "relationship",
        "purpose",
        "tone",
        "required_info",
        "signature",
        "subject",
        "body",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def render_inputs() -> None:
    st.subheader("入力")
    st.selectbox("宛先の関係性", RELATIONSHIPS, key="relationship")
    st.selectbox("目的", PURPOSES, key="purpose")
    st.radio("トーン", TONES, key="tone", horizontal=True)
    st.text_area("必須情報（箇条書き）", key="required_info", height=160)
    st.text_area("署名（任意）", key="signature", height=80)


def render_outputs() -> None:
    st.subheader("出力")
    st.text_input("件名", key="subject")
    st.text_area("本文", key="body", height=240)
    if st.session_state.get("subject") or st.session_state.get("body"):
        col_polite, col_short = st.columns(2)
        with col_polite:
            st.button(
                "もっと丁寧に",
                on_click=handle_rewrite,
                args=("敬語をより丁寧にし、失礼のない表現にしてください。",),
                use_container_width=True,
            )
        with col_short:
            st.button(
                "もっと短く",
                on_click=handle_rewrite,
                args=(
                    "要点を残して短くしてください。必要なら箇条書き可。"
                    "ただしメールとして自然に。",
                ),
                use_container_width=True,
            )


def render_actions() -> None:
    col_generate, col_clear = st.columns(2)
    with col_generate:
        st.button("生成する", on_click=handle_generate, use_container_width=True)
    with col_clear:
        st.button("入力をクリア", on_click=handle_clear, use_container_width=True)


def main() -> None:
    load_dotenv()
    st.title("メール文章作成")
    st.caption("Streamlit + LLM（ChatOpenAI）でメール文を生成します")
    init_session_state()

    render_inputs()
    render_actions()
    render_outputs()


if __name__ == "__main__":
    main()
