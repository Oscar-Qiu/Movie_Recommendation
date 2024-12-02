import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from typing import Optional, List, Dict, Tuple

class KNNMovieRecommender:
    def __init__(self, ratings_path: str, n_neighbors: int = 10, min_ratings: int = 5):
        """
        Initialize KNN Movie Recommender
        
        :param ratings_path: Path to ratings dataset
        :param n_neighbors: Number of neighbors for KNN
        :param min_ratings: Minimum number of ratings for a movie to be included
        """
        self.n_neighbors = n_neighbors
        self.min_ratings = min_ratings
        self.ratings_df = self.load_ratings(ratings_path)
        
        # Create matrices and mappings
        self.movie_user_matrix = None
        self.user_mapping = None
        self.movie_mapping = None
        self.reverse_movie_mapping = None
        self.movie_stats = None
        
        # Initialize KNN model
        self.knn_model = None
        
        # Prepare data
        self.prepare_data()
        self.train_model()  # Now this method exists

    def train_model(self):
        """
        Train KNN model using movie-user matrix
        """
        print("\nTraining KNN model...")
        try:
            self.knn_model = NearestNeighbors(
                n_neighbors=min(self.n_neighbors + 1, self.movie_user_matrix.shape[0]),
                metric='cosine',
                algorithm='brute'
            )
            self.knn_model.fit(self.movie_user_matrix)
            print("KNN model training completed")
        except Exception as e:
            print(f"Error training KNN model: {e}")
            raise

    def load_ratings(self, filepath: str) -> pd.DataFrame:
        """
        Load ratings data from file
        """
        try:
            # Load ratings data
            ratings = pd.read_csv(filepath, 
                                sep='::', 
                                names=['user_id', 'movie_id', 'rating', 'timestamp'],
                                engine='python')
            
            # Print sample of movie IDs for debugging
            print("\nSample of movie IDs from dataset:")
            print(ratings['movie_id'].head())
            
            # Print statistics
            print("\nDataset Statistics:")
            print(f"Total ratings: {len(ratings)}")
            print(f"Unique movies: {ratings['movie_id'].nunique()}")
            print(f"Unique users: {ratings['user_id'].nunique()}")
            print(f"Movie ID type: {ratings['movie_id'].dtype}")
            
            # Convert movie_id to string if it's not already
            ratings['movie_id'] = ratings['movie_id'].astype(str)
            
            return ratings
            
        except Exception as e:
            print(f"Error loading ratings file: {e}")
            raise

    def prepare_data(self):
        """
        Prepare data for KNN model
        """
        print("\nPreparing data...")
        
        # Create movie stats
        self.movie_stats = self.ratings_df.groupby('movie_id').agg({
            'rating': ['count', 'mean']
        }).droplevel(0, axis=1)
        self.movie_stats.columns = ['count', 'mean_rating']
        
        # Print movie ID samples from stats
        print("\nSample of movie IDs from stats:")
        print(self.movie_stats.head().index)
        
        # Filter movies with minimum ratings
        popular_movies = self.movie_stats[self.movie_stats['count'] >= self.min_ratings].index
        
        # Store all movie IDs for reference
        self.all_movie_ids = set(self.movie_stats.index)
        
        print(f"\nMovie counts:")
        print(f"Total unique movies: {len(self.all_movie_ids)}")
        print(f"Movies with >= {self.min_ratings} ratings: {len(popular_movies)}")
        
        # Filter ratings for popular movies
        ratings_filtered = self.ratings_df[self.ratings_df['movie_id'].isin(popular_movies)]
        
        # Create mappings
        unique_users = ratings_filtered['user_id'].unique()
        unique_movies = sorted(popular_movies)  # Sort to ensure consistent mapping
        
        self.user_mapping = {user: idx for idx, user in enumerate(unique_users)}
        self.movie_mapping = {movie: idx for idx, movie in enumerate(unique_movies)}
        self.reverse_movie_mapping = {idx: movie for movie, idx in self.movie_mapping.items()}
        
        # Create movie-user matrix
        rows = [self.movie_mapping[movie] for movie in ratings_filtered['movie_id']]
        cols = [self.user_mapping[user] for user in ratings_filtered['user_id']]
        data = ratings_filtered['rating'].values
        
        self.movie_user_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(unique_movies), len(unique_users))
        )
        
        print(f"Created matrix with shape: {self.movie_user_matrix.shape}")

    def standardize_movie_id(self, movie_id: str) -> str:
        """
        Standardize movie ID format
        """
        if movie_id is None:
            return None
            
        # Convert to string
        movie_id = str(movie_id)
        
        # Check if movie ID exists in dataset
        if movie_id in self.all_movie_ids:
            return movie_id
            
        # Try padding with zeros if it's numeric
        try:
            padded_id = movie_id.zfill(7)  # Pad to 7 digits
            if padded_id in self.all_movie_ids:
                return padded_id
        except:
            pass
            
        return movie_id

    def get_movie_recommendations(self, movie_id: str, 
                                n_recommendations: int = 5,
                                min_rating: float = None) -> List[Tuple[str, float, float, int]]:
        """
        Get movie recommendations based on a movie ID
        """
        # Standardize movie ID format
        movie_id = self.standardize_movie_id(movie_id)
        
        print(f"\nLooking for movie ID: {movie_id}")
        print(f"Available movie IDs sample: {list(self.movie_mapping.keys())[:5]}")
        
        if movie_id not in self.all_movie_ids:
            print(f"Movie ID {movie_id} not found in original dataset")
            return []
            
        if movie_id not in self.movie_mapping:
            print(f"Movie ID {movie_id} was filtered out (less than {self.min_ratings} ratings)")
            print(f"This movie has {self.movie_stats.loc[movie_id, 'count']} ratings")
            return []
        
        try:
            # Get movie index
            movie_idx = self.movie_mapping[movie_id]
            
            # Find nearest neighbors
            distances, indices = self.knn_model.kneighbors(
                self.movie_user_matrix[movie_idx].reshape(1, -1)
            )
            
            # Convert distances to similarities
            similarities = 1 - distances.flatten()
            
            # Get similar movies (excluding the input movie)
            recommendations = []
            for idx, similarity in zip(indices.flatten()[1:], similarities[1:]):
                rec_movie_id = self.reverse_movie_mapping[idx]
                avg_rating = self.movie_stats.loc[rec_movie_id, 'mean_rating']
                num_ratings = self.movie_stats.loc[rec_movie_id, 'count']
                
                if min_rating is None or avg_rating >= min_rating:
                    recommendations.append((rec_movie_id, similarity, avg_rating, num_ratings))
            
            # Sort by similarity and return top N
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:n_recommendations]
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            raise

    def get_movie_details(self, movie_id: str) -> Optional[Dict]:
        """
        Get movie statistics
        """
        movie_id = self.standardize_movie_id(movie_id)
        
        if movie_id not in self.all_movie_ids:
            print(f"Movie {movie_id} not found in dataset")
            return None
            
        stats = self.movie_stats.loc[movie_id]
        return {
            'movie_id': movie_id,
            'average_rating': stats['mean_rating'],
            'number_of_ratings': stats['count'],
            'included_in_model': movie_id in self.movie_mapping
        }

def main():
    try:
        # Initialize recommender
        recommender = KNNMovieRecommender(
            ratings_path='Data/ratings.dat',
            n_neighbors=10,
            min_ratings=5
        )
        
        while True:
            movie_id = input("\nEnter movie ID (or 'quit' to exit): ")
            if movie_id.lower() == 'quit':
                break
            
            # Get movie details first
            details = recommender.get_movie_details(movie_id)
            if details:
                print(f"\nMovie {movie_id} details:")
                for key, value in details.items():
                    print(f"{key}: {value}")
            
            # Get recommendations
            recommendations = recommender.get_movie_recommendations(
                movie_id=movie_id,
                n_recommendations=5,
                min_rating=7.0
            )
            
            if recommendations:
                print("\nSimilar movies:")
                for rec_id, sim, rating, count in recommendations:
                    print(f"Movie: {rec_id}, Similarity: {sim:.3f}, "
                          f"Rating: {rating:.2f}, Num ratings: {count}")
            else:
                print("No recommendations found")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()