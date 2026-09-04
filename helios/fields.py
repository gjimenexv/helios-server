import datetime

from django.forms import fields

from .timezone_utils import election_to_utc
from .widgets import SplitSelectDateTimeWidget, DateTimeLocalWidget


class SplitDateTimeField(fields.MultiValueField):
    widget = SplitSelectDateTimeWidget

    def __init__(self, *args, **kwargs):
        """
        Have to pass a list of field types to the constructor, else we
        won't get any data to our compress method.
        """
        all_fields = (fields.DateField(), fields.TimeField())
        super(SplitDateTimeField, self).__init__(all_fields, *args, **kwargs)

    def compress(self, data_list):
        """
        Takes the values from the MultiWidget and passes them as a
        list to this function. This function needs to compress the
        list into a single object to save.
        """
        if data_list:
            if not (data_list[0] and data_list[1]):
                return None
            return datetime.datetime.combine(*data_list)
        return None


class DateTimeLocalField(fields.DateTimeField):
    """
    A field for HTML5 datetime-local input widget.
    Handles datetime input in the format: YYYY-MM-DDTHH:MM

    What the administrator types is on the election's clock
    (settings.ELECTION_TIME_ZONE); what Helios stores is naive UTC. This
    field is where that translation happens on the way in, and
    DateTimeLocalWidget does the reverse on the way back out to the form.
    """
    widget = DateTimeLocalWidget
    input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']

    def __init__(self, *args, **kwargs):
        if 'input_formats' not in kwargs or kwargs.get('input_formats') is None:
            kwargs['input_formats'] = self.input_formats
        super(DateTimeLocalField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        result = super(DateTimeLocalField, self).to_python(value)

        # Only text the user typed carries the election zone. Some views bind
        # these forms with datetimes straight off the model to render them
        # (one_election_edit, one_election_extend); those are already UTC and
        # must not be shifted a second time.
        if isinstance(value, str):
            return election_to_utc(result)

        return result

