# -*- coding: utf-8 -*-

"""
AI Simscape Model Generator - Generating MATLAB Simscape Models using Large Language Models.
Copyright (C) 2024  Patrick Hummel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

--------------------------------------------------------------------------------------------

This module contains functions used to format an amount of time into a human-readable format.

Last modification: 01.02.2024
"""

__version__ = "1"
__author__ = "Patrick Hummel"


def seconds_to_string(time_in_seconds: float) -> str:
    """
    This method turns a float value representing an amount of time in seconds into a human-readable format such as
    for example: "1h 30min 15s" or "15s 125ms" (milliseconds will only be displayed for less than 60 seconds).
    :param time_in_seconds: An amount of time in seconds (float)
    :return: A string in the format of "Xh Xmin Xs" or "Xs Xms"
    """

    # Initialize variables
    time_string = ""
    hours = 0
    minutes = 0
    seconds = 0
    milliseconds = 0

    # Only display milliseconds if it makes sense
    show_milliseconds = time_in_seconds < 60

    # Calculate hours
    if time_in_seconds >= 60*60:
        hours = int(time_in_seconds / (60 * 60))
        time_in_seconds -= hours * (60 * 60)

    # Calculate minutes
    if time_in_seconds >= 60:
        minutes = int(time_in_seconds / 60)
        time_in_seconds -= minutes * 60

    # Calculate seconds and milliseconds
    if time_in_seconds > 0:

        # Round seconds if milliseconds are not required
        if not show_milliseconds:

            seconds = round(time_in_seconds)

            # Rounding up may increase larger unit of time
            if seconds == 60:
                minutes += 1
                seconds = 0

                if minutes == 60:
                    hours += 1
                    minutes = 0

        else:
            seconds = int(time_in_seconds)
            time_in_seconds -= seconds
            milliseconds = round(time_in_seconds * 1e3)

    # Only add non-zero values to string
    if hours > 0:
        time_string += f"{hours:d}h "

    if minutes > 0 or hours > 0:
        time_string += f"{minutes:d}min "

    if seconds > 0 or minutes > 0:
        time_string += f"{seconds:d}s "

    if show_milliseconds:
        time_string += f"{milliseconds:d}ms"

    # Remove unnecessary leading or trailing spaces and return
    return time_string.strip()
