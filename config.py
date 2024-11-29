# Centralized configuration for shared data
from matplotlib.colors import to_rgba


def calculate_tinted_colour(hex_colour, alpha=0.5):
    rgba = to_rgba(hex_colour, alpha)
    return 'rgba({},{},{},{})'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255), rgba[3])


services = ['Subways',
            'Buses',
            'LIRR',
            'Metro-North',
            'Access-A-Ride',
            'Bridges and Tunnels',
            'Staten Island Railway']

full_colours = ['#012A4A', '#01497C', '#2A6F97', '#2C7DA0',
                '#61A5C2', '#89C2D9', '#A9D6E5']  # Colours from a coolor.co palette
# Build the service colours dictionary for all charts
service_colours = {
    service: {
        "colour": colour,
        "tinted_colour": calculate_tinted_colour(colour, alpha=0.5)
    }
    for service, colour in zip(services, full_colours)
}

# Font Colours
dark_blue = '#134770'
dark_orange = '#D35940'
