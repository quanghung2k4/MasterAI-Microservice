import pickle
import os

class HybridRecommender:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        model_path = os.path.join(BASE_DIR, 'recommend_model.pkl')

        print("📦 Loading model from:", model_path)

        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            print("✅ Model loaded!")
        else:
            print("❌ Model NOT FOUND!")
            self.model = None

    def recommend(self, user_id, posts_queryset):
        if not self.model:
            return list(posts_queryset)[:20]

        matrix = self.model["matrix"]
        similarity = self.model["similarity"]

        # 🔥 đảm bảo cùng kiểu string
        user_id = str(user_id)
        matrix.index = matrix.index.map(str)
        matrix.columns = matrix.columns.map(str)

        if user_id not in matrix.index:
            print("⚠️ User chưa có dữ liệu → fallback")
            return list(posts_queryset)[:20]

        # ✅ KHÔNG reshape
        user_vector = matrix.loc[user_id].values  # (n,)

        # ✅ dùng dot thay vì @
        scores = similarity.dot(user_vector)      # (n,)

        # map post_id → score
        post_scores = {
            str(post_id): scores[i]
            for i, post_id in enumerate(matrix.columns)
        }

        scored_posts = []
        for post in posts_queryset:
            score = post_scores.get(str(post.id), 0)
            scored_posts.append((post, score))

        scored_posts.sort(key=lambda x: x[1], reverse=True)
        print("matrix shape:", matrix.shape)
        print("similarity shape:", similarity.shape)
        return [p[0] for p in scored_posts[:20]]