import streamlit as st
import requests
import os

st.markdown("""
<style>
.single-line {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
""", unsafe_allow_html=True)
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
            }
            details_response = requests.get(details_url, params=details_params)
            if details_response.status_code == 200:
                details = details_response.json()
                poster_path = details.get('poster_path')
                if poster_path:
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                else:
                    poster_url = None

                # Fetch video
                videos_url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos'
                videos_params = {
                    'api_key': api_key,
                }
                videos_response = requests.get(videos_url, params=videos_params)
                if videos_response.status_code == 200:
                    videos_data = videos_response.json()
                    videos = videos_data.get('results', [])
                    trailer_url = None
                    for video in videos:
                        if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                            youtube_key = video['key']
                            trailer_url = f'https://www.youtube.com/watch?v={youtube_key}'
                            break
                else:
                    trailer_url = None

                movie_info = {
                    'title': details.get('title', 'N/A'),
                    'release_date': details.get('release_date', 'N/A'),
                    'synopsis': details.get('overview', 'No info temporarily'),
                    'poster_url': poster_url,
                    'trailer_url': trailer_url
                }
                return movie_info
            else:
                st.error("Unable to fetch the detail of the movie.")
                return None
        else:
            st.error("Do not found movie match.")
            return None
    else:
        st.error("Request failed.")
        return None

def get_popular_movies():
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        st.error("The API key has not been set")
        return None

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

            movie_info = {
                'id': movie.get('id'),  # 添加这一行
                'title': movie.get('title', 'N/A'),
                'release_date': movie.get('release_date', 'N/A'),
                'synopsis': movie.get('overview', 'No info temporarily'),
                'poster_url': poster_url
            }
            popular_movies.append(movie_info)
        return popular_movies
    else:
        st.error("Failed to fetch popular movies.")
        return None

def get_movie_trailer(movie_id):
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        st.error("The API has not been set")
        return None

    videos_url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos'
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

# Set title
st.title("Movie Recommendation System")

# Set sub-header
st.subheader("Explore Trending Movies")
popular_movies = get_popular_movies()

if popular_movies:
    # Set columns for layout
    cols = st.columns(5)
    for idx, movie in enumerate(popular_movies[:10]):
        with cols[idx % 5]:
            if movie['poster_url']:
                st.image(movie['poster_url'])
            else:
                st.write("No poster for this movie")
            st.markdown(f"<p class='single-line'>{movie['title']}</p>", unsafe_allow_html=True)

            # Add Button to play trailer
            if st.button('Play Trailer', key=f"trailer_{movie['id']}"):
                trailer_url = get_movie_trailer(movie['id'])
                if trailer_url:
                    with st.expander("Play"):
                        st.video(trailer_url)
                else:
                    st.write("No Trailer for this movie")

# Movie Searching
movie_name = st.text_input("Begin Searching")
if movie_name:
    movie_info = get_movie_info(movie_name)
    if movie_info:
        col1, col2 = st.columns(2)
        with col1:
            if movie_info["poster_url"]:
                st.image(movie_info["poster_url"])
            else:
                st.write("No poster for this movie")
        with col2:
            st.markdown(f"### {movie_info['title']}")
            st.write(f"**Release date:** {movie_info['release_date']}")
            st.write(movie_info['synopsis'])

        # Add button to play trailer
        if movie_info['trailer_url']:
            if st.button('Play Trailer', key='search_movie_trailer'):
                with st.expander("Play"):
                    st.video(movie_info['trailer_url'])
        else:
            st.write("No Trailer for this movie")
    else:
        st.error("No movie found")
else:
    st.write("Enter the name of the movie you want to search")
