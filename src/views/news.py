"""
Live OSINT Crime News View Module
"""
import streamlit as st
from datetime import datetime
from src.services.news_service import fetch_live_news_data

def render_news_view(default_news_key: str):
    st.markdown("## 📰 Live OSINT Crime News & Intelligence Feed")
    st.write("Real-time Open-Source Intelligence (OSINT) crime news feed powered by **NewsAPI**. Search live crime headlines, monitor breaking operational developments, and chat with AI to summarize news reports.")
    
    with st.expander("⚙️ NewsAPI Key & Feed Settings", expanded=False):
        user_news_key = st.text_input("NewsAPI Key", value=st.session_state.get("news_api_key", default_news_key), type="password", key="txt_news_api_key_input")
        if st.button("Save NewsAPI Key", key="btn_save_news_key"):
            st.session_state["news_api_key"] = user_news_key
            st.success("NewsAPI Key updated successfully!")
            st.rerun()
            
    active_news_key = st.session_state.get("news_api_key", default_news_key)
    
    st.markdown("##### 🔍 Quick News Search Filters:")
    n_col1, n_col2, n_col3, n_col4, n_col5 = st.columns(5)
    
    selected_query = None
    with n_col1:
        if st.button("📍 Pune Crime News", key="chip_news_pune"):
            selected_query = "Pune crime"
    with n_col2:
        if st.button("🚨 Maharashtra Police", key="chip_news_mh"):
            selected_query = "Maharashtra police crime"
    with n_col3:
        if st.button("💻 India Cybercrime", key="chip_news_cyber"):
            selected_query = "India cybercrime fraud"
    with n_col4:
        if st.button("💊 Narcotics Seizures", key="chip_news_narcotics"):
            selected_query = "Pune narcotics drugs arrest"
    with n_col5:
        if st.button("⚖️ Court & Legal News", key="chip_news_legal"):
            selected_query = "Pune police court arrest"

    st.markdown("<br>", unsafe_allow_html=True)
    
    search_input = st.text_input("Enter News Search Topic or Location", value="Pune crime", placeholder="e.g. Pune crime, Hinjawadi fraud, Maharashtra police...", key="txt_news_search_query")
    query_to_run = selected_query if selected_query else search_input
    
    with st.spinner(f"📡 Fetching live crime news for '{query_to_run}' via NewsAPI..."):
        articles, news_err = fetch_live_news_data(query_to_run, active_news_key)
        
    tab_news_feed, tab_news_chat = st.tabs([
        f"📰 Live News Feed ({len(articles)} Articles)",
        "🤖 Ask AI News Analyst"
    ])
    
    with tab_news_feed:
        if news_err:
            st.error(f"⚠️ NewsAPI Fetch Error: {news_err}")
            st.info("Please make sure your NewsAPI key is valid and active.")
        elif not articles:
            st.warning(f"No news articles found for query: '{query_to_run}'. Try adjusting your search term.")
        else:
            st.caption(f"Showing **{len(articles)}** real-time news articles sorted by latest publication timestamp.")
            for i in range(0, len(articles), 2):
                col_art1, col_art2 = st.columns(2)
                with col_art1:
                    art = articles[i]
                    source_name = art.get("source", {}).get("name", "News Source")
                    pub_time = art.get("publishedAt", "")[:10]
                    title = art.get("title", "No Title")
                    desc = art.get("description") or art.get("content") or "No description summary available."
                    url = art.get("url", "#")
                    
                    st.markdown(f"""
                    <div style="background-color: rgba(17, 24, 39, 0.7); border: 1px solid rgba(75, 85, 99, 0.4); border-radius: 12px; padding: 18px; margin-bottom: 20px; height: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="background-color: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); padding: 3px 10px; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">{source_name}</span>
                            <span style="color: #9ca3af; font-size: 0.8rem;">📅 {pub_time}</span>
                        </div>
                        <h4 style="margin: 8px 0; font-size: 1.05rem; line-height: 1.3;"><a href="{url}" target="_blank" style="color: #60a5fa; text-decoration: none;">{title}</a></h4>
                        <p style="color: #d1d5db; font-size: 0.85rem; line-height: 1.4; margin-bottom: 12px;">{desc[:220]}...</p>
                        <a href="{url}" target="_blank" style="display: inline-block; background-color: #2563eb; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 600;">🔗 Read Full Article</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                if i + 1 < len(articles):
                    with col_art2:
                        art = articles[i + 1]
                        source_name = art.get("source", {}).get("name", "News Source")
                        pub_time = art.get("publishedAt", "")[:10]
                        title = art.get("title", "No Title")
                        desc = art.get("description") or art.get("content") or "No description summary available."
                        url = art.get("url", "#")
                        
                        st.markdown(f"""
                        <div style="background-color: rgba(17, 24, 39, 0.7); border: 1px solid rgba(75, 85, 99, 0.4); border-radius: 12px; padding: 18px; margin-bottom: 20px; height: 100%;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="background-color: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); padding: 3px 10px; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">{source_name}</span>
                                <span style="color: #9ca3af; font-size: 0.8rem;">📅 {pub_time}</span>
                            </div>
                            <h4 style="margin: 8px 0; font-size: 1.05rem; line-height: 1.3;"><a href="{url}" target="_blank" style="color: #60a5fa; text-decoration: none;">{title}</a></h4>
                            <p style="color: #d1d5db; font-size: 0.85rem; line-height: 1.4; margin-bottom: 12px;">{desc[:220]}...</p>
                            <a href="{url}" target="_blank" style="display: inline-block; background-color: #2563eb; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 600;">🔗 Read Full Article</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
    with tab_news_chat:
        st.markdown("### 🤖 Live AI Crime News Intelligence Analyst")
        st.write("Ask any question about today's crime headlines or real-time news reports. The AI cross-references the live fetched NewsAPI articles and provides an executive intelligence briefing.")
        
        api_key = st.session_state.get("llm_api_key", "")
        provider = st.session_state.get("llm_provider", "Gemini")
        model_name = st.session_state.get("llm_model", "gemini-1.5-flash")
        
        if not api_key:
            st.info("💡 **LLM API Key Required**: Please configure and save your API Key in the **💬 AI Intel Chatbot** tab above to interact with the AI News Analyst.")
            
        if "news_messages" not in st.session_state:
            st.session_state.news_messages = []
            
        st.markdown("##### 💡 Suggested News Queries:")
        nq_col1, nq_col2, nq_col3 = st.columns(3)
        clicked_news_q = None
        with nq_col1:
            if st.button("📰 What are today's top crime news in Pune?", key="chip_nq_top_pune"):
                clicked_news_q = "What are today's top crime headlines and news reports in Pune?"
        with nq_col2:
            if st.button("💻 Summarize latest cybercrime & fraud news", key="chip_nq_cyber"):
                clicked_news_q = "Summarize the latest cybercrime and financial fraud reports from the news."
        with nq_col3:
            if st.button("🚨 List recent police arrests & seizures", key="chip_nq_arrests"):
                clicked_news_q = "List key recent police arrests, narcotics seizures, and major investigations from the news feed."
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        for nmsg in st.session_state.news_messages:
            with st.chat_message(nmsg["role"]):
                st.markdown(nmsg["content"])
                
        news_user_input = st.chat_input("Ask a question about the live crime news feed...")
        news_prompt = clicked_news_q if clicked_news_q else news_user_input
        
        if news_prompt:
            if not api_key:
                st.warning("Please save your API Key in the '💬 AI Intel Chatbot' tab first.")
            else:
                with st.chat_message("user"):
                    st.markdown(news_prompt)
                st.session_state.news_messages.append({"role": "user", "content": news_prompt})
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Analyzing real-time NewsAPI articles and writing OSINT briefing..."):
                        art_snippets = []
                        for idx, a in enumerate(articles[:12]):
                            art_snippets.append(f"[{idx+1}] Source: {a.get('source',{}).get('name')}\nTitle: {a.get('title')}\nDate: {a.get('publishedAt', '')[:10]}\nSnippet: {a.get('description')}\nURL: {a.get('url')}")
                        context_str = "\n\n".join(art_snippets) if art_snippets else "No live articles currently fetched."
                        
                        now_dt = datetime.now()
                        live_dt_str = now_dt.strftime("%A, %d %B %Y, %I:%M:%S %p IST")
                        
                        news_system_prompt = f"""You are the OSINT Crime News Intelligence Analyst for Pune Police Command Center.
CURRENT REAL-TIME SYSTEM DATETIME: {live_dt_str}.

You have access to real-time live news articles fetched via NewsAPI for query '{query_to_run}'.

LIVE FETCHED ARTICLES CONTEXT:
{context_str}

INSTRUCTIONS:
1. Answer the user's question accurately using the live news articles provided above.
2. If articles contain information relevant to the question, synthesize them into a clear, professional police briefing with bullet points and cite the news source.
3. If the user asks for "today's crime" or "latest news", summarize the top articles from the context above. State clearly that this information is live open-source news (OSINT).
4. Maintain an authoritative, factual police intelligence briefing tone.
"""
                        ai_answer = ""
                        try:
                            if provider == "Gemini":
                                import google.generativeai as genai
                                genai.configure(api_key=api_key)
                                m_news = genai.GenerativeModel(model_name, system_instruction=news_system_prompt)
                                ai_answer = m_news.generate_content(news_prompt).text
                            else:
                                from openai import OpenAI
                                base_urls = {
                                    "OpenAI": None,
                                    "OpenRouter": "https://openrouter.ai/api/v1",
                                    "Groq": "https://api.groq.com/openai/v1",
                                    "NVIDIA NIM": "https://integrate.api.nvidia.com/v1"
                                }
                                client = OpenAI(api_key=api_key, base_url=base_urls.get(provider))
                                extra_headers = {}
                                if provider == "OpenRouter":
                                    extra_headers = {
                                        "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
                                        "X-Title": "Antigravity Crime Command Center"
                                    }
                                resp = client.chat.completions.create(
                                    model=model_name,
                                    messages=[
                                        {"role": "system", "content": news_system_prompt},
                                        {"role": "user", "content": news_prompt}
                                    ],
                                    extra_headers=extra_headers
                                )
                                ai_answer = resp.choices[0].message.content
                        except Exception as ex_news:
                            ai_answer = f"⚠️ Could not generate AI News Briefing: {ex_news}\n\nPlease verify your LLM API Key settings in the AI Intel Chatbot configuration panel."
                            
                        st.markdown(ai_answer)
                        st.session_state.news_messages.append({"role": "assistant", "content": ai_answer})
                        st.rerun()
