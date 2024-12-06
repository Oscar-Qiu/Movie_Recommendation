from CBFRS import MultilingualMovieRecommender
from CFRS_n import CFMovieRecommender, load_dat_files
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class ImprovedHybridRecommender:
    def __init__(self,
                 movies_path: str,
                 ratings_path: str,
                 tmdb_api_key: str):
        self.content_recommender = MultilingualMovieRecommender(
            movies_path=movies_path,
            tmdb_api_key=tmdb_api_key
        )
        
        # 加载数据并初始化CF推荐器
        self.movies_df, self.ratings_df = load_dat_files('data/movies.dat', 'data/ratings.dat')
        self.cf_recommender = CFMovieRecommender(self.movies_df, self.ratings_df, n_neighbers=10)
        self.cf_recommender.preprocess(min_ratings=10)
        self.cf_recommender.fit()
        
        # 加载丰富数据集
        self.enriched_df = pd.read_csv(movies_path)
        
        self.content_weight = 0.3
        self.cf_weight = 0.7

    def get_recommendations(self,
                          movie_title: str,
                          n_recommendations: int = 5,
                          min_rating: float = 7.0,
                          min_votes: int = 1000) -> pd.DataFrame:
        print(f"\nGetting recommendations for: {movie_title}")
        content_based_scores = {}
        cf_scores = {}
        
        # 获取内容推荐
        content_recommendations = self.content_recommender.get_movie_recommendations(
            search_title=movie_title,
            n_recommendations=n_recommendations * 2,
            min_rating=min_rating,
            min_votes=min_votes
        )
        
        if content_recommendations is not None:
            actual_movie = content_recommendations.iloc[0]['title']
            print(f"Matched movie title: {actual_movie}")
            
            for _, row in content_recommendations.iterrows():
                content_based_scores[row['title']] = row['similarity_score']
                print(f"Content score for {row['title']}: {row['similarity_score']:.3f}")
            
            # 获取CF推荐
            matches = self.cf_recommender.find_movie_id(actual_movie)
            if matches:
                selected_title, selected_id = matches[0]  # 使用最匹配的结果
                cf_recommendations = self.cf_recommender.recommend(selected_id)
                
                if not cf_recommendations.empty:
                    print("\nCF recommendations:")
                    for _, movie in cf_recommendations.iterrows():
                        title = movie['title_year'].rsplit(' (', 1)[0]
                        similarity = 1 - movie['similarity']  # 转换距离为相似度
                        print(f"CF score for {title}: {similarity:.3f}")
                        
                        # 在enriched_df中查找完整标题
                        enriched_title = self.find_matching_title(title)
                        if enriched_title:
                            cf_scores[enriched_title] = similarity
        
        # 组合分数
        combined_scores = {}
        all_movies = set(content_based_scores.keys()) | set(cf_scores.keys())
        
        for movie in all_movies:
            content_score = content_based_scores.get(movie, 0)
            cf_score = cf_scores.get(movie, 0)
            
            combined_scores[movie] = (
                self.content_weight * content_score +
                self.cf_weight * cf_score
            )
        
        # 创建推荐DataFrame
        recommendations = []
        top_movies = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]
        
        for movie_title, score in top_movies:
            movie_data = self.enriched_df[self.enriched_df['title'] == movie_title].iloc[0]
            recommendations.append({
                'title': movie_title,
                'year': movie_data['year'],
                'genres': movie_data['genres'],
                'director': movie_data['director'],
                'vote_average': movie_data['vote_average'],
                'content_score': content_based_scores.get(movie_title, 0),
                'cf_score': cf_scores.get(movie_title, 0),
                'combined_score': combined_scores[movie_title]
            })
        
        return pd.DataFrame(recommendations)

    def find_matching_title(self, partial_title: str) -> Optional[str]:
        """Find matching title in enriched dataset"""
        matches = self.enriched_df[
            self.enriched_df['title'].str.lower().str.contains(partial_title.lower())
        ]
        return matches['title'].iloc[0] if not matches.empty else None

    def adjust_weights(self, content_weight: float):
        if 0 <= content_weight <= 1:
            self.content_weight = content_weight
            self.cf_weight = 1 - content_weight
            print(f"Weights adjusted: Content={content_weight:.2f}, CF={1-content_weight:.2f}")
        else:
            print("Weight must be between 0 and 1")

def main():
    TMDB_API_KEY = "b32b227102e481fb8a48b5f68065a3b9"
    
    recommender = ImprovedHybridRecommender(
        movies_path='Data/enriched_movies.csv',
        ratings_path='Data/ratings.dat',
        tmdb_api_key=TMDB_API_KEY
    )
    
    while True:
        print("\n=== Hybrid Movie Recommender ===")
        print("1. Get recommendations")
        print("2. Adjust weights")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            movie_title = input("Enter movie title: ")
            recommendations = recommender.get_recommendations(movie_title)
            if not recommendations.empty:
                print("\nTop Recommendations:")
                print(recommendations.to_string(index=False))
            else:
                print("No recommendations found")
                
        elif choice == '2':
            try:
                weight = float(input("Enter content-based weight (0-1): "))
                recommender.adjust_weights(weight)
            except ValueError:
                print("Please enter a valid number between 0 and 1")
                
        elif choice == '3':
            break

if __name__ == "__main__":
    main()