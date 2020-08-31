from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime

#僅圖書館工作人員librarian可確認所有已經借出的書籍
from django.contrib.auth.mixins import PermissionRequiredMixin

from .forms import RenewBookForm

#利用Django的skeleton快速建立create, update, delete功能
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author

# Create your views here.



def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    
    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    
    # The 'all()' is implied by default.    
    num_authors = Author.objects.count()
    
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)



class BookListView(generic.ListView):
    model = Book
    paginate_by = 2



class BookDetailView(generic.DetailView):
    model = Book


class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')



@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})



class AllLoanedBooksListView(PermissionRequiredMixin, generic.ListView):
    #這個系統功能需要有can_view_all_borrowed_books權限
    permission_required = 'catalog.can_view_all_borrowed_books'
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_all.html'
    def get_queryset(self):
        #排序order by due_back desc
        return BookInstance.objects.filter(status__exact='o').order_by('-due_back')
    paginate_by = 10



class AuthorCreate(CreateView):
    model = Author
    #選取Author資料表全部的欄位
    fields = '__all__'
    initial={'date_of_death':'05/01/2018',}

class AuthorUpdate(UpdateView):
    model = Author
    #選取特定欄位
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    #刪除成功之後，自動導向到下列的網址
    success_url = reverse_lazy('authors')


class AuthorListView(LoginRequiredMixin, generic.ListView):

# class AuthorListView(generic.ListView):
    model = Author
    #透過定義get_queryset()就可以自己定義想要的資料
    #沒有要自定義的話就註解掉get_queryset()
    def get_queryset(self):
        # return Author.objects.filter(title__icontains='bike')[:5] #取前五筆資料，title包含關鍵字'bike'的
        return Author.objects.filter()[:100] #取前100筆資料
    #等等要去哪個路徑找.html檔案
    #不定義這個template_name的話，Django就會去預設的路徑尋找.html
    #預設的路徑是：/locallibrary/catalog/templates/catalog/author_list.html
    #不過目前暫時程式碼設定路徑的方式跟預設一樣就好    
    template_name = '/locallibrary/catalog/templates/catalog/author_list.html'

    #get_context_data()是用來建立自訂的Server side variable的
    #跟.Net MVC也挺像的
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(AuthorListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context

    #這是分頁機制, 以下設定每頁最多10筆資料
    paginate_by = 10      



class AuthorDetailView(generic.DetailView):
    """
    Generic class-based detail view for an author.
    """
    model = Author   
