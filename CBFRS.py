import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import re
import logging
import requests
from typing import Optional, Dict, Tuple, List
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# Configure jieba logging
jieba.setLogLevel(logging.INFO)

class TMDBSearcher:
    """
    Helper class for TMDB API operations with language support
    """
    def __init__(self, api_key: str):
        self.base_url = "https://api.themoviedb.org/3"
        self.api_key = api_key
        self.language_map = {
            'zh': 'zh-CN',
            'en': 'en-US',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'unknown': 'zh-CN'
        }

    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text
        """
        try:
            if re.search(r'[\u4e00-\u9fff]', text):
                return 'zh'
            lang = detect(text)
            return lang if lang in self.language_map else 'unknown'
        except LangDetectException:
            return 'unknown'

    def search_movie_multi_lang(self, title: str) -> List[Dict]:
        """
        Search for movies using multiple language parameters
        """
        detected_lang = self.detect_language(title)
        primary_lang = self.language_map[detected_lang]
        
        print(f"Detected language: {detected_lang}")
        
        primary_results = self.search_movie(title, primary_lang)
        
        if len(primary_results) < 3:
            alternative_langs = ['zh-CN' if primary_lang != 'zh-CN' else 'en-US']
            all_results = primary_results
            
            for lang in alternative_langs:
                additional_results = self.search_movie(title, lang)
                existing_ids = {movie['id'] for movie in all_results}
                new_results = [movie for movie in additional_results 
                             if movie['id'] not in existing_ids]
                all_results.extend(new_results)
            
            return all_results
        
        return primary_results

    def search_movie(self, title: str, language: str) -> List[Dict]:
        """
        Search for movies using TMDB API with specified language
        """
        search_url = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": title,
            "language": language,
            "include_adult": False
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"Error searching TMDB: {e}")
            return []

    def get_movie_details(self, tmdb_id: int, language: str = 'zh-CN') -> Optional[Dict]:
        """
        Get detailed movie information from TMDB
        """
        details_url = f"{self.base_url}/movie/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": language,
            "append_to_response": "credits"
        }
        
        try:
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting movie details: {e}")
            return None

class MultilingualMovieRecommender:
    def __init__(self, movies_path: str, tmdb_api_key: str):
        """
        Initialize the multilingual movie recommender system
        """
        self.df = pd.read_csv(movies_path)
        self.tmdb_searcher = TMDBSearcher(tmdb_api_key)
        self.feature_vectors = {}
        
        self.text_weights = {
            'genres': 0.20,
            'keywords': 0.15,
            'overview': 0.15,
            'director': 0.10,
            'top_actors': 0.10,
            'production_companies': 0.05,
            'production_countries': 0.05
        }
        
        self.numeric_weights = {
            'vote_average': 0.08,
            'popularity': 0.05,
            'runtime': 0.04,
            'vote_count': 0.03
        }
        
        self.stopwords = [
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
            '把', '让', '向', '在', '由', '这', '那', '到', '去', '又'
        ]
        
        self.prepare_features()

    def clean_mixed_text(self, text: str) -> str:
        """
        Clean and preprocess mixed language text
        """
        if not isinstance(text, str):
            return ''
        
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        text = re.sub(r'[a-zA-Z]+', lambda m: m.group(0).lower(), text)
        return re.sub(r'\s+', ' ', text).strip()

    def tokenize_mixed_text(self, text: str) -> str:
        """
        Tokenize text containing both Chinese and English
        """
        text = self.clean_mixed_text(text)
        
        english_words = re.findall(r'[a-z]+', text)
        chinese_text = re.sub(r'[a-z]+', '', text)
        
        chinese_words = jieba.cut(chinese_text)
        
        all_words = english_words + [w for w in chinese_words if w.strip()]
        filtered_words = [w for w in all_words if w not in self.stopwords]
        
        return ' '.join(filtered_words)

    def prepare_feature_text(self, feature_name: str) -> List[str]:
        """
        Prepare text feature for vectorization
        """
        texts = self.df[feature_name].fillna('')
        
        if feature_name in ['overview', 'keywords']:
            return [self.tokenize_mixed_text(text) for text in texts]
        else:
            return [self.clean_mixed_text(text) for text in texts]

    def prepare_features(self):
        """
        Prepare and vectorize all features for similarity calculation
        """
        for feature in self.text_weights.keys():
            processed_texts = self.prepare_feature_text(feature)
            
            tfidf = TfidfVectorizer(
                analyzer='word',
                token_pattern=r'(?u)\b\w+\b|[\u4e00-\u9fff]+',
                stop_words=None
            )
            
            tfidf_matrix = tfidf.fit_transform(processed_texts)
            self.feature_vectors[feature] = tfidf_matrix
        
        scaler = MinMaxScaler()
        for feature in self.numeric_weights.keys():
            self.df[feature] = self.df[feature].fillna(self.df[feature].mean())
            scaled_values = scaler.fit_transform(self.df[feature].values.reshape(-1, 1))
            self.feature_vectors[feature] = scaled_values

    def calculate_weighted_similarity(self, movie_idx: int) -> np.ndarray:
        """
        Calculate weighted similarity scores
        """
        final_similarity = np.zeros(len(self.df))
        
        for feature, weight in self.text_weights.items():
            feature_matrix = self.feature_vectors[feature]
            similarity = cosine_similarity(
                feature_matrix[movie_idx:movie_idx+1], 
                feature_matrix
            ).flatten()
            final_similarity += similarity * weight
        
        for feature, weight in self.numeric_weights.items():
            feature_values = self.feature_vectors[feature]
            target_value = feature_values[movie_idx]
            diff = np.abs(feature_values - target_value)
            similarity = 1 - diff.flatten()
            final_similarity += similarity * weight
        
        return final_similarity

    def find_movie_by_search(self, search_title: str) -> Tuple[Optional[int], Optional[str]]:
        """
               Search for a movie using TMDB API and find matching record in dataset
               Modified to return the top match without terminal interaction
               """
        print(f"\nSearching for '{search_title}'...")

        search_results = self.tmdb_searcher.search_movie_multi_lang(search_title)

        if not search_results:
            print("No movies found on TMDB")
            return None, None, None

        # Automatically select the first result as the best match
        selected_movie = search_results[0]

        detected_lang = self.tmdb_searcher.detect_language(search_title)
        movie_details = self.tmdb_searcher.get_movie_details(
            selected_movie['id'],
            self.tmdb_searcher.language_map[detected_lang]
        )

        if not movie_details:
            print("Could not get movie details")
            return None, None, None

        tmdb_id = selected_movie['id']
        dataset_match = self.df[self.df['tmdb_id'] == tmdb_id]

        if len(dataset_match) > 0:
            idx = dataset_match.index[0]
            title = dataset_match.iloc[0]['title']
            print(f"\nFound in dataset: {title}")
            return idx, title, tmdb_id

        print("\nMovie not found in local dataset")
        return None, None, tmdb_id  # return tmdb_id

    def get_movie_recommendations(self, search_title: str, n_recommendations: int = 5,
                                  min_rating: float = None, min_votes: int = None) -> Optional[pd.DataFrame]:
        """
        Get movie recommendations based on search
        """
        movie_idx, actual_title, tmdb_id = self.find_movie_by_search(search_title)

        if movie_idx is None:
            print("Cannot generate recommendations: movie not found in dataset")
            return None

        similarity_scores = self.calculate_weighted_similarity(movie_idx)

        mask = np.ones(len(self.df), dtype=bool)
        if min_rating is not None:
            mask &= self.df['vote_average'] >= min_rating
        if min_votes is not None:
            mask &= self.df['vote_count'] >= min_votes

        filtered_scores = similarity_scores * mask
        similar_indices = filtered_scores.argsort()[::-1][1:n_recommendations + 1]

        recommendations = pd.DataFrame({
            'tmdb_id': self.df.iloc[similar_indices]['tmdb_id'],
            'title': self.df.iloc[similar_indices]['title'],
            'year': self.df.iloc[similar_indices]['year'],
            'genres': self.df.iloc[similar_indices]['genres'],
            'director': self.df.iloc[similar_indices]['director'],
            'top_actors': self.df.iloc[similar_indices]['top_actors'],
            'vote_average': self.df.iloc[similar_indices]['vote_average'],
            'vote_count': self.df.iloc[similar_indices]['vote_count'],
            'runtime': self.df.iloc[similar_indices]['runtime'],
            'similarity_score': filtered_scores[similar_indices]
        })

        return recommendations.sort_values('similarity_score', ascending=False)

def main():
    TMDB_API_KEY = "b32b227102e481fb8a48b5f68065a3b9"
    
    try:
        recommender = MultilingualMovieRecommender(
            movies_path='Data\enriched_movies.csv',
            tmdb_api_key=TMDB_API_KEY
        )
        
        while True:
            search_title = input("\nEnter movie title (or 'quit' to exit): ")
            if search_title.lower() == 'quit':
                break
                
            recommendations = recommender.get_movie_recommendations(
                search_title=search_title,
                n_recommendations=5,
                min_rating=7.0,
                min_votes=1000
            )
            
            if recommendations is not None:
                print("\nTop 5 recommendations:")
                print(recommendations.to_string(index=False))
            
            print("\n" + "="*80)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()