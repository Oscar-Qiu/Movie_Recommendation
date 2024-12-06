import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from difflib import get_close_matches

class CFMovieRecommender:
    def __init__(self, movies_df, ratings_df, n_neighbers):
        self.movies_df = movies_df
        self.ratings_df = ratings_df
        self.n_neighbers = n_neighbers
        self.model = None
        self.movie_user_mat = None
        self.movie_to_idx = None
        self.title_to_id = self._create_title_mapping()
    
    def _create_title_mapping(self):
        titles = self.movies_df['title_year'].apply(lambda x: x.rsplit(' (', 1)[0].lower())
        return dict(zip(titles, self.movies_df['movie_id']))
    
    def find_movie_id(self, title):
        title = title.lower()
        titles = list(self.title_to_id.keys())
        matches = get_close_matches(title, titles, n=3, cutoff=0.6)
        return [(match, self.title_to_id[match]) for match in matches]
    
    def preprocess(self, min_ratings=10):
        # 使用groupby统计每部电影的评分数
        movie_ratings = self.ratings_df.groupby('movie_id').size()
        valid_movies = movie_ratings[movie_ratings >= min_ratings].index
        
        # 过滤评分数据
        filtered_ratings = self.ratings_df[self.ratings_df['movie_id'].isin(valid_movies)]
        
        # 创建电影-用户矩阵
        rows = filtered_ratings['movie_id'].astype('category').cat.codes
        cols = filtered_ratings['user_id'].astype('category').cat.codes
        self.movie_to_idx = dict(zip(filtered_ratings['movie_id'].unique(), range(len(valid_movies))))
        
        # 创建稀疏矩阵
        self.movie_user_mat = csr_matrix(
            (filtered_ratings['rating'], (rows, cols)),
            shape=(len(valid_movies), len(filtered_ratings['user_id'].unique()))
        )
    
    def fit(self):
        self.model = NearestNeighbors(
            metric='cosine',
            algorithm='brute',
            n_neighbors=10
        )
        self.model.fit(self.movie_user_mat)
    
    def recommend(self, movie_id):
        if movie_id not in self.movie_to_idx:
            return pd.DataFrame()
            
        idx = self.movie_to_idx[movie_id]
        distances, indices = self.model.kneighbors(
            self.movie_user_mat[idx].reshape(1, -1),
            n_neighbors=self.n_neighbers+1
        )
        
        movie_indices = list(self.movie_to_idx.keys())
        similar_movies = [movie_indices[idx] for idx in indices.flatten()[1:]]
        similarities = distances.flatten()[1:]
        
        recommendations = self.movies_df[
            self.movies_df['movie_id'].isin(similar_movies)
        ].copy()
        recommendations['similarity'] = similarities
        return recommendations

def load_dat_files(movies_path, ratings_path):
    movies_df = pd.read_csv(
        movies_path, 
        sep='::', 
        engine='python',
        names=['movie_id', 'title_year', 'genres'],
        encoding='latin-1'
    )
    
    # 分块读取评分数据以减少内存使用
    ratings_df = pd.read_csv(
        ratings_path,
        sep='::',
        engine='python',
        names=['user_id', 'movie_id', 'rating', 'timestamp'],
        chunksize=1000000  # 每次读取100万行
    )
    ratings_df = pd.concat(ratings_df, ignore_index=True)
    
    return movies_df, ratings_df

def main():
    print("正在加载数据，请稍候...")
    movies_df, ratings_df = load_dat_files('data/movies.dat', 'data/ratings.dat')
    
    print("正在构建推荐系统...")
    recommender = CFMovieRecommender(movies_df, ratings_df)
    recommender.preprocess(min_ratings=50)
    recommender.fit(n_neighbors=10)
    
    while True:
        movie_title = input("\n输入电影名称(输入q退出): ")
        if movie_title.lower() == 'q':
            break
            
        matches = recommender.find_movie_id(movie_title)
        if not matches:
            print("未找到相关电影")
            continue
            
        print("\n找到以下匹配电影：")
        for i, (title, movie_id) in enumerate(matches, 1):
            movie_info = movies_df[movies_df['movie_id'] == movie_id]['title_year'].iloc[0]
            print(f"{i}. {movie_info}")
            
        choice = input("\n选择电影序号(1-{0}): ".format(len(matches)))
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(matches):
            print("无效选择")
            continue
            
        selected_title, selected_id = matches[int(choice)-1]
        recommendations = recommender.recommend(selected_id, n_recommendations=5)
        
        if recommendations.empty:
            print("该电影的评分数据不足，无法提供推荐")
            continue
            
        print(f"\n为 '{movies_df[movies_df['movie_id'] == selected_id]['title_year'].iloc[0]}' 推荐的相似电影：")
        for _, movie in recommendations.iterrows():
            similarity_percentage = (1 - movie['similarity']) * 100
            print(f"- {movie['title_year']} ({movie['genres']}) - 相似度: {similarity_percentage:.1f}%")

if __name__ == "__main__":
    main()