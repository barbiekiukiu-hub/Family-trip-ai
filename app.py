import streamlit as st
import os
import time
import requests
from openai import OpenAI
import dashscope

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="AI Family Travel Pro", page_icon="✈️", layout="wide")
st.title("🌎 AI Family Travel Planner Pro")
st.markdown("### *Your personalized, AI-powered family concierge*")

# API Keys (Update these with your keys)
DEEPSEEK_API_KEY = "sk-34d5bcdbfecc40f3a0bc5a92a29f9acc"
ALIYUN_API_KEY = "sk-1edc10b1c4b041b7935a5c6d76a81de3"

# Initialize Clients
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
dashscope.api_key = ALIYUN_API_KEY

# Initialize Session State (Memory)
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'images' not in st.session_state:
    st.session_state.images = []

# --- 2. HELPER FUNCTIONS ---

def generate_ai_itinerary(prompt_data, system_msg):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt_data}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to AI: {e}"

def generate_multi_images(dest, interests, count=3):
    image_urls = []
    for i in range(count):
        prompt = f"Family travel photography: {dest}, activity involving {interests[i % len(interests)]}, cinematic lighting, 4k, happy family"
        try:
            rsp = dashscope.ImageSynthesis.call(model="wanx-v1", prompt=prompt, size="1024*1024", n=1)
            if rsp.status_code == 200:
                image_urls.append(rsp.output.results[0]['url'])
        except:
            image_urls.append("https://via.placeholder.com/1024?text=Travel+Visual")
    return image_urls

# --- 3. SIDEBAR (User Inputs) ---
with st.sidebar:
    st.header("📍 Trip Preferences")
    dest = st.text_input("Destination City/Country", "Tokyo, Japan")
    days = st.slider("Duration (Days)", 1, 14, 5)
    budget = st.select_slider("Budget Level", options=["Budget", "Standard", "Luxury", "Ultra-Luxe"])
    
    st.divider()
    st.subheader("👨‍👩‍👧‍👦 Family Structure")
    adults = st.number_input("Adults", 1, 10, 2)
    child_count = st.number_input("Children", 0, 10, 0)
    child_ages = []
    if child_count > 0:
        for i in range(child_count):
            age = st.number_input(f"Child {i+1} Age", 0, 18, 5, key=f"age_{i}")
            child_ages.append(age)

    st.divider()
    st.subheader("🎨 Interests")
    # Expanded Choice in Interests
    all_interests = [
        "Theme Parks 🎡", "Nature & Parks 🌳", "Museums & History 🏛️", 
        "Local Food & Markets 🍜", "Shopping 🛍️", "Zoo & Aquariums 🦒",
        "Interactive Science 🧪", "Beaches & Water 🏖️", "Hiking & Adventure 🥾",
        "Photography Spots 📸", "Workshops/Classes 🎨", "Relaxation/Spas 🧘"
    ]
    selected_interests = st.multiselect("Select what you love:", all_interests, default=["Theme Parks 🎡", "Local Food & Markets 🍜"])

    if st.button("🚀 Generate Full Plan", type="primary", use_container_width=True):
        with st.spinner("Crafting your dream trip..."):
            family_info = f"{adults} adults and {len(child_ages)} kids (Ages: {child_ages})"
            main_prompt = f"Plan a {days}-day trip to {dest}. Budget: {budget}. Interests: {', '.join(selected_interests)}. Family: {family_info}."
            sys_msg = "You are a world-class family travel expert. Provide a detailed English itinerary with daily morning/afternoon/evening activities and family tips."
            
            st.session_state.itinerary = generate_ai_itinerary(main_prompt, sys_msg)
            st.session_state.images = generate_multi_images(dest, selected_interests)
            # Reset chat when a new plan is made
            st.session_state.chat_history = [{"role": "assistant", "content": "Your itinerary is ready! How can I adjust it for you?"}]

# --- 4. MAIN LAYOUT ---
col_main, col_chat = st.columns([2, 1], gap="large")

with col_main:
    if st.session_state.itinerary:
        st.header(f"Your Journey to {dest}")
        
        # Image Gallery
        if st.session_state.images:
            idx = st.tabs(["View 1", "View 2", "View 3"])
            for i, tab in enumerate(idx):
                with tab:
                    st.image(st.session_state.images[i], use_container_width=True)
        
        st.markdown("---")
        st.markdown(st.session_state.itinerary)
    else:
        st.info("👈 Fill in your details on the left and click 'Generate' to begin!")

with col_chat:
    st.header("💬 Real-time Adjustments")
    st.write("Need to swap a day? Add a specific museum? Just ask!")
    
    # Display Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if user_adj := st.chat_input("e.g., 'Make Day 3 more outdoor-focused'"):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_adj})
        with st.chat_message("user"):
            st.markdown(user_adj)

        # Generate Adjustment
        with st.chat_message("assistant"):
            adj_sys_msg = "You are refining a travel itinerary. Update the current plan based on user feedback. Stay helpful and warm."
            adj_prompt = f"Current Itinerary: {st.session_state.itinerary}\n\nUser Request: {user_adj}"
            
            new_itinerary = generate_ai_itinerary(adj_prompt, adj_sys_msg)
            st.session_state.itinerary = new_itinerary # Update the main view
            
            response = "I've updated your itinerary based on your request! Check the main window."
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun() # Refresh to show changes
