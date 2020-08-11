# Kanban Board
Simple Kanban Board in Python. Please make sure to follow the instructions below to run the board on your browser and be marvelled at this beauty-->

![](/kanban_login.png)
![](/kanban_page.png)

## How to get it up and running
This was tested in a Windows environment. Please make sure that the commands are the same
in other OS. (Download the files first)

Run in order:
[type into your cmd] python -m venv .venv\ source 

[cd into] .venv/Scripts/

[type into your cmd] activate 

[add the files in the .venv folder] 

[cd out of Scripts folder and into .venv again]

[type into your cmd] pip install -r requirements.txt 

[type into your cmd] python kanban.py 

**** To run the tests!
[type into your cmd] python tests.py (You should see if tests failed or passed in the cmd)


Project Usage:
The Kanban Doge Board allows for each user to have their own board. After registering
and logging in, the user is able to add tasks under the 3 categories:
- Such to do;
- Very doing;
- Many done
With that, the user can also apply actions to multiple tasks at once (under one category
at a time) by checking the checkbox attached to each task. The actions are:
-Delete one or more task(s)
-Move one or more task(s) to the next stage of the board
After using it, remember to logout!

