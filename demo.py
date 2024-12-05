# frontend.py

import base64
import streamlit as st
import requests
import os
import pandas as pd
from CBFRS import MultilingualMovieRecommender


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


# Set background image
set_jpg_as_page_bg('resources/movie_background3.jpg')

# Set font colors and styles
st.markdown("""
<style>
/* Set text to white, but exclude input and textarea elements */
.block-container h1, .block-container h2, .block-container h3,
.block-container h4, .block-container h5, .block-container h6,
.block-container p, .block-container span, .block-container div,
.block-container label {
    color: white !important;
}

/* Set links to light blue */
.block-container a {
    color: #ADD8E6 !important;
}

/* Style the buttons */
.block-container .stButton button {
    color: white !important;
    background-color: #1E90FF !important; 
    border: none !important;
    border-radius: 5px !important;
    padding: 10px 20px !important;
    font-size: 16px !important;
    cursor: pointer !important;
}

/* Hover effect for buttons */
.block-container .stButton button:hover {
    background-color: #63B3ED !important; 
}

/* Transparency and shadow for single-line text */
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


# Load the recommender with caching to improve performance
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
    """
    Fetch the trailer URL for a given TMDB movie ID.
    """
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


def get_movie_info(name):
    """
    Fetch movie details using TMDB API.
    """
    api_key = os.getenv("TMDB_API_KEY")
    # Get movie data
    search_url = f'https://api.themoviedb.org/3/search/movie'
    params = {
        'api_key': api_key,
        'query': name,
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            # Get first result
            movie = data['results'][0]
            movie_id = movie['id']

            # Get detailed info
            details_url = f'https://api.themoviedb.org/3/movie/{movie_id}'
            details_params = {
                'api_key': api_key,
            }
            details_response = requests.get(details_url, params=details_params)
            if details_response.status_code == 200:
                details = details_response.json()
                poster_path = details.get('poster_path')
                if poster_path:
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                else:
                    poster_url = None

                # Get trailer URL
                trailer_url = get_movie_trailer(movie_id)

                movie_info = {
                    'tmdb_id': movie_id,
                    'title': details.get('title', 'N/A'),
                    'release_date': details.get('release_date', 'N/A'),
                    'synopsis': details.get('overview', 'information unavailable'),
                    'poster_url': poster_url,
                    'trailer_url': trailer_url
                }
                return movie_info
            else:
                st.error("Cannot get movie detail")
                return None
        else:
            st.error("Do not found matching movie")
            return None
    else:
        st.error("request failed")
        return None


def get_popular_movies():
    """
    Fetch popular movies using TMDB API.
    """
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
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                poster_url = None

            trailer_url = get_movie_trailer(movie.get('id'))

            movie_info = {
                'id': movie.get('id'),
                'title': movie.get('title', 'N/A'),
                'release_date': movie.get('release_date', 'N/A'),
                'synopsis': movie.get('overview', 'information unavailable'),
                'poster_url': poster_url,
                'trailer_url': trailer_url
            }
            popular_movies.append(movie_info)
        return popular_movies
    else:
        st.error("Cannot fetch popular movie list")
        return None

def get_poster_url(tmdb_id):
    details_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}'
    params = {'api_key': os.getenv("TMDB_API_KEY")}
    details_response = requests.get(details_url, params=params)
    if details_response.status_code == 200:
        details = details_response.json()
        poster_path = details.get('poster_path')
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        else:
            poster_url = None
    else:
        poster_url = None
    return poster_url
# set title
st.title("🎬 Movie Recommendation System")

# set sub header
st.subheader("✨ Explore Trending movies")
popular_movies = get_popular_movies()

if popular_movies:
    # set columns for layout purpose
    cols = st.columns(5)
    for idx, movie in enumerate(popular_movies[:10]):
        with cols[idx % 5]:
            if movie['poster_url']:
                st.image(movie['poster_url'])
            else:
                st.write("poster unavailable")
            # add css effect
            st.markdown(f"<p class='single-line'>{movie['title']}</p>", unsafe_allow_html=True)

            # add play button
            if movie.get('trailer_url'):
                if st.button('▶️ play trailer', key=f"trailer_{movie['id']}"):
                    with st.expander("▶️ trailer"):
                        st.video(movie['trailer_url'])
            else:
                st.write("trailer unavailable")

# movie searching
movie_name = st.text_input("🔍 Begin Searching")

if movie_name:
    movie_info = get_movie_info(movie_name)
    if movie_info:
        col1, col2 = st.columns(2)
        with col1:
            if movie_info["poster_url"]:
                st.image(movie_info["poster_url"])
            else:
                st.write("poster unavailable")
        with col2:
            st.markdown(f"### {movie_info['title']}")
            st.write(f"**release date:** {movie_info['release_date']}")
            st.write(movie_info['synopsis'])

        if movie_info['trailer_url']:
            if st.button('▶️ play trailer', key='search_movie_trailer'):
                with st.expander("▶️ trailer"):
                    st.video(movie_info['trailer_url'])
        else:
            st.write("No trailer")
    else:
        st.error("No movie detail。")

    # display movie on sidebar
    recommendations = recommender.get_movie_recommendations(
        search_title=movie_name,
        n_recommendations=5,
        min_rating=7.0,
        min_votes=1000
    )

    if recommendations is not None and not recommendations.empty:
        st.sidebar.header("🔍 Similar movies you might be interested in")
        for _, rec in recommendations.iterrows():
            tmdb_id = rec['tmdb_id']
            rec_title = rec['title']
            # set poster url
            poster_url = get_poster_url(tmdb_id)
            # display poster
            if poster_url:
                st.sidebar.image(poster_url, width=100)
            else:
                st.sidebar.write("No poster available")

            # Get trailer url
            trailer_url = get_movie_trailer(tmdb_id)
            if trailer_url:
                st.sidebar.markdown(f"[▶️ play trailer]({trailer_url})")
            else:
                st.sidebar.write("no trailer available")

            st.sidebar.markdown("---")
    else:
        st.sidebar.write("No similar movie found。")
else:
    st.write("Enter the name of the movie that you want to search.")
