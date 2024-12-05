# frontend.py

import base64
import streamlit as st
import requests
import os
import pandas as pd
from CBFRS import MultilingualMovieRecommender
import emoji


# Helper Functions
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_jpg_as_page_bg(jpg_file):
    bin_str = get_base64_of_bin_file(jpg_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# set background image
set_jpg_as_page_bg('resources/movie_background3.jpg')

# set css
st.markdown("""
<style>
.block-container h1, .block-container h2, .block-container h3,
.block-container h4, .block-container h5, .block-container h6,
.block-container p, .block-container span, .block-container div,
.block-container label {
    color: white !important;
}

.block-container a {
    color: #ADD8E6 !important;
}

.block-container .stButton button {
    color: white !important;
    background-color: #1E90FF !important; 
    border: none !important;
    border-radius: 5px !important;
    padding: 10px 20px !important;
    font-size: 16px !important;
    cursor: pointer !important;
}

.block-container .stButton button:hover {
    background-color: #63B3ED !important; 
}

.single-line {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    background-color: rgba(0, 0, 0, 0.5); 
    padding: 2px 4px;
    border-radius: 4px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7); 
}
</style>
""", unsafe_allow_html=True)

# load recommender system, cache to boot the performance
@st.cache_resource
def load_recommender():
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    recommender = MultilingualMovieRecommender(
        movies_path='Data/enriched_movies.csv',
        tmdb_api_key=TMDB_API_KEY
    )
    return recommender

recommender = load_recommender()

def get_movie_trailer(tmdb_id):
    api_key = os.getenv("TMDB_API_KEY")
    videos_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}/videos'
    videos_params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    videos_response = requests.get(videos_url, params=videos_params)
    if videos_response.status_code == 200:
        videos_data = videos_response.json()
        videos = videos_data.get('results', [])
        for video in videos:
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                youtube_key = video['key']
                trailer_url = f'https://www.youtube.com/watch?v={youtube_key}'
                return trailer_url
    return None

def get_movie_info_by_id(tmdb_id):
    api_key = os.getenv("TMDB_API_KEY")
    details_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}'
    details_params = {
        'api_key': api_key,
        'language': 'en-US'
    }
    details_response = requests.get(details_url, params=details_params)
    if details_response.status_code == 200:
        details = details_response.json()
        poster_path = details.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        # get trailer
        trailer_url = get_movie_trailer(tmdb_id)

        movie_info = {
            'tmdb_id': tmdb_id,
            'title': details.get('title', 'N/A'),
            'release_date': details.get('release_date', 'N/A'),
            'synopsis': details.get('overview', 'N/A'),
            'poster_url': poster_url,
            'trailer_url': trailer_url
        }
        return movie_info
    else:
        st.error("No info available")
        return None

def get_popular_movies():
    api_key = os.getenv("TMDB_API_KEY")
    popular_url = 'https://api.themoviedb.org/3/movie/popular'
    params = {
        'api_key': api_key,
        'language': 'en-US',
        'page': 1
    }

    response = requests.get(popular_url, params=params)
    if response.status_code == 200:
        data = response.json()
        movies = data['results']
        popular_movies = []
        for movie in movies:
            poster_path = movie.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            trailer_url = get_movie_trailer(movie.get('id'))

            movie_info = {
                'id': movie.get('id'),
                'title': movie.get('title', 'N/A'),
                'release_date': movie.get('release_date', 'N/A'),
                'synopsis': movie.get('overview', 'N/A'),
                'poster_url': poster_url,
                'trailer_url': trailer_url
            }
            popular_movies.append(movie_info)
        return popular_movies
    else:
        st.error("Unable to fetch popular movies")
        return None

# set header
st.title(emoji.emojize("🎬 Movie Recommendation System"))

# set sub header
st.subheader(emoji.emojize("✨ Explore Trending Movies"))
popular_movies = get_popular_movies()

if popular_movies:
    # 5 columns for layout
    cols = st.columns(5)
    for idx, movie in enumerate(popular_movies[:10]):
        with cols[idx % 5]:
            if movie['poster_url']:
                st.image(movie['poster_url'])
            else:
                st.write("No Poster Available")
            # add css
            st.markdown(f"<p class='single-line'>{movie['title']}</p>", unsafe_allow_html=True)

            # add play button
            if movie.get('trailer_url'):
                if st.button('▶️ Play Trailer', key=f"trailer_{movie['id']}"):
                    with st.expander("▶️ Trailer"):
                        st.video(movie['trailer_url'])
            else:
                st.write("No Trailer Available")

# Movie Searching
movie_name = st.text_input("🔍 Begin Searching")

if movie_name:
    movie_infos = recommender.find_movie_by_search(movie_name)
    if movie_infos:
        # Add select box for multiple recommendation result
        if len(movie_infos) > 1:
            options = []
            for info in movie_infos:
                # unboxing tuple
                idx, title, tmdb_id = info
                if title:
                    release_year = get_movie_info_by_id(tmdb_id)['release_date'][:4] if get_movie_info_by_id(tmdb_id) else 'N/A'
                    display_title = f"{title} ({release_year})"
                else:
                    display_title = f"TMDB ID {tmdb_id}"
                options.append(display_title)
            selected_option = st.selectbox("Please select a movie:", options)
            selected_index = options.index(selected_option)
            selected_movie_info_tuple = movie_infos[selected_index]
            tmdb_id = selected_movie_info_tuple[2]
            movie_info = get_movie_info_by_id(tmdb_id)
        else:
            selected_movie_info_tuple = movie_infos[0]
            tmdb_id = selected_movie_info_tuple[2]
            movie_info = get_movie_info_by_id(tmdb_id)

        if movie_info:
            # display movie detail
            col1, col2 = st.columns(2)
            with col1:
                if movie_info["poster_url"]:
                    st.image(movie_info["poster_url"])
                else:
                    st.write("No Poster")
            with col2:
                st.markdown(f"### {movie_info['title']}")
                st.write(f"**Release Date:** {movie_info['release_date']}")
                st.write(movie_info['synopsis'])

            if movie_info['trailer_url']:
                if st.button('▶️ Play Trailer', key='search_movie_trailer'):
                    with st.expander("▶️ Trailer"):
                        st.video(movie_info['trailer_url'])
            else:
                st.write("No Trailer Available")

            # add sider bar to display
            recommendations = recommender.get_movie_recommendations(
                search_title=movie_info['title'],
                n_recommendations=5,
                min_rating=7.0,
                min_votes=1000
            )

            if recommendations is not None and not recommendations.empty:
                st.sidebar.header(emoji.emojize("🔍 Similar Movies"))
                for _, rec in recommendations.iterrows():
                    tmdb_id = rec['tmdb_id']
                    rec_title = rec['title']
                    rec_search_url = f"https://www.themoviedb.org/movie/{tmdb_id}"

                    # set poster url
                    if 'poster_path' in rec and rec['poster_path']:
                        poster_url = f"https://image.tmdb.org/t/p/w500{rec['poster_path']}"
                    else:
                        details_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}'
                        params = {'api_key': os.getenv("TMDB_API_KEY")}
                        details_response = requests.get(details_url, params=params)
                        if details_response.status_code == 200:
                            details = details_response.json()
                            poster_path = details.get('poster_path')
                            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                        else:
                            poster_url = None

                    # display poster
                    if poster_url:
                        st.sidebar.image(poster_url, width=100)
                    else:
                        st.sidebar.write("No Poster")

                    # get trailer url
                    trailer_url = get_movie_trailer(tmdb_id)
                    if trailer_url:
                        st.sidebar.markdown(f"[▶️ Play Trailer]({trailer_url})")
                    else:
                        st.sidebar.write("No Trailer")

                    st.sidebar.markdown("---")
            else:
                st.sidebar.write("No Similar Movies")
    else:
        st.error("No movie info")
else:
    st.write("Begin Searching")
