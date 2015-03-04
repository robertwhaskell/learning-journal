Feature: Edit Features


    Scenario Outline: I should be able to delete entries entirely
        Go to an entry's edit page
        Press the delete button
        Then I see that the entry is gone from the homepage
        Then I see that the entry is gone from the database