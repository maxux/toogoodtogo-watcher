#
# watcher user configuration
#
config = {
    # your too good to go credentials
    'email': 'too-good-to-go-email',
    'password': 'too-good-to-go-password',

    # email notification settings
    'sender': 'toogoodtogo@provider.com',
    'destination': 'notification-target@email.com',
    'smtp': 'provider.smtp.net',

    # your location preference (for distance)
    'latitude': 50.632905,
    'longitude': 5.568583,

    # pause the script during the night
    # pause at 21h for 9h long (21h00 > 6h00)
    'pause-from': 21,
    'pause-for': 9,
}
