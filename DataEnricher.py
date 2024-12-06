import requests
import pandas as pd
import time
import logging
from typing import List, Dict, Optional

class TMDbEnricher:
    def __init__(self, api_key: str):
        """
        初始化TMDb数据丰富器
        
        :param api_key: TMDb API密钥
        """
        self.base_url = "https://api.themoviedb.org/3"
        self.api_key = api_key
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename='movie_enricher.log',
            filemode='w'
        )
        self.logger = logging.getLogger()

    def validate_api_key(self) -> bool:
        """
        验证API密钥是否可用
        
        :return: 是否验证成功
        """
        try:
            # 使用一个简单的端点进行验证
            validation_url = f"{self.base_url}/configuration"
            params = {
                "api_key": self.api_key
            }
            response = requests.get(validation_url, params=params)
            
            # 检查响应状态码
            if response.status_code == 200:
                self.logger.info("API密钥验证成功")
                print("✅ API密钥验证成功")
                return True
            elif response.status_code == 401:
                self.logger.error("API密钥无效，请检查您的凭据")
                print("❌ API密钥无效，请检查您的凭据")
                return False
            else:
                self.logger.error(f"API验证出现异常：状态码 {response.status_code}")
                print(f"❓ API验证出现异常：状态码 {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"验证API密钥时网络错误: {e}")
            print(f"❌ 网络错误：{e}")
            return False
        except Exception as e:
            self.logger.error(f"验证API密钥时发生未知错误: {e}")
            print(f"❌ 未知错误：{e}")
            return False

    def api_key_check(self) -> bool:
        """
        提供更详细的API密钥检查和指导
        
        :return: 是否可以继续处理
        """
        print("\n--- TMDb API 密钥检查 ---")
        
        # 检查密钥是否为空
        if not self.api_key or self.api_key.strip() == "your_tmdb_api_key_here":
            print("❌ 错误：未设置API密钥")
            print("请按以下步骤操作：")
            print("1. 访问 https://www.themoviedb.org/documentation/api")
            print("2. 注册并获取API密钥")
            print("3. 将密钥替换脚本中的 'your_tmdb_api_key_here'\n")
            return False
        
        # 验证API密钥
        return self.validate_api_key()

    def parse_movie_dataset(self, file_path: str) -> pd.DataFrame:
        """
        解析原始电影数据集
        
        :param file_path: 数据集文件路径
        :return: DataFrame包含movie_id, title, year, genres
        """
        def parse_line(line: str) -> Dict:
            parts = line.strip().split('::')
            movie_id = parts[0]
            title_year = parts[1].split('(')
            title = title_year[0].strip()
            year = title_year[1].rstrip(')').strip()
            genres = parts[2].split('|')
            return {
                'movie_id': movie_id,
                'title': title,
                'year': year,
                'genres': genres
            }

        with open(file_path, 'r', encoding='utf-8') as f:
            movies = [parse_line(line) for line in f]
        
        return pd.DataFrame(movies)

    def search_movie(self, title: str, year: str) -> Optional[Dict]:
        """
        通过标题和年份搜索电影
        
        :param title: 电影标题
        :param year: 电影年份
        :return: 匹配的电影信息或None
        """
        search_url = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": title,
            "year": year,
            "language": "zh-CN"
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # 增加调试日志
            self.logger.info(f"搜索结果 for {title} ({year}): {len(data.get('results', []))} 匹配")
            
            # 如果有多个结果，选择最匹配的一个
            if data.get('results'):
                # 尝试找到年份最接近的
                best_match = min(
                    data['results'], 
                    key=lambda x: abs(int(x.get('release_date', '0')[:4]) - int(year))
                )
                return best_match
            
            return None
            
        except requests.RequestException as e:
            self.logger.error(f"搜索 {title} 时出错: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析搜索结果时出错 {title}: {e}")
            return None

    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        获取电影详细信息
        
        :param movie_id: TMDb电影ID
        :return: 电影详细信息
        """
        try:
            # 获取基本详情和演职员表
            details_url = f"{self.base_url}/movie/{movie_id}"
            params = {
                "api_key": self.api_key,
                "language": "zh-CN",
                "append_to_response": "credits,keywords"
            }
            
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"获取电影详情时出错 (ID: {movie_id}): {e}")
            return None

    def get_director(self, credits: Dict) -> str:
        """
        从演员表中获取导演姓名
        
        :param credits: 电影演员表信息
        :return: 导演姓名
        """
        directors = [crew['name'] for crew in credits.get('crew', []) if crew['job'] == 'Director']
        return directors[0] if directors else ''

    def get_top_actors(self, credits: Dict, top_n: int = 5) -> List[str]:
        """
        获取前N名主要演员
        
        :param credits: 电影演员表信息
        :param top_n: 返回演员数量
        :return: 演员姓名列表
        """
        actors = sorted(
            [actor for actor in credits.get('cast', []) if actor['known_for_department'] == 'Acting'],
            key=lambda x: x.get('popularity', 0),
            reverse=True
        )
        return [actor['name'] for actor in actors[:top_n]]

    def enrich_movie_dataset(self, dataset_path: str, output_path: str):
        """
        丰富电影数据集
        
        :param dataset_path: 原始数据集路径
        :param output_path: 输出丰富后的数据集路径
        """
        # 首先检查API密钥
        if not self.api_key_check():
            print("❌ 无法继续处理，请先解决API密钥问题")
            return

        movies_df = self.parse_movie_dataset(dataset_path)
        enriched_movies = []

        total_movies = len(movies_df)
        print(f"\n开始处理 {total_movies} 部电影")

        for idx, movie in movies_df.iterrows():
            try:
                # 添加延迟以避免触发API速率限制
                if idx > 0 and idx % 20 == 0:
                    time.sleep(1)  # 每20个电影暂停1秒
                    print(f"处理进度: {idx}/{total_movies}")

                search_result = self.search_movie(movie['title'], movie['year'])
                
                if search_result:
                    details = self.get_movie_details(search_result['id'])
                    
                    if details:
                        enriched_movie = {
                            **movie,
                            'tmdb_id': search_result['id'],
                            'overview': details.get('overview', ''),
                            'vote_average': details.get('vote_average', 0),
                            'vote_count': details.get('vote_count', 0),
                            'popularity': details.get('popularity', 0),
                            'original_language': details.get('original_language', ''),
                            'runtime': details.get('runtime', 0),  # 电影时长（分钟）
                            'production_countries': ', '.join([country['name'] for country in details.get('production_countries', [])]),
                            'production_companies': ', '.join([company['name'] for company in details.get('production_companies', [])]),
                            'director': self.get_director(details.get('credits', {})) if details.get('credits') else '',
                            'top_actors': ', '.join(self.get_top_actors(details.get('credits', {})) if details.get('credits') else []),
                            'keywords': ', '.join([keyword['name'] for keyword in details.get('keywords', {}).get('keywords', [])])
                        }
                        enriched_movies.append(enriched_movie)
                        self.logger.info(f"丰富成功: {movie['title']} ({movie['year']})")
                    else:
                        self.logger.warning(f"无法获取详细信息: {movie['title']} ({movie['year']})")
                else:
                    self.logger.warning(f"未找到: {movie['title']} ({movie['year']})")
            
            except Exception as e:
                self.logger.error(f"处理 {movie['title']} 时出错: {e}")

        # 保存结果
        if enriched_movies:
            enriched_df = pd.DataFrame(enriched_movies)
            enriched_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"\n✅ 处理完成！")
            print(f"- 总计处理: {total_movies} 部电影")
            print(f"- 成功丰富: {len(enriched_movies)} 部电影")
            print(f"- 结果保存至: {output_path}")
            self.logger.info(f"丰富后的数据集已保存到 {output_path}")
        else:
            print("\n❌ 没有成功处理任何电影数据")

def main():
    # 请替换为您的TMDb API密钥
    API_KEY = "b32b227102e481fb8a48b5f68065a3b9"
    
    enricher = TMDbEnricher(API_KEY)
    
    enricher.enrich_movie_dataset(
        dataset_path='Data\movies.dat', 
        output_path='Data\enriched_movies.csv'
    )

if __name__ == "__main__":
    main()