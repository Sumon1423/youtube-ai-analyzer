import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from PIL import Image

st.set_page_config(page_title="YouTube AI Analyzer", layout="wide")
st.title("🎬 YouTube Video & Thumbnail AI Analyzer")

st.sidebar.header("🔑 API Keys Setup")
gemini_api_key = st.sidebar.text_input("Gemini API Key দিন", type="password")
youtube_api_key = st.sidebar.text_input("YouTube API Key দিন", type="password")

if not gemini_api_key or not youtube_api_key:
    st.warning("⚠️ সাইডবারে আপনার Gemini এবং YouTube API Key দিন।")
else:
    genai.configure(api_key=gemini_api_key)
    # আপডেটেড মডেল নেম
    model = genai.GenerativeModel('gemini-2.5-flash')

    tab1, tab2 = st.tabs(["🖼️ থাম্বনেইল এনালাইসিস", "📊 ভিডিও অডিট"])

    with tab1:
        st.subheader("থাম্বনেইল রিভিউ")
        uploaded_image = st.file_uploader("থাম্বনেইল আপলোড করুন", type=["jpg", "png", "jpeg"])
        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Thumbnail", use_container_width=True)
            if st.button("এনালাইজ করুন"):
                with st.spinner("AI থাম্বনেইল বিশ্লেষণ করছে..."):
                    try:
                        prompt = "তুমি একজন প্রফেশনাল ইউটিউব থাম্বনেইল এবং CTR এক্সপার্ট। এই থাম্বনেইলটি গভীরভাবে বিশ্লেষণ করো এবং বাংলা ভাষায় উত্তর দাও: ১. থাম্বনেইলের প্লাস পয়েন্ট ২. সমস্যা বা দুর্বলতা ৩. ভিউ বাড়ানোর জন্য প্রয়োজনীয় পরিবর্তন।"
                        response = model.generate_content([prompt, image])
                        st.success("বিশ্লেষণ সম্পন্ন হয়েছে!")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Gemini API Error: {str(e)}")

    with tab2:
        st.subheader("ভিডিও Performance & SEO Audit")
        video_id = st.text_input("ভিডিওর Video ID দিন:")
        if video_id and st.button("ভিডিও অডিট শুরু করুন"):
            with st.spinner("ইউটিউব ডাটা এনালাইসিস চলছে..."):
                try:
                    youtube = build('youtube', 'v3', developerKey=youtube_api_key)
                    request = youtube.videos().list(part="snippet,statistics", id=video_id)
                    data = request.execute()
                    if data['items']:
                        item = data['items'][0]
                        title = item['snippet']['title']
                        views = item['statistics'].get('viewCount', '0')
                        st.write(f"**ভিডিও টাইটেল:** {title}")
                        st.write(f"**মোট ভিউ:** {views}")
                        
                        ai_prompt = f"ভিডিও টাইটেল: {title}, ভিউ: {views}। এটি কেন কম ভিউ পেল এবং ভিউ বাড়াতে এসইও ও টাইটেলে কী পরিবর্তন দরকার তা বাংলায় বলো।"
                        analysis_res = model.generate_content(ai_prompt)
                        st.markdown(analysis_res.text)
                    else:
                        st.error("ভুল Video ID দেওয়া হয়েছে।")
                except Exception as e:
                    st.error(f"এরর: {str(e)}")
