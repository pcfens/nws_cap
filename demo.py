import nws_cap

# Get Alerts for the whole country
alerts = nws_cap.CAP_Feed.from_url()

# Iterate over alerts that are marked as Immediate urgency
for alert in alerts.filter_alerts('cap:urgency', 'Immediate'):
    # Display the event and the zones for which they're issued
    print alert.get_field('cap:event')
    print alert.get_geocode('UGC')
