from django.views.generic import TemplateView

__author__ = 'josearrecio'



class Home(TemplateView):
    template_name = "home.html"

    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base Test first to get a context
        context = super(Home, self).get_context_data(**kwargs)

        context['myvar'] = ['hola','mundo']

        return context

