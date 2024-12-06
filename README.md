# Project Documentation

## Overview
This project aims to create an intelligent movie recommendation system that combines traditional recommendation techniques, similarity-based algorithms, and sentiment analysis derived from user-generated content such as reviews. The system leverages a multi-source dataset comprising movies, users, ratings, and reviews to deliver personalized and accurate movie suggestions.

### Key Features
- **Frontend**: User-friendly interface for exploring and receiving movie recommendations.
- **Hybrid Movie Recommendation Module**: The Hybrid Movie Recommendation System Framework integrates content-based filtering with collaborative filtering to provide comprehensive movie recommendations.
- **Sentiment Analysis Module**: Analyzes review sentiments to fine-tune recommendations and highlight highly-rated movies.
- **Integration**: Seamless integration of traditional recommendation techniques with advanced natural language processing.

---

## Frontend
The frontend serves as the user interface, providing intuitive navigation and efficient access to recommendations.

### Technology Stack
- **Framework**: 


### Features
- **Search**: 


---

## Hybrid Movie Recommendation Module
The Hybrid Movie Recommendation System Framework integrates content-based filtering with collaborative filtering to provide comprehensive movie recommendations. 

### System Architecture
![image](https://github.com/user-attachments/assets/6e0c8177-dd6e-406a-874c-d0f19011724b) \
The system consists of three main components that work together to generate personalized recommendations:
- **Content-Based Module**:
This module analyzes movie attributes using the TMDB API and enriched movie data. It processes multiple features including genres (20% weight), keywords (15%), plot overview (15%), director (10%), actors (10%), and production details (10%). The module vectorizes text features using TF-IDF and normalizes numerical features using MinMaxScaler. It then calculates weighted cosine similarity between movies across these dimensions.
- **Collaborative Filtering Module**:
This component utilizes user-item interaction data to identify similar movies based on rating patterns. It constructs a sparse user-item rating matrix and applies a KNN algorithm with cosine similarity to find movies with similar rating patterns. The system preprocesses the data by filtering movies with a minimum number of ratings to ensure recommendation quality.
- **Hybrid Integration Layer**:
This layer combines recommendations from both modules using an adjustable weighting scheme. By default, it assigns 30% weight to content-based scores and 70% to collaborative filtering scores. The integration process involves normalizing scores from both systems to ensure fair combination, then ranking recommendations based on the weighted sum.
### Workflow
1. **Initial Data Loading and Enrichment**:
- Loads base movie data and user ratings
- Enriches movie data using TMDB API
- Processes multilingual content using specialized tokenization
2. **Feature Processing**: 
- Vectorizes text features while handling multiple languages
- Normalizes numerical attributes
- Creates sparse matrices for collaborative filtering
3. **Recommendation Generation**:
- Matches user queries across multiple languages
- Generates separate recommendations from each module
- Combines and ranks final recommendations
---

## Sentiment Analysis Module

### Approach
- **Data Preprocessing**: The data used for sentiment analysis was sourced from the Kaggle competition [Movie Review Sentiment Analysis](https://www.kaggle.com/competitions/movie-review-sentiment-analysis-kernels-only/). The preprocessing involved cleaning the movie review text, tokenizing, and converting it into the input format required for fine-tuning the BERT.
- **Sentiment Classification**: A fine-tuned BERT model was used to classify the sentiments of the reviews that we get from TMDB API into five categories: Negative, Slightly Negative, Neutral, Slightly Positive, and Positive.
- **Sentiment Scoring**: Each sentiment category was assigned a score from 0 to 4, where 0 represents "Negative" and 4 represents "Positive." The average score of all reviews for a given movie was computed to adjust the movie's rating we get directly from TMDB in the similarity-based recommendation system.

### Workflow
1. **Data Collection**: Movie data and their corresponding reviews were retrieved using the TMDB API.
2. **Sentiment Analysis**: The fine-tuned BERT model analyzed the reviews and classified their sentiments into five levels.
3. **Scoring and Aggregation**: Each review was scored based on its sentiment classification. The scores were averaged to calculate a sentiment-adjusted rating for each movie.
4. **Integration with Recommendation System**: The sentiment-adjusted rating was used alongside original ratings to refine movie recommendations.

--- 

## Future Enhancements
- **Real-time Analysis**: Implement real-time sentiment analysis for live user feedback.
- **Scalability**: Optimize similarity calculations for large datasets.
- **Multi-lingual Support**: Extend sentiment analysis to support multiple languages.

---

## Contributors
- **Borui Chen** - 
- **Lingsong Qin** - Sentiment Analysis Module
- **Yiheng Qiu** - 

---
