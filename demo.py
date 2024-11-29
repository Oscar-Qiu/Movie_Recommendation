import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
import os
def get_movie_info(name):
    # load api key from os
    api_key = os.getenv("TMDB_API_KEY")
    # verify it's load it or not
    if not api_key:
        st.error("The API key has not been set")
        return None
    # fetch data
    search_url = f'https://api.themoviedb.org/3/search/movie'
    params = {
        'api_key': api_key,
        'query': name,
        'language': 'zh-CN'
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            # Get the first searching result
            movie = data['results'][0]
            movie_id = movie['id']

            # Get detail info
            details_url = f'https://api.themoviedb.org/3/movie/{movie_id}'
            details_params = {
                'api_key': api_key,
                'language': 'zh-CN'
            }
            details_response = requests.get(details_url, params=details_params)
            if details_response.status_code == 200:
                details = details_response.json()
                poster_path = details.get('poster_path')
                if poster_path:
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                else:
                    poster_url = None

                movie_info = {
                    'title': details.get('title', 'N/A'),
                    'release_date': details.get('release_date', 'N/A'),
                    'synopsis': details.get('overview', 'No info temporarily'),
                    'poster_url': poster_url
                }
                return movie_info
            else:
                st.error("Unable to fetch the detail of the movie.")
                return None
        else:
            st.error("Do not found movie match。")
            return None
    else:
        st.error("request failed。")
        return None
# Set the title of the movie website
st.title("Movie Recommendation")
# A text box for user to enter movie
movie_name = st.text_input("Search movie")
# if the movie name is valid, get the corresponding info
if movie_name:
    movie_info = get_movie_info(movie_name)
    # use columns for layout purpose
    col1,col2 = st.columns(2)
    # col1 is used for movie poster
    with col1:
        st.image(movie_info["poster_url"])
    # col2 is used for meta info
    with col2:
        st.markdown(f"### {movie_info['title']}")
        st.write(f"**Release date：** {movie_info['release_date']}")
        st.write(movie_info['synopsis'])