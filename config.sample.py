#
# watcher user configuration
#
config = {
    # your too good to go credentials
    'email': 'too-good-to-go-email',
    'password': 'too-good-to-go-password',

    # your location preference (for distance)
    'latitude': 50.632905,
    'longitude': 5.568583,

    # default waiting time
    'normal-wait-from': 20,    # min 20 seconds
    'normal-wait-to': 50,      # max 50 seconds

    # speed-up time range
    'speedup-time-from': 1900, # 19;30
    'speedup-time-to': 2030,   # 20:30
    'speedup-wait-from': 10,   # min 10 seconds
    'speedup-wait-to': 20,     # max 20 seconds

    # pause the script during the night
    # pause at 21h for 9h long (21h00 > 6h00)
    'pause-from': 2100,        # 21:00
    'pause-for': 9 * 60,       # 9h (in minutes)

    # telegram bot
    'telegram-token': '',
    'telegram-chat-id': '',
}
