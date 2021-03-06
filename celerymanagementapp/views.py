import datetime
import itertools
import urllib

from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.conf import settings

from celery.task.control import inspect, broadcast

#from celery.task.control import Control
#from celery.app import app_or_default
from celerymanagementapp.stats import calculate_throughputs, calculate_runtimes
from celerymanagementapp.models import DispatchedTask, OutOfBandWorkerNode
from celerymanagementapp.models import Provider, PolicyModel
from celerymanagementapp.forms import OutOfBandWorkerNodeForm, ProviderForm
from celerymanagementapp.forms import PolicyModelForm

import gviz_api

#==============================================================================#
# DATETIME_FMT is used by the datestr_to_datetime() and datetime_to_datestr() 
# functions.
# regex corresponding to DATETIME_FMT:  '\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'
DATETIME_FMT = '%Y-%m-%d-%H-%M-%S'   # YYYY-MM-DD-HH-MM-SS

def datestr_to_datetime(s):
    """Convienence function to convert from a string as passed in a URL to a 
       datetime.datetime object.
    """
    if not s:
        return s
    else:
        return datetime.datetime.strptime(s, DATETIME_FMT)
    
def datetime_to_datestr(dt):
    """Convienence function to convert from a datetime.datetime object to a 
       string as it would be passed in a URL.
    """
    return dt.strftime(DATETIME_FMT)
    
def searchrange_from_post(post):
    """ Retrieve the search_range tuple from a request.POST or request.GET 
        QueryDict.  The tuple will contain None in place of either time (or 
        both times) if they are not found.
    """
    min = datestr_to_datetime(post.get('start_time', None))
    max = datestr_to_datetime(post.get('end_time', None))
    return (min, max)
    
    
def string_to_bool(s):
    s = s.lower()
    if s == 'true' or s == 'yes':
        return True
    elif s.isdigit():
        return int(s) != 0
    return False
    

def get_postval(postdict, name, convfunc, default=None):
    """ Retrieve a value from the request.POST or request.GET QueryDict.  The 
        advantage of using this over using QueryDict.get() is that this 
        function will also convert the value from a string.
       
        postdict:
            The QueryDict object from which to get the value.
        name:
            The key to look up in the postdict.
        convfunc:
            A function to convert from the value in the QueryDict (a string) to 
            the expected value.  Often, a built-in function can do this, as in 
            the case of int() and float().
        default:
            The value to return if the name was not found in the QueryDict.  If 
            not given, it defaults to None.
        
        Example usage:
            count = get_postval(request.POST, 'count', int, default=0)
    """
    try:
        return convfunc(postdict[name])
    except KeyError:
        return default
    

class QueryStringBuilder(object):
    """ Class to help create query strings for URLs from within view functions.
        The values may come from both the view function parameters and from the 
        request object.
        
        To use this class, first create a subclass which defines param_names.  
        Then, within the view function, construct an instance with the view 
        function parameters, and call the add_querydict method with request.GET 
        or request.POST.
    """
    param_names = []
    def __init__(self, **kwargs):
        """The view function parameters should be given as keyword arguments."""
        self.args = {}
        for name in self.param_names:
            val = kwargs.get(name, '')
            self.args[name] = str(val)  if val is not None else  None
    
    def add_querydict(self, pdict):
        """Add values from a request.GET or request.POST QueryDict.  Values 
           will override those given in __init__().
        """
        for name in self.param_names:
            val = pdict.get(name, None)
            if val is not None:
                self.args[name] = str(val)
                
    def _iter_formatted_params(self):
        quote = urllib.quote
        return ('{0}={1}'.format(quote(name), quote(val)) 
                for name, val in self.args 
                    if val is not None)
                
    def to_querystring(self):
        """Build a query string from the QueryStringBuilder's values."""
        quote = urllib.quote
        def single_query(n, v):
            return '{0}={1}'.format(quote(n), quote(v))
        # Join all name/value pairs, except those that have an empty value.
        r = '&'.join( single_query(name, val) 
                      for name, val in self.args.iteritems() if val )
        if r:
            r = '?' + r
        return r


#==============================================================================#
def test_view(request, taskname=None):
    now = datetime.datetime.now()
    timerange = (now-datetime.timedelta(seconds=120), now)
    start = timerange[0]
    stop = timerange[1]
    states_in_range = DispatchedTask.objects.filter(state='SUCCESS', 
                                                    tstamp__range=(start, stop)
                                                   )
    return HttpResponse(states_in_range)
    
#==============================================================================#
@login_required()
def view_throughputs(request, taskname=None):
    # Simple view, mostly for testing purposes at this point.
    now = datetime.datetime.now()
    timerange = (now-datetime.timedelta(seconds=120), now)
    interval = 15
    throughputs = calculate_throughputs(taskname, timerange, interval)
    return HttpResponse(str(throughputs))

#==============================================================================#
@login_required()
def get_throughput_data(request, taskname=None):
    all_data = [] 
    description = {}
    description['timestamp'] = ("DateTime", "timestamp")
    description['tasks'] = ("number", "tasks")
    
    now = datetime.datetime.now()
    timerange = (now-datetime.timedelta(seconds=120), now)
    interval = 2
    throughputs = calculate_throughputs(taskname, timerange, interval)
    
    for i, p in enumerate(throughputs):
        data = {}
        tdiff = now-datetime.timedelta(seconds=120)
        data['timestamp'] = tdiff + datetime.timedelta(seconds=interval*i)
        data['tasks'] = p
        all_data.append(data)

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(all_data)

    if "tqx" in request.GET:
        tqx = request.GET['tqx']
        params = dict([p.split(':') for p in tqx.split(';')])
        reqId = params['reqId'] 
        return HttpResponse(
                    data_table.ToJSonResponse(
                        columns_order=("timestamp", "tasks"),
                        req_id=reqId)
                    )
    return HttpResponse(
                data_table.ToJSonResponse(
                    columns_order=("timestamp", "tasks"))
                )


@login_required()
def get_runtime_data(request, taskname=None):
    search_range =          searchrange_from_post(request.GET)
    runtime_range_min =     get_postval(request.GET, 'runtime_min', float, 0.)
    runtime_range_max =     get_postval(request.GET, 'runtime_max', float, None)
    runtime_range =         (runtime_range_min, runtime_range_max)
    bin_size =              get_postval(request.GET, 'bin_size', float, None)
    bin_count =             get_postval(request.GET, 'bin_count', int, None)
    auto_runtime_range =    get_postval(request.GET, 'auto_runtime_range', 
                                        string_to_bool, False)
    runtimes = calculate_runtimes(
                    taskname, 
                    search_range=search_range, 
                    runtime_range=runtime_range, 
                    bin_size=float(bin_size) if bin_size is not None else None, 
                    bin_count=int(bin_count) if bin_count is not None else None,
                    auto_runtime_range=auto_runtime_range
                    )
    all_data = []
    description = {
        'bin_name': ("string", "bin_name"),
        'count':    ("number", "count"),
        }
    for (runtime_min, runtime_max), count  in  runtimes:
        data = {
            'bin_name': '{0:g}-{1:g}'.format(runtime_min, runtime_max),
            'count':    count,
            }
        all_data.append(data)
    
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(all_data)
    
    if "tqx" in request.GET:
        tqx = request.GET['tqx']
        params = dict([p.split(':') for p in tqx.split(';')])
        reqId = params['reqId']
        return HttpResponse(
                    data_table.ToJSonResponse(
                        columns_order=("bin_name", "count"), 
                        req_id=reqId)
                    )
    return HttpResponse(
                data_table.ToJSonResponse(
                    columns_order=("bin_name", "count"))
                )
    

class RuntimeQueryStringBuilder(QueryStringBuilder):
    param_names = ['runtime_min', 'runtime_max', 'bin_count', 'bin_size',
                   'start_time', 'end_time', 'auto_runtime_range']


#==============================================================================#
def visualize_runtimes(request, taskname=None, runtime_min=0., bin_count=None, 
                       bin_size=None):
    
    qsbuilder = RuntimeQueryStringBuilder(runtime_min=runtime_min, 
                                          bin_count=bin_count, 
                                          bin_size=bin_size)
    if "submit" in request.POST:
        qsbuilder.add_querydict(request.POST)
    else:
        qsbuilder.add_querydict(request.GET)
    kwargs = {}
    if taskname:
        kwargs['taskname'] = taskname
    
    url = reverse("celerymanagementapp.views.get_runtime_data", kwargs=kwargs)
    url += qsbuilder.to_querystring()
    params = {'url':url, 'taskname':taskname}
    return render_to_response('celerymanagementapp/barchart.html', params,
            context_instance=RequestContext(request))

@login_required()
def visualize_throughput(request, taskname=None):
    return render_to_response('celerymanagementapp/timeseries.html',
            {'task': taskname, 'taskname': taskname },
            context_instance=RequestContext(request))

@login_required()
def view_defined_tasks(request):
    i = inspect()
    workers = i.registered_tasks()
    defined = []
    if workers:
        defined = set(x for x in 
                        itertools.chain.from_iterable(workers.itervalues())
                     )
        defined = list(defined)
        defined.sort()

    return render_to_response('celerymanagementapp/tasklist.html',
            {'tasks':defined},
            context_instance=RequestContext(request))


@login_required()
def get_dispatched_tasks(request, taskname=None):
    """View DispatchedTasks, possibly limited to those for a particular 
       DefinedTask.
    """
    alltasks = DispatchedTask.objects.all()  # was TaskState
    if taskname:
        alltasks = alltasks.filter(name=taskname)
    
    pg = Paginator(alltasks, 50)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
        
    try:
        tasks = pg.page(page)
    except (EmptyPage, InvalidPage):
        tasks = pg.page(pg.num_pages)
    
    return HttpResponse(tasks)


@login_required()
def view_dispatched_tasks(request, taskname=None):
    """View DispatchedTasks, possibly limited to those for a particular 
       DefinedTask.
    """
    alltasks = DispatchedTask.objects.all()
    if taskname:
        alltasks = alltasks.filter(name=taskname)
    
    pg = Paginator(alltasks, 50)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
        
    try:
        tasks = pg.page(page)
    except (EmptyPage, InvalidPage):
        tasks = pg.page(pg.num_pages)
     
    return render_to_response('celerymanagementapp/dispatched_tasklist.html',
            {'taskname':taskname, 'tasks': tasks},
            context_instance=RequestContext(request))

def get_runtimes_new(request, taskname=None, interval=0):
    if taskname is None:
        dataset = DispatchedTask.objects.all()  # was TaskState
    else:
        dataset = DispatchedTask.objects.filter(name=taskname)  # was TaskState
    stats = CeleryStats(dataset)
    if interval is 0:
        runtimes = stats.calculate_runtimes()
    else:
        TD = datetime.timedelta
        runtimes = stats.calculate_runtimes(TD(seconds=interval))

    all_data = [] 
    description = {}
    description['timestamp'] = ("DateTime", "timestamp")
    description['runtime'] = ("number", "runtime")
    
    for i in runtimes:
        data = {}
        data['timestamp'] = i[0]
        data['runtime'] = i[1]
        all_data.append(data)

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(all_data)

    if "tqx" in request.GET:
        tqx = request.GET['tqx']
        params = dict([p.split(':') for p in tqx.split(';')])
        reqId = params['reqId'] 
        return HttpResponse(
                    data_table.ToJSonResponse(
                        columns_order=("timestamp", "runtime"),
                        req_id=reqId)
                    )
    return HttpResponse(
                data_table.ToJSonResponse(
                    columns_order=("timestamp", "runtime"))
                )

@login_required()
def visualize_runtimes_new(request, taskname=None, interval=0):
    return render_to_response('celerymanagementapp/runtime_timeseries.html',
            {'task': taskname, 'taskname': taskname },
            context_instance=RequestContext(request))

@login_required()
def system_overview(request):
    return render_to_response('celerymanagementapp/system.html',
            context_instance=RequestContext(request))
            
@login_required()
def chart(request):
    return render_to_response('celerymanagementapp/chart.html',
            context_instance=RequestContext(request))

@login_required()
def configure(request):
    context = {}
    if settings.CELERYMANAGEMENTAPP_INFRASTRUCTURE_USE_MODE == "static":
        out_of_band_worker_node_form = OutOfBandWorkerNodeForm()
        OutOfBandWorkers = []

        outofbandworkernodes = OutOfBandWorkerNode.objects.all()
        for worker in outofbandworkernodes:
            worker.active = worker.is_celeryd_running()
            workerForm = OutOfBandWorkerNodeForm(instance=worker)
            OutOfBandWorkers.append({ "worker" : worker, 
                                      "workerForm" : workerForm })

        context["outofbandworkernode_form"] = out_of_band_worker_node_form
        context["outofbandworkernodes"] = OutOfBandWorkers

    elif settings.CELERYMANAGEMENTAPP_INFRASTRUCTURE_USE_MODE == "dynamic":
        provider = Provider.objects.all()
        providers = {}
        
        if provider:
            provider_form = ProviderForm(instance=provider)
            providers["provider_form"] = provider_form
            providers["provider"] = provider
        else:
            provider_form = ProviderForm()
            providers["provider_form"] = provider_form

        context["provider"] = providers

    return render_to_response('celerymanagementapp/configure.html',
            context,
            context_instance=RequestContext(request))

@login_required()
def task_view(request, taskname=None):
    return render_to_response('celerymanagementapp/task.html',
            { "taskname" : taskname, },
            context_instance=RequestContext(request))

@login_required()
def worker_view(request, workername=None):
    return render_to_response('celerymanagementapp/worker.html',
            { "workername" : workername, },
            context_instance=RequestContext(request))

@login_required()
def dashboard(request):
    return render_to_response('celerymanagementapp/dashboard.html',
            context_instance=RequestContext(request))
    
@login_required()
def policy(request):
    pols = PolicyModel.objects.all()
    policies = []
    for policyobj in pols:
        policyForm = PolicyModelForm(instance=policyobj)
        policies.append({ "policy" : policyobj, "policyForm" : policyForm })
    blank_policy_form = PolicyModelForm()
    return render_to_response('celerymanagementapp/policy.html',
            { 'policies': policies,
            'blank_policy_form': blank_policy_form },
            context_instance=RequestContext(request))

#==============================================================================#
def _resolve_name_param(name):
    """If name is None or 'all', return None.  Otherwise, returns name."""
    if not name or name.lower() == 'all':
        name = None
    return name

@login_required()
def kill_worker(request, name=None):
    """ Kills a running worker (celeryd).  However, no action will be taken 
        unless the request method is 'POST'.
        
        name:
            The name of the worker to stop.  The special value 'all' will stop 
            *all* workers.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    else:
        name = _resolve_name_param(name)
        dest = name and [name]  # dest will be None or a list of a single name
        print 'name: {0}'.format(name)
        print 'dest: {0}'.format(dest)
        broadcast('shutdown', destination=dest)
        return HttpResponse('success')

@login_required()
def grow_worker_pool(request, name=None, num=1):
    """ Kills a running worker (celeryd).  However, no action will be taken 
        unless the request method is 'POST'.
        
        name:
            The name of the worker to stop.  The special value 'all' will stop 
            *all* workers.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    else:
        name = _resolve_name_param(name)
        dest = name and [name]  # dest will be None or a list of a single name
        broadcast('pool_grow', destination=dest, arguments={'n':num})
        return HttpResponse('')

@login_required()
def shrink_worker_pool(request, name=None, num=1):
    """ Kills a running worker (celeryd).  However, no action will be taken 
        unless the request method is 'POST'.
        
        name:
            The name of the worker to stop.  The special value 'all' will stop 
            *all* workers.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    else:
        name = _resolve_name_param(name)
        dest = name and [name]  # dest will be None or a list of a single name
        broadcast('pool_shrink', destination=dest, arguments={'n':num})
        return HttpResponse('')
    





