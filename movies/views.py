from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import ListView
from pandas.tests.groupby.test_value_counts import df

from .models import Movies, Ratings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import numpy as np
import pandas as pd
import pymysql
from django.contrib.auth.decorators import login_required
import pickle
import os
from django.conf import settings
from django.db.models import Avg
from django_pandas.io import read_frame
import psycopg2
from sqlalchemy import create_engine
from accounts.forms import ReviewForm
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

def recommendation(request):

    engine = create_engine('postgresql://postgres:admin@localhost:1234/movies')
    movies = pd.read_sql_query('SELECT * from "movies_movies"', engine)
    ratings = pd.read_sql_query('SELECT * from "movies_ratings"', engine)

    current_user=request.user.id
    print(current_user)

    ratings=pd.merge(movies,ratings).drop(columns=["genres"])

    print("RATINGSSSSSSSSSSSSSSSSSSSSSSSSS\n",ratings)
    user_ratings=ratings.pivot_table(index={'userId_id'},columns={'title'},values={'rating'})
    movie_user_rating_pivot=user_ratings


    user_ratings=user_ratings.fillna(0)
    print("users\n",user_ratings)

    file_ = open(os.path.join(settings.BASE_DIR, 'testfile'),'rb')
    pickle_model = pickle.load(file_)
    file_.close()


    preds_df = pd.DataFrame(pickle_model, index=user_ratings.index,columns = user_ratings.columns)


    def recommend_movies(predictions_df, userID, movies_df, original_ratings_df, num_recommendations=5):
         # Get and sort the user's predictions
            user_row_number = userID - 1 # UserID starts at 1, not 0

            user_data = original_ratings_df[original_ratings_df.userId_id == (userID)]
            user_full = (user_data.merge(movies_df, how = 'left', left_on = 'movieId_id', right_on = 'movieId_id'))

            # Get the user's data and merge in the movie information.

            print('User {0} has already rated {1} movies.'.format(userID, user_full.shape[0]))
            print('Recommending the highest {0} predicted ratings movies not already rated.'.format(num_recommendations))
            
            # Recommend the highest predicted rating movies that the user hasn't seen yet.
            if user_full.shape[0]>0:
                title="Recommendation"
                sorted_user_predictions = predictions_df.iloc[user_row_number].sort_values(ascending=False)


                recommendations = (movies_df[~movies_df['movieId_id'].isin(user_full['id'])].
                     merge(pd.DataFrame(sorted_user_predictions).reset_index()).
                     rename(columns = {userID: 'Ratings'}).
                     sort_values('Ratings', ascending = False).
                                   iloc[:num_recommendations :1])
            else:
                title=""
                movie_ratings = original_ratings_df.groupby('movieId_id')['rating']
                avg_ratings = movie_ratings.mean()
                avg_ratings=round(avg_ratings, 2)
                num_ratings = movie_ratings.count()


                rating_count_df = pd.DataFrame({'avg_rating': avg_ratings, 'num_ratings': num_ratings})



                movie_recs = movies.set_index('movieId_id').join(rating_count_df)

                recommendations = (movies_df[~movies_df['movieId_id'].isin(user_full['id'])].merge(movie_recs.sort_values(['avg_rating', 'num_ratings'], ascending=False).iloc[:num_recommendations :1]))

            return user_full, recommendations,title

    already_rated, predictions,title = recommend_movies(preds_df,current_user, movies, ratings, 50)
    print(predictions)

    context = {
         "object_list": predictions,
         "title": title
        }

    return render(request, "recommendation.html", context)


def post_list(request):
    query=request.GET.get("title")
    queryset_list=None
    search=None
    queryset_count=0
    if query:
        search = "true"
        queryset_list=Movies.objects.all().filter(title__icontains=query)
        if not queryset_list:
            return render(request, "search.html")
        else:
            queryset_count=len(queryset_list)
    else:
        queryset_list=Movies.objects.all().order_by("id")
    userid = request.user.id
    userName = request.user.username

    paginator = Paginator(queryset_list, 20)
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:

        queryset = paginator.page(1)
    except EmptyPage:

        queryset = paginator.page(paginator.num_pages)

    context = {
        "user_id": userid,
        "user_name": userName,
        "object_list": queryset,
        "title": "List",
        "search": search,
        "query":query,
        "search_count":queryset_count}
    return render(request, "home.html", context)


def detail(request,id):
    detail = Movies.objects.get(id=id)
    detail_movie = str(detail)

    rating = Ratings.objects.filter(movieid=id)
    rating=rating.aggregate(rating=Avg('rating'))

    print("id=",id)
    print("\n detail=",detail)
    print("\n rating=",rating)
    print("userid",request.user.id)
    reviews=Ratings.objects.filter(movieid=id).order_by("comment")
   
    condition="false"
    count=0
    for review in reviews:
        if request.user.id==review.userid.id:
            print("user has reviewed")
            condition="true"
            break
        else:
            print("not reviewed")
            condition="false"
    print("count",count)
    for review in reviews:
        count=count+1

    engine = create_engine('postgresql://postgres:admin@localhost:1234/movieRecommend')
    movies = pd.read_sql_query('SELECT * from "movies_movies"', engine)

    for index, rows in movies.iterrows():
        if (detail_movie in (rows.title)):
            print(rows.id)
            movie_ids = rows.id - 1
            break
    print(movie_ids)
    movies['genre'] = movies['genres']
    movies['genre'] = movies['genre'].str.split('|')
    movies['genres'] = movies['genres'].fillna("").astype('str')

    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(movies['title'])

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    cosine_sim[:4, :4]

    indices = pd.Series(movies.index, index=movies['title'])

    sim_scores = list(enumerate(cosine_sim[movie_ids]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:21]
    movie_indices = [i[0] for i in sim_scores]
    similar_movie = movies.iloc[movie_indices]

    similar_movie = similar_movie.head(8)

    current_user=request.user.id
    context = {
        "detail": detail,
        "rating": rating,
        "reviews":reviews,
        "condition":condition,
        "current_user":current_user,
        "count":count,
        #     "content":content,
    }
    return render(request, "detail.html", context)


def search(request):
    return render(request, 'search.html')

#edit the review
def edit_review(request,review_id):
    if request.user.is_authenticated:
        #review
        review=Ratings.objects.get(id=review_id)
        movieid=review.movieid
        movieid1=Movies.objects.get(title=movieid)
        movie_id=movieid1.id
        #check if the reviews by the logged in user
        if request.user==review.userid:
            #grant permission
            if request.method=="POST":
                form=ReviewForm(request.POST,instance=review)
                if form.is_valid():
                    data=form.save(commit=False)
                    if (data.rating > 5) or (data.rating < 0):
                        error="Out of range. Please select rating from 1 to 5."
                        return render(request,'edit_review.html',{"error":error,"form":form})
                    else:
                        data.save()
                        return redirect("movies:detail",movie_id)      
            else:
                form=ReviewForm(instance=review)
            return render(request,"edit_review.html",{"form":form})
        else:
            return redirect("movies:detail",movie_id)
    else:
        return redirect("movies:login")

#delete review
def delete_review(request,review_id):
    if request.user.is_authenticated:
        #review
        review=Ratings.objects.get(id=review_id)
        movieid=review.movieid
        movieid1=Movies.objects.get(title=movieid)
        movie_id=movieid1.id
        #check if the reviews by the logged in user
        if request.user==review.userid:
            #grant permission to delete
            review.delete()
        
        return redirect("movies:detail",movie_id)
    else:
        return redirect("movies:login")






