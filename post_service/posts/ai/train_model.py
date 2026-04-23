from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import pickle
import os

def build_user_item_matrix(df):
    return df.pivot_table(index='user_id', columns='post_id', values='score').fillna(0)

def run_training():
    from posts.models import UserInteraction

    interactions = UserInteraction.objects.all().values('user_id', 'post_id', 'score')

    if not interactions.exists():
        print("No data")
        return

    df = pd.DataFrame(list(interactions))

    matrix = build_user_item_matrix(df)

    similarity = cosine_similarity(matrix.T)

    model = {
        "matrix": matrix,
        "similarity": similarity
    }

    with open("recommend_model.pkl", "wb") as f:
        pickle.dump(model, f)