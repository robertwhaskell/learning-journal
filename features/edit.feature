Feature: Journal edit page
    Edit an entry from learning journal, and then check that it's 
    actually edited.

    Scenario: Edit an entry
        Given an entry with the title "Uneditted Title"
        When I press the edit button
        Then I see the changes I made to the entry