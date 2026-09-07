from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def guide(request):
    return render(request, "core/guide.html")


def game(request):
    return render(request, "core/game.html")
