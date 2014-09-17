from datetime import datetime
from django.contrib.auth.models import User
from django.http import HttpResponse
from metrics.models import Event
import StringIO
import xlsxwriter


def _event_log(event_type=0, object=None):
    def decorator(view_func):
        def _wrapped_view(self, request, *args, **kwargs):
            etype = event_type
            if type(event_type) == int or type(event_type) == str:
                params = [event_type, self.request.user if isinstance(self.request.user, User) else None]
            elif type(event_type) == dict:
                etype = event_type.get(self.request.method)
                params = [etype, self.request.user if isinstance(self.request.user, User) else None]
            else:
                raise TypeError('"event_type" argument can be only int, str or dict')
            result = view_func(self, request, *args, **kwargs)
            obj = getattr(self, object) if object else None
            if etype:
                if obj:
                    params.append(obj)
                Event.log(*params)
            return result
        return _wrapped_view
    return decorator


def event_log(function=None, event_type=0, object=None):
    actual_decorator = _event_log(event_type, object)
    if function:
        return actual_decorator(function)
    return actual_decorator


def queryset_to_excel(queryset):
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Metrics Log')
    col = 0
    bold = workbook.add_format({'bold': True})
    worksheet.set_column(0, 1, 30)
    worksheet.write(0, 0, 'Date', bold)
    worksheet.write(0, 1, 'User ID', bold)
    worksheet.write(0, 2, 'User', bold)
    worksheet.write(0, 3, 'Action', bold)
    worksheet.write(0, 4, 'Object', bold)
    worksheet.write(0, 5, 'Object ID', bold)
    for row, event in enumerate(queryset, start=1):
        raw_data = [
            event.date.strftime('%Y-%m-%d %H:%M:%S'),
            event.user.id if event.user else '',
            event.user.__str__().encode('utf-8') if event.user else '',
            str(event.type),
            event.object.__str__().encode('utf-8') if event.object else '',
            event.object_id,
        ]
        worksheet.write_row(row, col, raw_data)
    workbook.close()
    output.seek(0)

    response = HttpResponse(output.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Metrics {0}.xlsx'.format(datetime.now())
    return response