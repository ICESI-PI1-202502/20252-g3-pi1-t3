from django.shortcuts import render

# Create your views here.



def news_view(request):
    return render(request, 'news/news.html')
