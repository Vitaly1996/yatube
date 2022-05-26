from django.core.paginator import Paginator

number = 10


def func(request, list_group):
    paginator = Paginator(list_group, number)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return context['page_obj']
