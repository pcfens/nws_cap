"""
.. module:: nws_cap

.. moduleauthor:: Phil Fenstermacher <phillip.fenstermacher@gmail.com>

"""

import urllib2
import itertools
from lxml import objectify
from CAP_Alert import CAP_Alert

class CAP_Feed:
    """A class to fetch and filter sets of NWS Public Alerts

    Instances are rarely instatiated using the :func:`__init__` method.
    Suggested instantiation methods are :func:`from_url`, :func:`whole_state`, :func:`get_zones`,
    :func:`get_zone`, and :func:`get_county`.

    """

    def __init__(self, alert_list):
        """A class to manage sets of NWS Public Alerts.
        
        Args:
            alert_list (list): A list of CAP_Alert items that will be de-duped and 
                indexed based on the alert ID
        """
        self.alerts = dict()
        for alert in alert_list:
            self.alerts[alert.get_field('id')] = alert

    @classmethod
    def from_url(cls, url='http://alerts.weather.gov/cap/us.php?x=0'):
        """
        Fetch a list of public alerts from an ATOM feed of CAP data.

        Kwargs:
            url (str): The URL of the ATOM feed - defaults to entire US
        """
        request = urllib2.urlopen(url)
        raw_xml = request.read()
        xml_doc = objectify.fromstring(raw_xml)
        alerts = list()

        for entry in xml_doc.entry:
            if entry['title'] != 'There are no active watches, warnings or advisories':
                alerts.append(CAP_Alert(entry, xml_doc.nsmap))

        return cls(alerts)

    @classmethod
    def whole_state(cls, state, base_url = 'http://alerts.weather.gov/cap/', suffix = '.php?x=0'):
        """
        Fetch the NWS Public Alerts for an entire state.

        Args:
            state (str): The 2 character state code to pull alerts for.

        Kwargs:
            base_url (str): The pre-state code portion of the URL
            suffix (str): The post-state code portion of the URL
        """
        state_url = base_url + state.lower() + suffix
        return cls.from_url(url=state_url)

    @classmethod
    def get_zones(cls, zone_codes, base_url = 'http://alerts.weather.gov/cap/', suffix = '.php?x=0'):
        """
        Fetch the NWS Public Alerts for a list of zone codes.

        Args:
            zone_codes (list): A list of zone codes to pull alerts for.
        
        Kwargs:
            base_url (str): The pre-state code portion of the URL
            suffix (str): The post-state code portion of the URL

        .. note::
            You can get a list of zone codes by state from http://alerts.weather.gov/
        """
        requests = dict()
        alerts = list()
        for zone in zone_codes:
            requests.setdefault(zone[0:2].lower(), []).append(zone)
        for state in requests.keys():
            state_alerts = cls.whole_state(state, base_url=base_url, suffix=suffix)
            for zone in requests[state]:
               alerts += state_alerts.filter_by_location([zone], notation='UGC')
        return cls(alerts)

    @classmethod
    def get_county(cls, county_code, base_url = 'http://alerts.weather.gov/cap/wwaatmget.php?x=', suffix = '&y=0'):
        """
        Fetch the NWS Public alerts for a particular county/zone.

        Args:
            county_code (str): The county/zone code to pull alerts for.

        Kwargs:
            base_url (str): The pre-state code portion of the URL
            suffix (str): The post-state code portion of the URL

        .. note::
            You can get a list of county codes by state from http://alerts.weather.gov/

        .. note::
            This function is aliased to :func:`get_zone` because they perform the same operation,
            even though a county code is different than a zone code.
        """
        county_url = base_url + county_code.upper() + suffix
        return cls.from_url(url=county_url)
    
    get_zone = get_county

    def __add__(self, other):
        """
            Combine CAP_Feed instances.  After combining the alert list is de-duped
        """
        alerts = self.get_alerts() + other.get_alerts()
        return self.__class__(alerts)

    def __iadd__(self, other):
        """
            Combine CAP_Feed instances.  After combining the alert list is de-duped
        """
        for alert in other.get_alerts():
            self.alerts[alert.get_field('id')] = alert
        return self

    def categorize_alerts(self, field_name):
        """
        Categorize alerts based on a particular, non-geocoded field.

        Args:
            field_name (str): The field to categorize by.

        Returns:
            A dictionary object where the keys are the unique values of field_name.
            The values are lists of the CAP_Alerts that match.
        """
        if self.count_alerts():
            alerts = dict()
            for entry in self.alerts.values():
                alerts.setdefault(entry.get_field(field_name), []).append(entry)
            return alerts
        else:
            return None

    def filter_alerts(self, field_name, values, store=False):
        """
        Filter alerts based on a particular, non-geocoded field.

        Args:
            field_name (str): The field to filter on
            values (list): A list of values that indicate the alert should be kept

        Kwargs:
            store (bool): Whether or not to keep the filtered list as the new object
                (defauls to False)
        """
        if self.count_alerts():
            alerts = dict()
            for entry in self.alerts.values():
                if entry.get_field(field_name) in values:
                    alerts[entry.get_field('id')] = entry
            if store:
                self.alerts = alerts
        else:
            return None
        return alerts.values()

    def get_alerts(self):
        """
        Get a list of all of the CAP_Alerts in this feed object.

        Returns:
            A list of CAP_Alerts.
        """
        return self.alerts.values()

    def count_alerts(self):
        """
        Find out how many alerts there are in this feed

        Returns:
            A count of the alerts.
        """
        return len(self.alerts.values())

    def filter_by_location(self, locations, notation='UGC', store=False):
        """
        Retrieve alerts out of the set that are effective for certain locations.

        Args:
            locations (list): A list of location codes that you want to see alerts for

        Kwargs:
            notation (str): Which location notation to filter based on. UGC (default) or FIPS6
            store (bool): Whether or not to store the result as the new alert list or not 
                (defaults to False)

        .. note:: 
            UGC codes and zone codes are the same thing.
        """
        if self.count_alerts() == 0:
            return None
        alerts = dict()
        for alert in self.get_alerts():
            matches = len(set(alert.get_geocode(notation)).intersection(set(locations)))
            if matches == len(locations):
                alerts[alert.get_field('id')] = alert
        if store:
            self.alerts = alerts
        return alerts.values()

