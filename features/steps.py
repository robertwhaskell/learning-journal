from lettuce import world
from lettuce import step


@step('an (/s+)')
def get_entry(step, entry):
    # get entry date, text, title, assign it to world
    pass


@step('I press the detail (/s+)')
def press_button(step, button):
    # press the detail button associated with the entry held in world
    pass


@step('I see (/s+)')
def see_detail(step, details):
    # check that the details being displayed on the page are the 
    # same as what the world is holding.
    pass
