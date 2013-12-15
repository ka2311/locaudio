
"""

triangulation

This file contains functions that can be used to determine the position
of a sound in a mesh network given a set of nodeEvents with associated
information. The nodeEvent (at this point) is a simple struct containing
its x and y position, the confidence of the sound that was just detected,
and the sound pressure level of the sound when it was detected. Using this
information we can create a probability function that can be maximized to
determine the position of the sample sound. The sample sound (for localization
given that the sound has been accurately detected by a set of nodeEvents)
only needs to contain the reference sound pressure level and a reference
distance from which this measurement has been taken.

"""


from collections import namedtuple
from detectionevent import DetectionEvent
from functools import partial
import math
import scipy.optimize as opt


## Scaling constant to transform a confidence probability into a
# a standard deviation.
K =  0.7


def distance_from_sound(r_ref, l_ref, l_current):
    """

    Determines the distance from a sound given the sound pressure level
    and a reference sound pressure level with an associated distance

    @param rRef The reference distance at which the reference sound
    pressure level was recorded

    @param lRef The reference sound pressure level used to determine the
    distance from the newly measured sound pressure level

    @param lCurrent Newly measured sound pressure level

    @return The predicted radius from a node event that the sound will be
    located at given the current sound pressure level

    """

    return r_ref * math.pow(10, (l_ref - l_current) / 20)


def distance_from_detection_event(x, y, node_event):
    """

    Given x and y coordinates, this returns the distance to a nodeEvent
    where the nodeEvent has attributes, x and y, on the same plane

    @param x the horizontal location of the node event when the node event
    was captured

    @param y the vertical location of the node event when the node event
    was captured

    @param nodeEvent The associated data when a node detects with some
    confidence that the sound has been identified

    @return The distance from a node event given x and y coordinates

    """

    return math.sqrt(
        math.pow(x - node_event.x, 2) +
        math.pow(y - node_event.y, 2)
    )


def normal_distribution(x):
    """

    This is the normal distribution function

    @param x Input for the normal distribution function

    @return The resulting value for the probability desnsity function

    """

    return (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * math.pow(x, 2))


def position_evaluation(x, y, r_ref, l_ref, node_events):
    """

    Evaluation function to deterimine with some weight, where a sound is
    located in the mesh network of nodes. Given an x and y, this returns
    a weight. The higher the weight, the higher the likelihood that the
    sound originated from x and y.

    @param x the horizontal location of the node event when the node event
    was captured

    @param y the vertical location of the node event when the node event
    was captured

    @param rRef The reference distance at which the reference sound
    pressure level was recorded

    @param lRef The reference sound pressure level used to determine the
    distance from the newly measured sound pressure level

    @param nodeEvents The list ofassociated data when a node detects with some
    confidence that the sound has been identified

    @return The a result, given independent variables, x and y, and a
    configuration of node events with per sample sound constants, rRef and
    lRef, will be a value representing the likelihood of the sample sound
    being located at position (x, y).

    """

    return sum(
        [
            normal_distribution(
                (
                    distance_from_detection_event(x, y, n) -
                    distance_from_sound(r_ref, l_ref, n.spl)
                ) / (K / n.confidence)
            ) / (K / n.confidence) for n in node_events
        ]
    )


def position_probability(x, y, r_ref, l_ref, node_events):
    """

    Scales the evaluation function so it returns a probability (i.e. a float
    between 0 and 1 inclusive) that a given x and y is where a sample sound
    originated from

    @param x the horizontal location of the node event when the node event
    was captured

    @param y the vertical location of the node event when the node event
    was captured

    @param rRef The reference distance at which the reference sound
    pressure level was recorded

    @param lRef The reference sound pressure level used to determine the
    distance from the newly measured sound pressure level

    @param nodeEvents The list ofassociated data when a node detects with some
    confidence that the sound has been identified

    @return The a result, given independent variables, x and y, and a
    configuration of node events with per sample sound constants, rRef and
    lRef, will be a value representing the probability of the sample
    sound being located at position (x, y).

    """

    return position_evaluation(
        x, y,
        r_ref, l_ref,
        node_events
    ) / float(len(node_events))


def determine_sound_position(r_ref, l_ref, init_guess, node_events):
    """

    Gets the x and y position of a sound in a mesh network given a set of
    node events. In order to establish the x and y positions we need a
    reference sound pressure level and the distance when this measurement
    was taken.

    @param rRef The reference distance at which the reference sound
    pressure level was recorded

    @param lRef The reference sound pressure level used to determine the
    distance from the newly measured sound pressure level

    @param initGuess The initial guess for gradient decent

    @param nodeEvents The list ofassociated data when a node detects with some
    confidence that the sound has been identified

    @return The x and y position of the sound.

    """

    p_func = lambda v: -1 * position_probability(
        v[0], v[-1],
        r_ref, l_ref,
        node_events
    )

    return opt.fmin(p_func, init_guess)


def generate_sound_position_func(r_ref, l_ref, init_guess):
    """

    This is a closure that provides a new function that makes it so the
    developer does not need to continue passing the rRef, lRef and initGuess
    variables when determining the sound position. This is most useful when
    tracking a sound throughout an enivronment because these parameters will
    stay constant.

    @param rRef The reference distance at which the reference sound
    pressure level was recorded

    @param lRef The reference sound pressure level used to determine the
    distance from the newly measured sound pressure level

    @param initGuess The initial guess for gradient decent

    @return A function that will use rRef, lRef, and initGuess to determine
    the position of the input sound. The independent variable will become
    just the node detection events.

    """

    return partial(
        determine_sound_position,
        r_ref, l_ref, init_guess
    )

