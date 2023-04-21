import streamlit as st

def errorsearch(access_token, user_id):
    user_input = st.text_area("Describe What Issue you are Facing", height=200)
    if st.button("Search"):
        st.write("Searching")

if __name__ == "__main__":
    errorsearch()