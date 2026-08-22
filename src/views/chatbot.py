"""
AI Intelligence Chatbot View Module
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.services.llm_service import generate_sql_query, execute_safe_query, synthesize_briefing

def render_chatbot_view():
    st.markdown("## 💬 AI Intelligence Chatbot & Natural Language SQL Assistant")
    st.write("Ask natural language queries about Pune crime records, suspect registries, gang networks, and district socio-economics. The AI assistant generates verified read-only SQL queries and presents structured intelligence briefings.")

    api_key = st.session_state.get("llm_api_key", "")
    provider = st.session_state.get("llm_provider", "Gemini")
    model_name = st.session_state.get("llm_model", "gemini-1.5-flash")
    
    col_st1, col_st2 = st.columns([3, 1])
    with col_st1:
        if api_key:
            st.markdown(f"**Connection Status**: 🟢 <span style='color: #10B981; font-weight: 700;'>Online</span> &nbsp;|&nbsp; **Provider**: `{provider}` &nbsp;|&nbsp; **Model**: `{model_name}`", unsafe_allow_html=True)
        else:
            st.markdown("**Connection Status**: 🔴 <span style='color: #EF4444; font-weight: 700;'>API Key Required</span>", unsafe_allow_html=True)
    with col_st2:
        if st.button("🗑️ Clear Chat History", key="btn_clear_chat"):
            st.session_state.messages = []
            st.rerun()

    with st.expander("⚙️ API Provider & Key Configuration", expanded=not bool(api_key)):
        config_col1, config_col2, config_col3 = st.columns([1, 1.2, 1.2])
        with config_col1:
            provider_list = ["Gemini", "OpenAI", "OpenRouter", "Groq", "NVIDIA NIM"]
            provider_idx = provider_list.index(provider) if provider in provider_list else 0
            new_provider = st.selectbox("API Provider", provider_list, index=provider_idx, key="cb_provider_sel")
        with config_col2:
            presets = {
                "Gemini": ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.5-pro", "Custom Model"],
                "OpenAI": ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo", "Custom Model"],
                "OpenRouter": ["meta-llama/llama-3-8b-instruct:free", "google/gemma-2-9b-it:free", "mistralai/mistral-7b-instruct:free", "openrouter/auto", "Custom Model"],
                "Groq": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it", "Custom Model"],
                "NVIDIA NIM": ["meta/llama3-70b-instruct", "nvidia/nemotron-4-340b-instruct", "nvidia/llama-3.1-nemotron-70b-instruct", "Custom Model"]
            }
            options = presets.get(new_provider, ["Custom Model"])
            default_idx = options.index(model_name) if model_name in options else (len(options) - 1 if "Custom Model" in options else 0)
            selected_model_option = st.selectbox("Model Version", options, index=default_idx, key="cb_model_option")
            model_name_input = st.text_input("Custom Model Name/ID", value=model_name if model_name not in options else "", key="cb_custom_model_txt") if selected_model_option == "Custom Model" else selected_model_option
                
        with config_col3:
            api_key_input = st.text_input("API Key", type="password", value=api_key, placeholder="Paste your API Key here", key="cb_api_key_input")
            
        btn_c1, btn_c2, _ = st.columns([1, 1, 3])
        with btn_c1:
            if st.button("Save Credentials", key="btn_save_creds"):
                st.session_state["llm_api_key"] = api_key_input
                st.session_state["llm_provider"] = new_provider
                st.session_state["llm_model"] = model_name_input
                st.success("API credentials saved!")
                st.rerun()
        with btn_c2:
            if st.button("Clear Credentials", key="btn_clear_creds"):
                st.session_state["llm_api_key"] = ""
                st.session_state["llm_provider"] = "Gemini"
                st.session_state["llm_model"] = "gemini-1.5-flash"
                st.success("Credentials cleared!")
                st.rerun()

    st.markdown("<hr style='border-top: 1px solid rgba(75, 85, 99, 0.2);'>", unsafe_allow_html=True)

    if not api_key:
        st.info("💡 **API Key Required**: Please expand the settings above and save your Gemini or OpenAI API Key to start chatting with the intelligence database.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.markdown("##### 💡 Suggested Intelligence Queries:")
        chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
        clicked_prompt = None
        with chip_col1:
            if st.button("🔍 Top 5 High-Risk Suspects", key="chip_top_suspects"):
                clicked_prompt = "List top 5 highest risk repeat suspects in Pune with their gang affiliation."
        with chip_col2:
            if st.button("📍 Crimes in Kothrud", key="chip_kothrud_crimes"):
                clicked_prompt = "How many crimes were logged in Kothrud district and what are their severity levels?"
        with chip_col3:
            if st.button("🚨 Open High Severity Cases", key="chip_open_cases"):
                clicked_prompt = "List all open crimes with High severity level across Pune."
        with chip_col4:
            if st.button("👥 Pune Local Boys Gang", key="chip_gang_members"):
                clicked_prompt = "Who are all the suspects affiliated with Pune Local Boys gang?"

        st.markdown("<br>", unsafe_allow_html=True)

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sql_query" in message and message["sql_query"]:
                    with st.expander("🔍 Executed SQL Query"):
                        st.code(message["sql_query"], language="sql")
                if "query_df_json" in message and message["query_df_json"]:
                    with st.expander("📊 Queried Database Records"):
                        try:
                            df_rec = pd.read_json(message["query_df_json"])
                            st.dataframe(df_rec, use_container_width=True, hide_index=True)
                        except Exception:
                            pass
                if "sql_error" in message and message["sql_error"]:
                    st.error(f"SQL Error: {message['sql_error']}")

        chat_user_input = st.chat_input("Ask a question about Pune crime database...")
        prompt_to_process = clicked_prompt if clicked_prompt else chat_user_input

        if prompt_to_process:
            with st.chat_message("user"):
                st.markdown(prompt_to_process)
            st.session_state.messages.append({"role": "user", "content": prompt_to_process})
            
            with st.chat_message("assistant"):
                status_placeholder = st.status("🤖 Analyzing question & writing SQL query...", expanded=True)
                try:
                    sql_query = generate_sql_query(prompt_to_process, provider, model_name, api_key)
                    df_result, query_df_json, sql_error = execute_safe_query(sql_query)
                    
                    if sql_query and not sql_error:
                        status_placeholder.update(label=f"✅ Query complete. Found {len(df_result)} records.", state="complete")
                    elif sql_error:
                        status_placeholder.update(label="❌ SQLite Execution Failed.", state="error")
                    else:
                        status_placeholder.update(label="🤖 Answer generated directly.", state="complete")

                    status_placeholder2 = st.empty()
                    status_placeholder2.info("📝 Formulating response briefing...")
                    
                    final_answer = synthesize_briefing(prompt_to_process, sql_query, query_df_json, sql_error, provider, model_name, api_key)
                    status_placeholder2.empty()
                    st.markdown(final_answer)
                    
                    if sql_query:
                        with st.expander("🔍 Executed SQL Query"):
                            st.code(sql_query, language="sql")
                    if df_result is not None and not df_result.empty:
                        with st.expander("📊 Queried Database Records"):
                            st.dataframe(df_result, use_container_width=True, hide_index=True)
                    if sql_error:
                        st.error(f"SQL Error: {sql_error}")
                        
                    msg_obj = {"role": "assistant", "content": final_answer}
                    if sql_query:
                        msg_obj["sql_query"] = sql_query
                    if query_df_json:
                        msg_obj["query_df_json"] = query_df_json
                    if sql_error:
                        msg_obj["sql_error"] = sql_error
                        
                    st.session_state.messages.append(msg_obj)
                    st.rerun()
                except Exception as ex:
                    status_placeholder.update(label="? Failed to connect to API or parse response.", state="error")
                    st.error(f"Error: {ex}")
                    st.info("Please make sure your API key is valid and you have an active internet connection.")
