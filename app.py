import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from streamlit_oauth import OAuth2Component
from PIL import Image
import requests
from io import BytesIO

st.set_page_config(page_title="YouTube Channel AI Auditor", layout="wide")
st.title("🎬 YouTube AI Studio & Video Auditor")

# Streamlit Secrets থেকে Client ID, Secret এবং Gemini API Key নেওয়া
CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_TOKEN_URL = "https://oauth2.googleapis.com/revoke"
SCOPE = "https://www.googleapis.com/auth/youtube.readonly"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)

if 'token' not in st.session_state:
    st.session_state['token'] = None

# --- গুগল লগইন বাটন ---
if not st.session_state['token']:
    st.info("👋 আপনার ইউটিউব চ্যানেলের ভিডিও অ্যানালাইসিস করতে নিচে লগইন করুন:")
    # আপনার Streamlit অ্যাপের লিংক redirect_uri-তে দিন
    result = oauth2.authorize_button(
        name="Sign in with Google / YouTube",
        icon="https://www.google.com/favicon.ico",
        redirect_uri="https://youtube-ai-analyzer-bnxjdgxwcb77aey6mvyzvw.streamlit.app",
        scope=SCOPE,
        key="google_auth"
    )
    if result and 'token' in result:
        st.session_state['token'] = result['token']
        st.rerun()

# --- চ্যানেলের ভিডিও প্রদর্শন ও AI এনালাইসিস ---
else:
    st.success("✅ ইউটিউব চ্যানেল সফলভাবে কানেক্ট হয়েছে!")
    if st.button("Logout"):
        st.session_state['token'] = None
        st.rerun()

    if not GEMINI_API_KEY:
        st.warning("⚠️ Streamlit Secrets-এ GEMINI_API_KEY যুক্ত করা হয়নি।")
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-3.6-flash')

        # YouTube API সার্ভিস তৈরি
        creds = Credentials(st.session_state['token']['access_token'])
        youtube = build('youtube', 'v3', credentials=creds)

        try:
            request = youtube.search().list(
                part="snippet",
                mine=True,
                maxResults=12,
                type="video",
                order="date"
            )
            response = request.execute()
            videos = response.get('items', [])

            st.subheader("📹 আপনার চ্যানেলের ভিডিওসমূহ (যেকোনো একটিতে ক্লিক করুন):")

            cols = st.columns(3)
            for index, video in enumerate(videos):
                v_id = video['id']['videoId']
                title = video['snippet']['title']
                thumb_url = video['snippet']['thumbnails']['high']['url']

                col = cols[index % 3]
                with col:
                    st.image(thumb_url, use_container_width=True)
                    st.caption(f"**{title}**")
                    if st.button(f"🔍 এই ভিডিওটি অডিট করুন", key=v_id):
                        st.session_state['selected_video'] = {
                            'id': v_id,
                            'title': title,
                            'thumb_url': thumb_url
                        }

            if 'selected_video' in st.session_state:
                vid = st.session_state['selected_video']
                st.markdown("---")
                st.subheader(f"📊 অডিট রিপোর্ট: {vid['title']}")

                col_img, col_info = st.columns([1, 2])
                with col_img:
                    st.image(vid['thumb_url'], caption="Selected Thumbnail", use_container_width=True)
                
                with col_info:
                    with st.spinner("AI আপনার থাম্বনেইল ও টাইটেল বিশ্লেষণ করে সাজেস্ট তৈরি করছে..."):
                        img_res = requests.get(vid['thumb_url'])
                        image = Image.open(BytesIO(img_res.content))

                        prompt = f"""
                        তুমি একজন ইউটিউব অ্যালগরিদম ও CTR বৃদ্ধি বিশেষজ্ঞ।
                        ভিডিও টাইটেল: '{vid['title']}'
                        
                        উপরে আপলোড করা থাম্বনেইল এবং টাইটেল একসাথে বিশ্লেষণ করে নিচে উত্তরগুলো নিখুঁত বাংলায় দাও:
                        ১. **CTR স্কোর ও সমস্যা:** এই থাম্বনেইল এবং টাইটেলে প্রধান কী ভুল আছে যার কারণে মানুষ ক্লিক কম করতে পারে?
                        ২. **থাম্বনেইল পরিবর্তনের সাজেস্ট:** থাম্বনেইলের কালার, ফন্ট বা ছবিতে কী পরিবর্তন করলে এটি চোখের সামনে ভেসে উঠবে?
                        ৩. **৩টি সেরা নতুন টাইটেল আইডিয়া:** ভিউ ৩ গুণ বাড়ানোর মতো ৩টি আকর্ষণীয় (Click-worthy) নতুন টাইটেল সাজেস্ট করো।
                        """

                        ai_response = model.generate_content([prompt, image])
                        st.markdown(ai_response.text)

        except Exception as e:
            st.error(f"ইউটিউব ভিডিও আনতে সমস্যা হয়েছে: {str(e)}")
